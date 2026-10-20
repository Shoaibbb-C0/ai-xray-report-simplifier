import test from 'node:test';
import assert from 'node:assert/strict';
import { build } from 'esbuild';

test('server auth awaits Next async cookies and verifies the user before exposing a client',async()=>{
 let patient = {id:'DEMO-OWNER'};
 const written = [];
 globalThis.__serverAuthTest = {
  cookies:async()=>({getAll:()=>[{name:'test-cookie',value:'DEMO'}],set:(...args)=>written.push(args)}),
  createServerClient:(url,key,options)=>{ assert.equal(options.cookies.getAll()[0].name,'test-cookie'); options.cookies.setAll([{name:'refreshed',value:'DEMO',options:{httpOnly:true}}]); return {auth:{getUser:async()=>({data:{user:patient},error:null})}}; },
  redirect:path=>{throw new Error(`REDIRECT:${path}`);},
  supabaseConfig:()=>({url:'https://test.invalid',key:'DEMO'}),
 };
 try {
  const result=await build({entryPoints:['lib/supabase/server.js'],bundle:true,write:false,platform:'node',format:'cjs',plugins:[{name:'auth-boundaries',setup(builder){
   builder.onResolve({filter:/^(server-only|@supabase\/ssr|next\/headers|next\/navigation|\.\/config)$/},args=>({path:args.path,namespace:'mocks'}));
   builder.onLoad({filter:/.*/,namespace:'mocks'},()=>({contents:'export const {cookies,createServerClient,redirect,supabaseConfig}=globalThis.__serverAuthTest;'}));
  }}]});
  const module={exports:{}};
  new Function('module','exports',result.outputFiles[0].text)(module,module.exports);
  assert.equal((await module.exports.requirePatient()).user.id,'DEMO-OWNER');
  assert.equal(written[0][0],'refreshed');
  patient=null;
  await assert.rejects(module.exports.requirePatient(),/REDIRECT:\/login/);
 } finally { delete globalThis.__serverAuthTest; }
});
