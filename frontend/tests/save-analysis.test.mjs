import test from 'node:test';
import assert from 'node:assert/strict';
import { saveAnalysis } from '../services/save-analysis.js';

function client(failResult = false, failCleanup = false) {
 const calls = [];
 return { calls, auth:{getUser:async()=>({data:{user:{id:'test-owner'}},error:null})},
  storage:{from:()=>({upload:async(path)=>{calls.push(['upload',path]);return {error:null};},remove:async(paths)=>{calls.push(['remove',paths]);return {error:failCleanup?{}:null};}})},
  from(table) { const query = { insert:async(record)=>{calls.push(['insert',table,record]);return {error:failResult&&table==='analysis_results'?{}:null};},update(record){calls.push(['update',table,record]);return query;},delete(){calls.push(['delete',table]);return query;},eq(...args){calls.push(['eq',...args]);return query;},then(resolve){return Promise.resolve({error:null}).then(resolve);} }; return query; },
 };
}
const result = {explanation:{analysis_status:'ERROR',body_part:{id:'hand'},attention:{available:true,overlay_base64:'TEST_ONLY',overlay_path:'/temporary'},model_versions:{}},model_versions:{}};

test('future-connected save derives ownership from verified auth and strips transient media without input mutation',async()=>{
 const db=client();
 const id=await saveAnalysis(db,{type:'image/png'},result);
 assert.match(id,/^[0-9a-f-]{36}$/);
 const scan=db.calls.find(call=>call[0]==='insert'&&call[1]==='xray_scans')[2];
 assert.equal(scan.user_id,'test-owner'); assert.equal(scan.body_side,null);
 const analysis=db.calls.find(call=>call[0]==='insert'&&call[1]==='analysis_results')[2];
 assert.equal(analysis.explanation.attention.overlay_base64,null);
 assert.equal(analysis.explanation.attention.available,false);
 assert.equal(result.explanation.attention.overlay_base64,'TEST_ONLY');
 assert.ok(db.calls.some(call=>call[0]==='eq'&&call[1]==='user_id'&&call[2]==='test-owner'));
});

test('failed saves remove private files before metadata, and preserve recoverable metadata if storage cleanup fails',async()=>{
 const db=client(true);
 await assert.rejects(saveAnalysis(db,{type:'image/jpeg'},result),/could not be saved/);
 assert.ok(db.calls.findIndex(call=>call[0]==='remove')<db.calls.findIndex(call=>call[0]==='delete'));
 const broken=client(true,true);
 await assert.rejects(saveAnalysis(broken,{type:'image/png'},result),/cleanup needs attention/);
 assert.ok(!broken.calls.some(call=>call[0]==='delete'));
 const anonymous=client(); anonymous.auth.getUser=async()=>({data:{user:null},error:null});
 await assert.rejects(saveAnalysis(anonymous,{type:'image/png'},result),/Sign in/);
 assert.equal(anonymous.calls.length,0);
});
