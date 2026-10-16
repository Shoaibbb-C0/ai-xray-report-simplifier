-- DEMO / TEST DATA ONLY. Run with database administrator access in a test
-- project after the migration. All test rows and role changes roll back.
begin;
insert into auth.users(id) values
 ('f6000000-0000-4000-8000-000000000001'),
 ('f6000000-0000-4000-8000-000000000002');
insert into public.profiles(id,display_name) values
 ('f6000000-0000-4000-8000-000000000001','DEMO / TEST DATA A'),
 ('f6000000-0000-4000-8000-000000000002','DEMO / TEST DATA B');
insert into public.xray_scans(id,user_id,body_part) values
 ('f6100000-0000-4000-8000-000000000001','f6000000-0000-4000-8000-000000000001','hand'),
 ('f6100000-0000-4000-8000-000000000002','f6000000-0000-4000-8000-000000000002','leg');
insert into public.analysis_results(scan_id,user_id,analysis_status,explanation)
select id,user_id,'ERROR','{"analysis_status":"ERROR","body_part":{"id":"unknown"},"finding":{},"summary":"DEMO / TEST DATA","limitations":[],"visual":{},"attention":{},"localization":{},"model_versions":{},"language":"en"}'::jsonb
from public.xray_scans where id in ('f6100000-0000-4000-8000-000000000001','f6100000-0000-4000-8000-000000000002');

-- Real Storage API upload/download testing remains separate: do not insert
-- storage.objects rows here because that would not create corresponding files.
set local role authenticated;
select set_config('request.jwt.claim.sub','f6000000-0000-4000-8000-000000000001',true);
do $$
declare affected integer;
begin
  assert (select count(*) from public.profiles where id::text like 'f6000000-%') = 1, 'Profile isolation failed';
  assert (select count(*) from public.xray_scans where id::text like 'f6100000-%') = 1, 'Scan isolation failed';
  assert (select count(*) from public.analysis_results where scan_id::text like 'f6100000-%') = 1, 'Result isolation failed';
  update public.xray_scans set status='failed' where user_id='f6000000-0000-4000-8000-000000000002';
  get diagnostics affected = row_count;
  assert affected=0, 'Cross-user update allowed';
  delete from public.profiles where id='f6000000-0000-4000-8000-000000000002';
  get diagnostics affected = row_count;
  assert affected=0, 'Cross-user delete allowed';
  begin
    insert into public.xray_scans(user_id) values ('f6000000-0000-4000-8000-000000000002');
    raise exception 'Cross-user insert allowed';
  exception when insufficient_privilege then null;
  end;
end $$;

select set_config('request.jwt.claim.sub','f6000000-0000-4000-8000-000000000002',true);
do $$ begin
  assert not exists(select 1 from public.profiles where id='f6000000-0000-4000-8000-000000000001'), 'Reverse profile isolation failed';
  assert not exists(select 1 from public.xray_scans where user_id='f6000000-0000-4000-8000-000000000001'), 'Reverse scan isolation failed';
  assert not exists(select 1 from public.analysis_results where user_id='f6000000-0000-4000-8000-000000000001'), 'Reverse result isolation failed';
end $$;
reset role;
do $$ begin
  assert exists(select 1 from storage.buckets where id='xray-scans' and public=false), 'Private bucket missing';
end $$;
rollback;
