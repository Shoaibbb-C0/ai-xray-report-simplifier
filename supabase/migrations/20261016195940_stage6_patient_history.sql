-- Stage 6: patient-owned metadata; no production seed data or analysis endpoint.
begin;

create table public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  display_name text check (char_length(display_name) <= 100),
  preferred_language text not null default 'en' check (preferred_language in ('en','hi','mr')),
  height_cm numeric check (height_cm > 0 and height_cm < 300),
  weight_kg numeric check (weight_kg > 0 and weight_kg < 700),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.xray_scans (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  scan_date date not null default current_date,
  body_part text not null default 'unknown' check (body_part in ('hand','leg','hip','shoulder','mixed','unknown')),
  body_side text check (body_side in ('left','right','unknown')),
  source_filename text check (char_length(source_filename) <= 255),
  storage_path text,
  mime_type text check (mime_type in ('image/png','image/jpeg')),
  status text not null default 'pending' check (status in ('pending','complete','failed')),
  unique (id, user_id),
  check (storage_path is null or (storage_path like user_id::text || '/' || id::text || '/%'
    and array_length(string_to_array(storage_path,'/'),1) = 3
    and split_part(storage_path,'/',3) <> ''
    and storage_path !~ '(^|/)\.\.(/|$)' and storage_path !~ '\\'))
);

create table public.analysis_results (
  id uuid primary key default gen_random_uuid(),
  scan_id uuid not null unique,
  user_id uuid not null references auth.users(id) on delete cascade,
  created_at timestamptz not null default now(),
  xray_validation_result text check (xray_validation_result in ('x_ray','non_xray','uncertain')),
  xray_validation_confidence double precision check (xray_validation_confidence between 0 and 1),
  body_part_result text check (body_part_result in ('hand','leg','hip','shoulder','mixed','unknown')),
  body_part_confidence double precision check (body_part_confidence between 0 and 1),
  fracture_result text check (fracture_result in ('fracture','no_fracture','uncertain','not_analyzed')),
  fracture_confidence double precision check (fracture_confidence between 0 and 1),
  analysis_status text not null check (analysis_status in (
    'VALID_XRAY_FRACTURE_SUSPECTED','VALID_XRAY_NO_FRACTURE_SIGNAL','VALID_XRAY_UNCERTAIN',
    'BODY_PART_UNKNOWN','NON_XRAY','XRAY_VALIDATION_UNCERTAIN','MODEL_UNAVAILABLE','ERROR')),
  model_versions jsonb not null default '{}'::jsonb check (jsonb_typeof(model_versions) = 'object'),
  explanation jsonb not null check (jsonb_typeof(explanation) = 'object'),
  foreign key (scan_id, user_id) references public.xray_scans(id, user_id) on delete cascade,
  check (explanation ?& array['analysis_status','body_part','finding','summary','limitations','visual','attention','localization','model_versions','language']),
  check (explanation->>'analysis_status' = analysis_status),
  check (not jsonb_path_exists(explanation, '$.**.overlay_base64 ? (@ != null)')),
  check (not jsonb_path_exists(explanation, '$.** ? (@.type() == "string" && @ like_regex "^data:image/")'))
);

create index xray_scans_user_date_idx on public.xray_scans(user_id, scan_date desc, id desc);
create index xray_scans_user_region_idx on public.xray_scans(user_id, body_part, scan_date desc);
create index analysis_results_user_idx on public.analysis_results(user_id);

create function public.stage6_updated_at() returns trigger language plpgsql
set search_path = '' as $$ begin new.updated_at = now(); return new; end $$;
revoke all on function public.stage6_updated_at() from public;
create trigger profiles_updated_at before update on public.profiles for each row execute function public.stage6_updated_at();
create trigger scans_updated_at before update on public.xray_scans for each row execute function public.stage6_updated_at();

alter table public.profiles enable row level security;
alter table public.xray_scans enable row level security;
alter table public.analysis_results enable row level security;

revoke all on public.profiles, public.xray_scans, public.analysis_results from anon;
grant select, insert, update, delete on public.profiles, public.xray_scans, public.analysis_results to authenticated;

create policy profiles_select on public.profiles for select to authenticated using ((select auth.uid()) = id);
create policy profiles_insert on public.profiles for insert to authenticated with check ((select auth.uid()) = id);
create policy profiles_update on public.profiles for update to authenticated using ((select auth.uid()) = id) with check ((select auth.uid()) = id);
create policy profiles_delete on public.profiles for delete to authenticated using ((select auth.uid()) = id);

create policy scans_select on public.xray_scans for select to authenticated using ((select auth.uid()) = user_id);
create policy scans_insert on public.xray_scans for insert to authenticated with check ((select auth.uid()) = user_id);
create policy scans_update on public.xray_scans for update to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
create policy scans_delete on public.xray_scans for delete to authenticated using ((select auth.uid()) = user_id);

create policy results_select on public.analysis_results for select to authenticated using ((select auth.uid()) = user_id);
create policy results_insert on public.analysis_results for insert to authenticated with check ((select auth.uid()) = user_id);
create policy results_update on public.analysis_results for update to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
create policy results_delete on public.analysis_results for delete to authenticated using ((select auth.uid()) = user_id);

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('xray-scans','xray-scans',false,10485760,array['image/png','image/jpeg']);

-- Require both the owner prefix and an existing owned scan. No public URLs.
create policy xray_objects_select on storage.objects for select to authenticated using (
  bucket_id = 'xray-scans' and (storage.foldername(name))[1] = (select auth.uid())::text
  and exists (select 1 from public.xray_scans s where s.user_id = (select auth.uid()) and s.id::text = (storage.foldername(name))[2]));
create policy xray_objects_insert on storage.objects for insert to authenticated with check (
  bucket_id = 'xray-scans' and (storage.foldername(name))[1] = (select auth.uid())::text
  and array_length(storage.foldername(name),1) = 2 and name !~ '(^|/)\.\.(/|$)' and name !~ '\\'
  and exists (select 1 from public.xray_scans s where s.user_id = (select auth.uid()) and s.id::text = (storage.foldername(name))[2]));
create policy xray_objects_update on storage.objects for update to authenticated using (
  bucket_id = 'xray-scans' and (storage.foldername(name))[1] = (select auth.uid())::text
  and exists (select 1 from public.xray_scans s where s.user_id = (select auth.uid()) and s.id::text = (storage.foldername(name))[2]))
with check (
  bucket_id = 'xray-scans' and (storage.foldername(name))[1] = (select auth.uid())::text
  and array_length(storage.foldername(name),1) = 2 and name !~ '(^|/)\.\.(/|$)' and name !~ '\\'
  and exists (select 1 from public.xray_scans s where s.user_id = (select auth.uid()) and s.id::text = (storage.foldername(name))[2]));
-- Prefix ownership lets users clean up objects even after scan metadata is deleted.
create policy xray_objects_delete on storage.objects for delete to authenticated using (
  bucket_id = 'xray-scans' and (storage.foldername(name))[1] = (select auth.uid())::text);

commit;
