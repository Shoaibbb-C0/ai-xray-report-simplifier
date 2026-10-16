// Local embedded PostgreSQL. Auth/storage schemas model Supabase interfaces only;
// this is real SQL/RLS execution, not a substitute for live Supabase API testing.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile, readdir } from 'node:fs/promises';
import { PGlite } from '@electric-sql/pglite';

test('migration enforces two-user isolation, constraints, cascades and private storage in PostgreSQL', async () => {
  const db = new PGlite();
  try {
    await db.exec(`
      create role anon; create role authenticated;
      create schema auth; create schema storage;
      create table auth.users(id uuid primary key);
      create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub',true),'')::uuid $$;
      create table storage.buckets(id text primary key, name text, public boolean, file_size_limit bigint, allowed_mime_types text[]);
      create table storage.objects(id uuid primary key default gen_random_uuid(), bucket_id text, name text);
      alter table storage.objects enable row level security;
      create function storage.foldername(name text) returns text[] language sql immutable as $$ select (string_to_array(name,'/'))[1:array_length(string_to_array(name,'/'),1)-1] $$;
      grant usage on schema auth,storage to authenticated,anon;
      grant select,insert,update,delete on storage.objects to authenticated;
    `);
    const migrations = await readdir('../supabase/migrations');
    for (const file of migrations.filter(file => file.endsWith('.sql')).sort()) await db.exec(await readFile(`../supabase/migrations/${file}`, 'utf8'));
    const a = '10000000-0000-4000-8000-000000000001';
    const b = '10000000-0000-4000-8000-000000000002';
    const sa = '20000000-0000-4000-8000-000000000001';
    const sb = '20000000-0000-4000-8000-000000000002';
    const unattached = '20000000-0000-4000-8000-000000000003';
    const explanation = JSON.stringify({ analysis_status: 'ERROR', body_part: { id: 'unknown' }, finding: {}, summary: 'DEMO / TEST DATA', limitations: [], visual: {}, attention: { overlay_base64: null }, localization: {}, model_versions: {}, language: 'en' });
    await db.exec(`insert into auth.users values ('${a}'),('${b}');`);
    const asUser = async id => db.exec(`reset role; set role authenticated; select set_config('request.jwt.claim.sub','${id}',false);`);
    for (const [user, scan] of [[a,sa],[b,sb]]) {
      await asUser(user);
      await db.query('insert into public.profiles(id,display_name) values ($1,$2)', [user, 'DEMO / TEST DATA']);
      await db.query('insert into public.xray_scans(id,user_id,body_part) values ($1,$2,$3)', [scan,user,'hand']);
      await db.query("insert into public.analysis_results(scan_id,user_id,analysis_status,explanation) values ($1,$2,'ERROR',$3::jsonb)", [scan,user,explanation]);
      await db.query("insert into storage.objects(bucket_id,name) values ('xray-scans',$1)", [`${user}/${scan}/TEST.png`]);
    }
    for (const [owner,other,otherScan] of [[a,b,sb],[b,a,sa]]) {
      await asUser(owner);
      for (const [table, ownerKey] of [['profiles','id'],['xray_scans','user_id'],['analysis_results','user_id']]) {
        assert.equal((await db.query(`select * from public.${table}`)).rows.length, 1);
        assert.equal((await db.query(`select * from public.${table} where ${ownerKey}=$1`, [other])).rows.length, 0);
        assert.equal((await db.query(`update public.${table} set ${ownerKey}=${ownerKey} where ${ownerKey}=$1 returning *`, [other])).rows.length, 0);
        assert.equal((await db.query(`delete from public.${table} where ${ownerKey}=$1 returning *`, [other])).rows.length, 0);
      }
      await assert.rejects(db.query('insert into public.xray_scans(user_id) values ($1)', [other]), /row-level security/);
      await assert.rejects(db.query('update public.xray_scans set user_id=$1 where user_id=$2', [other,owner]));
      await assert.rejects(db.query("insert into public.analysis_results(scan_id,user_id,analysis_status,explanation) values ($1,$2,'ERROR',$3::jsonb)", [otherScan,owner,explanation]));
      assert.equal((await db.query('select * from storage.objects')).rows.length, 1);
      assert.equal((await db.query('select * from storage.objects where name like $1', [`${other}/%`])).rows.length, 0);
      assert.equal((await db.query('delete from storage.objects where name like $1 returning *', [`${other}/%`])).rows.length, 0);
      assert.equal((await db.query('update storage.objects set name=name where name like $1 returning *', [`${other}/%`])).rows.length, 0);
      await assert.rejects(db.query("insert into storage.objects(bucket_id,name) values ('xray-scans',$1)", [`${other}/${otherScan}/TEST2.png`]), /row-level security/);
      await assert.rejects(db.query("insert into storage.objects(bucket_id,name) values ('xray-scans',$1)", [`${owner}/${otherScan}/TEST2.png`]), /row-level security/);
    }
    await asUser(a);
    await db.exec('reset role');
    await db.query('insert into public.xray_scans(id,user_id) values ($1,$2)', [unattached,b]);
    await asUser(a);
    await assert.rejects(db.query("insert into public.analysis_results(scan_id,user_id,analysis_status,explanation) values ($1,$2,'ERROR',$3::jsonb)", [unattached,a,explanation]), /foreign key constraint/);
    for (const [column,value] of [['body_part','chest'],['body_side','inferred_left'],['storage_path',`${b}/${sb}/TEST.png`]]) {
      await assert.rejects(db.query(`update public.xray_scans set ${column}=$1 where id=$2`, [value,sa]), /check constraint/);
    }
    await assert.rejects(db.query("update public.analysis_results set fracture_confidence=2"), /check constraint/);
    await assert.rejects(db.query("update public.analysis_results set explanation=jsonb_set(explanation,'{attention,overlay_base64}','\"data:image/png;base64,TEST\"')"), /check constraint/);
    await db.query('delete from public.xray_scans where id=$1', [sa]);
    assert.equal((await db.query('select * from public.analysis_results')).rows.length, 0);
    await db.query('delete from storage.objects where name like $1', [`${a}/%`]);
    assert.equal((await db.query('select * from storage.objects')).rows.length, 0);
    await db.exec("reset role; set role anon; select set_config('request.jwt.claim.sub','',false);");
    for (const table of ['profiles','xray_scans','analysis_results']) await assert.rejects(db.query(`select * from public.${table}`), /permission denied/);
    await db.exec('reset role');
    assert.equal((await db.query("select public from storage.buckets where id='xray-scans'")).rows[0].public, false);
    const rls = await db.query("select relname,relrowsecurity from pg_class where relname in ('profiles','xray_scans','analysis_results')");
    assert.ok(rls.rows.every(row => row.relrowsecurity));
    await db.query('delete from auth.users where id=$1', [b]);
    assert.equal((await db.query('select * from public.xray_scans')).rows.length, 0);
    assert.equal((await db.query('select * from public.profiles')).rows.length, 1);
    await db.exec(await readFile('../supabase/tests/stage6_isolation.sql', 'utf8'));
  } finally { await db.close(); }
});
