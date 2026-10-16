import test from 'node:test';
import assert from 'node:assert/strict';
import { build } from 'esbuild';

test('middleware redirects anonymous/forged sessions and preserves refreshed cookies', async () => {
  let user = null;
  let refresh = false;
  let configEnabled = true;
  const fakeCookies = () => ({ values: [], getAll() { return this.values; }, set(...args) { this.values.push(args.length === 1 ? args[0] : { name: args[0], value: args[1] }); } });
  globalThis.__stage6Mocks = {
    createServerClient: (url,key,options) => ({ auth: { getUser: async () => {
      if (refresh) options.cookies.setAll([{ name: 'test-session', value: 'refreshed', options: {} }]);
      return { data: { user } };
    } } }),
    supabaseConfig: () => configEnabled ? { url: 'https://test.invalid', key: 'DEMO' } : null,
    NextResponse: {
      next: () => ({ headers: new Headers(), cookies: fakeCookies(), status: 200 }),
      redirect: url => ({ headers: new Headers(), cookies: fakeCookies(), status: 307, url: url.toString() }),
    },
  };
  const output = await build({ entryPoints: ['middleware.js'], bundle: true, write: false, platform: 'node', format: 'cjs', plugins: [{ name: 'mock-boundaries', setup(build) {
    build.onResolve({ filter: /^(@supabase\/ssr|next\/server|\.\/lib\/supabase\/config)$/ }, args => ({ path: args.path, namespace: 'test-mocks' }));
    build.onLoad({ filter: /.*/, namespace: 'test-mocks' }, () => ({ contents: 'export const {createServerClient,NextResponse,supabaseConfig}=globalThis.__stage6Mocks;' }));
  } }] });
  const module = { exports: {} };
  new Function('module','exports',output.outputFiles[0].text)(module,module.exports);
  const request = path => ({ url: `http://localhost:3000${path}`, nextUrl: new URL(`http://localhost:3000${path}`), cookies: fakeCookies() });
  const middleware = module.exports.middleware;
  for (const path of ['/map','/history','/history/other-users-id','/profile']) {
    const response = await middleware(request(path));
    assert.equal(response.status,307);
    assert.equal(new URL(response.url).pathname,'/login');
    assert.equal(response.headers.get('Cache-Control'),'private, no-store');
  }
  refresh = true;
  assert.equal((await middleware(request('/history'))).cookies.values[0].value,'refreshed');
  user = { id: 'user-a' };
  assert.equal((await middleware(request('/history'))).status,200);
  configEnabled = false;
  const setup = await middleware(request('/map'));
  assert.equal(new URL(setup.url).searchParams.get('setup'),'required');
  delete globalThis.__stage6Mocks;
});
