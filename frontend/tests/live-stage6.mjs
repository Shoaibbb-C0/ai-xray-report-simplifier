// Explicit live acceptance harness. Never included in npm test or seeded at startup.
// Credentials must identify disposable, confirmed DEMO accounts provisioned for this run.
// Usage: node tests/live-stage6.mjs <temporary-credentials-json> [local-app-origin]
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createClient } from '@supabase/supabase-js';
import { createServerClient } from '@supabase/ssr';
import { randomUUID } from 'node:crypto';

const accounts = JSON.parse(await readFile(process.argv[2], 'utf8'));
assert.equal(accounts.length, 2);
assert.ok(accounts.every(account => /^stage6-test-[a-f0-9]+@example\.invalid$/.test(account.email)), 'Only isolated test accounts may be used');
const env = Object.fromEntries((await readFile('.env.local', 'utf8')).trim().split(/\r?\n/).map(line => {
  const i = line.indexOf('='); return [line.slice(0, i), line.slice(i + 1)];
}));
const url = env.NEXT_PUBLIC_SUPABASE_URL;
const key = env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY || env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
const clients = accounts.map(() => createClient(url,key,{auth:{persistSession:false,autoRefreshToken:false}}));
const anonymous = createClient(url,key,{auth:{persistSession:false,autoRefreshToken:false}});
const scans = accounts.map(() => randomUUID());
const paths = accounts.map((account,i) => `${account.id}/${scans[i]}/DEMO-TEST.png`);
const explanation = {
  analysis_status:'ERROR', body_part:{id:'hand',label:'Hand',is_supported:true,confidence:null},
  finding:{id:'fracture',label:'Fracture',state:'not_analyzed',probability:null,confidence:null},
  summary:'DEMO / TEST DATA — no medical prediction was made.',what_this_test_checks:'Software acceptance test only.',
  what_the_result_means:'No medical interpretation.',next_step_message:'Discard test record.',
  limitations:['DEMO / TEST DATA'],visual:{illustration_id:'hand_neutral',illustration_url:'/assets/anatomy/hand/hand_neutral.svg',illustration_path:'assets/anatomy/hand/hand_neutral.svg',educational_only:true,exact_location:false,title:'Educational anatomy',alt_text:'Standard hand reference',label_notice:'DEMO / TEST DATA'},
  attention:{available:false,overlay_base64:null,is_exact_localization:false,clinical_localization:false,disclaimer:'Model attention is not an injury location.'},
  localization:{available:false,exact_location:false,reason:'No localization in this software test.'},model_versions:{},language:'en',
};
const png = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+j9XcAAAAASUVORK5CYII=','base64');
function ok(result,label) { assert.equal(result.error,null,label); return result.data; }
function denied(result,label) { assert.ok(result.error || result.data?.length === 0,label); }
let assertions = 0;
const disposable = [false,false];
try {
  for (let i=0;i<2;i++) {
    const client=clients[i], account=accounts[i];
    const login=ok(await client.auth.signInWithPassword({email:account.email,password:account.password}),'Confirmed test login');
    assert.equal(login.user.user_metadata.stage6_test,true,'Disposable account marker required');
    disposable[i]=true;
    ok(await client.from('profiles').insert({id:account.id,display_name:'DEMO / TEST DATA'}),'Own profile insert');
    ok(await client.from('xray_scans').insert({id:scans[i],user_id:account.id,body_part:'hand',status:'complete'}),'Own scan insert');
    ok(await client.from('analysis_results').insert({scan_id:scans[i],user_id:account.id,analysis_status:'ERROR',explanation}),'Own result insert');
    ok(await client.storage.from('xray-scans').upload(paths[i],png,{contentType:'image/png'}),'Own private upload');
    ok(await client.storage.from('xray-scans').download(paths[i]),'Own private download');
    assertions+=6;
  }
  for (let i=0;i<2;i++) {
    const client=clients[i], other=accounts[1-i];
    for (const [table,column] of [['profiles','id'],['xray_scans','user_id'],['analysis_results','user_id']]) {
      assert.equal(ok(await client.from(table).select('*').eq(column,other.id),'Foreign read').length,0);
      assert.equal(ok(await client.from(table).update(table==='profiles'?{display_name:'DEMO FORBIDDEN'}:table==='xray_scans'?{status:'failed'}:{fracture_confidence:.1}).eq(column,other.id).select(),'Foreign update').length,0);
      assert.equal(ok(await client.from(table).delete().eq(column,other.id).select(),'Foreign delete').length,0);
      assertions+=3;
    }
    assert.ok((await client.from('xray_scans').insert({user_id:other.id})).error,'Foreign insert denied');
    assert.ok((await client.from('xray_scans').update({user_id:other.id}).eq('id',scans[i])).error,'Owner reassignment denied');
    assert.ok((await client.from('analysis_results').update({scan_id:scans[1-i]}).eq('user_id',accounts[i].id)).error,'Foreign result association denied');
    const bucket=client.storage.from('xray-scans');
    assert.ok((await bucket.download(paths[1-i])).error,'Foreign download denied');
    assert.ok((await bucket.createSignedUrl(paths[1-i],60)).error,'Foreign signed URL denied');
    denied(await bucket.list(`${other.id}/${scans[1-i]}`),'Foreign list denied');
    assert.ok((await bucket.upload(paths[1-i],png,{contentType:'image/png',upsert:true})).error,'Foreign replacement denied');
    denied(await bucket.remove([paths[1-i]]),'Foreign object deletion denied');
    ok(await clients[1-i].storage.from('xray-scans').download(paths[1-i]),'Foreign attempt leaves owner object intact');
    assertions+=9;
  }
  for (const table of ['profiles','xray_scans','analysis_results']) { denied(await anonymous.from(table).select('*'),'Anonymous patient read denied'); assertions++; }
  assert.ok((await anonymous.storage.from('xray-scans').download(paths[0])).error,'Anonymous private download denied'); assertions++;
  if (process.argv[3]) {
    const cookies=[];
    const server=createServerClient(url,key,{cookies:{getAll:()=>cookies,setAll:values=>values.forEach(value=>{const old=cookies.findIndex(c=>c.name===value.name); if(old>=0)cookies.splice(old,1);cookies.push(value);})}});
    ok(await server.auth.signInWithPassword({email:accounts[0].email,password:accounts[0].password}),'SSR cookie login');
    const headers={Cookie:cookies.map(c=>`${c.name}=${c.value}`).join('; ')};
    for (const path of ['/map','/history',`/history/${scans[0]}`]) {
      const response=await fetch(process.argv[3]+path,{headers,redirect:'manual'});
      assert.equal(response.status,200,`Authenticated ${path}`);
      const html=await response.text();
      assert.ok(html.includes(path.startsWith('/history/')?'DEMO / TEST DATA':path==='/map'?'My X-Ray Map':'Scan history'));
      assertions++;
    }
    const foreign=await fetch(`${process.argv[3]}/history/${scans[1]}`,{headers,redirect:'manual'});
    assert.equal(foreign.status,404,'Foreign detail hidden'); assertions++;
    ok(await server.auth.signOut(),'SSR logout');
    const after=await fetch(process.argv[3]+'/map',{headers:{Cookie:cookies.filter(c=>c.value).map(c=>`${c.name}=${c.value}`).join('; ')},redirect:'manual'});
    assert.equal(after.status,307,'Logged-out map redirects'); assertions++;
  }
  console.log(`PASS: ${assertions} live Auth/PostgREST/Storage/SSR acceptance checks.`);
} finally {
  for (let i=0;i<2;i++) {
    if (!disposable[i]) continue;
    // No patient data: remove test objects first, then rows; admin cleanup removes users.
    const client=clients[i];
    await client.auth.signInWithPassword({email:accounts[i].email,password:accounts[i].password});
    const removed=await client.storage.from('xray-scans').remove([paths[i]]);
    if(removed.error) console.error('Test object cleanup needs attention.');
    await client.from('xray_scans').delete().eq('id',scans[i]);
    await client.from('profiles').delete().eq('id',accounts[i].id);
    await client.auth.signOut();
  }
}
