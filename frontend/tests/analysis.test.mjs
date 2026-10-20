import test from 'node:test';
import assert from 'node:assert/strict';
import { validateFile, analyzeImage, MAX_UPLOAD_BYTES } from '../lib/analysis.js';

test('upload validation accepts JPEG/PNG and rejects empty/oversized/unsupported files', () => {
  assert.ok(validateFile(null));
  for (const type of ['image/jpeg','image/png']) assert.equal(validateFile({type,size:120}),null);
  for (const file of [{type:'image/svg+xml',size:12},{type:'image/png',size:0},{type:'image/png',size:MAX_UPLOAD_BYTES+1}]) assert.ok(validateFile(file));
});

test('analysis client posts multipart language/attention and preserves safe errors', async () => {
  const original = globalThis.fetch;
  try {
    globalThis.fetch = async (url, options) => {
      assert.ok(url.endsWith('/api/v1/analyze'));
      assert.equal(options.body.get('language'),'mr');
      assert.equal(options.body.get('attention'),'true');
      return {ok:true,json:async()=>({status:'TEST_ONLY',persistence:{saved:false}})};
    };
    assert.equal((await analyzeImage(new Blob(['TEST'],{type:'image/png'}),{language:'mr',attention:true})).persistence.saved,false);
    globalThis.fetch = async () => ({ok:false,json:async()=>({detail:{code:'model_unavailable',message:'Models unavailable'}})});
    await assert.rejects(analyzeImage(new Blob(['TEST'])),error=>error.code==='model_unavailable');
    globalThis.fetch = async () => { throw new TypeError('network'); };
    await assert.rejects(analyzeImage(new Blob(['TEST'])),/Start the backend/);
  } finally { globalThis.fetch=original; }
});
