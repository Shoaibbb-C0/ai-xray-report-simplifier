// One terminal, two local processes. No global npm command is required.
import { spawn, spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { createServer } from 'node:net';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
if (process.argv.includes('--help')) {
  console.log('node scripts/dev.mjs [--production] [--api-port=8001] [--web-port=3000]');
  process.exit(0);
}
const port = (name, fallback) => {
  const value = Number(process.argv.find(arg => arg.startsWith(`--${name}=`))?.split('=')[1] || fallback);
  if (!Number.isInteger(value) || value < 1024 || value > 65535) throw new Error(`Invalid ${name}`);
  return value;
};
const apiPort = port('api-port', 8001), webPort = port('web-port', 3000);
if (apiPort === webPort) throw new Error('The web and API ports must differ.');
if (process.argv.includes('--production') && apiPort !== 8001) throw new Error('Production uses the API URL baked into the build. Use development mode for automatic API port overrides.');
for (const candidate of [apiPort, webPort]) await new Promise((resolve, reject) => {
  const server = createServer();
  server.on('error', () => reject(new Error(`Port ${candidate} is busy. Stop its server or choose another port.`)));
  server.listen(candidate, '127.0.0.1', () => server.close(resolve));
});
const python = path.join(root, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
const next = path.join(root, 'frontend/node_modules/next/dist/bin/next');
if (!existsSync(python) || !existsSync(next)) throw new Error('Install the Python and frontend dependencies first. See docs/local-development.md.');
const children = [];
let stopping = false;
function stop(code = 0) {
  if (stopping) return;
  stopping = true;
  for (const child of children) {
    if (child.exitCode !== null || !child.pid) continue;
    if (process.platform === 'win32') spawnSync('taskkill.exe', ['/PID', String(child.pid), '/T', '/F'], { windowsHide: true, stdio: 'ignore' });
    else child.kill();
  }
  process.exitCode = code;
}
function start(command, args, cwd, env) {
  const child = spawn(command, args, { cwd, env: { ...process.env, ...env }, stdio: 'inherit', windowsHide: true });
  children.push(child);
  child.on('error', error => { console.error(error.message); stop(1); });
  child.on('exit', code => { if (!stopping) stop(code || 0); });
}
start(python, ['-m', 'uvicorn', 'backend.app.main:app', '--host', '127.0.0.1', '--port', String(apiPort)], root,
  { CORS_ORIGINS: `http://127.0.0.1:${webPort},http://localhost:${webPort}` });
start(process.execPath, [next, process.argv.includes('--production') ? 'start' : 'dev', '--hostname', '127.0.0.1', '--port', String(webPort)], path.join(root, 'frontend'),
  { NEXT_PUBLIC_API_URL: `http://127.0.0.1:${apiPort}` });
process.on('SIGINT', () => stop());
process.on('SIGTERM', () => stop());
console.log(`\nAI X-Ray: http://127.0.0.1:${webPort}\nAPI: http://127.0.0.1:${apiPort}\nCtrl+C stops both servers.\n`);
