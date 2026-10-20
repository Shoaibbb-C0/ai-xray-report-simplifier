# Local development

Use Python 3.12+ and Node 22+. This PC was verified with Python 3.12.14,
Node 24.19.0 and npm 10.9.2. It has a two-core i3 CPU, about 7.8 GiB visible
RAM, Intel UHD graphics and no PyTorch CUDA device. CPU is the supported default.

## Install

From the repository root, create .venv if it does not already exist:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
cd frontend
npm ci
cd ..
```

This PC's .venv already exists and uses Codex's bundled Python installation.
System Python/npm were not on PATH. npm was installed outside the repository;
if the normal npm command is unavailable on this PC, use:

```powershell
$xrayNpmCli = Join-Path $env:LOCALAPPDATA 'xray-dev-tools/package/bin/npm-cli.js'
# From frontend/:
node $xrayNpmCli ci
node $xrayNpmCli test
node $xrayNpmCli run build
```

requirements.txt describes direct dependencies; requirements-lock.txt records
the versions verified in the final environment. No environment directory or
Node package directory belongs in Git.

## Configure local analysis

Copy frontend/.env.example to ignored frontend/.env.local and set only:

```dotenv
NEXT_PUBLIC_API_URL=http://127.0.0.1:8001
```

Leave Supabase URL/key blank for the disconnected local workflow. No backend
Supabase key is required. Never use a service-role key in frontend variables.
Backend settings read process environment variables; the example .env file is
a reference, not an automatically loaded secret file. Safe defaults bind loopback.

## Start

The simplest command starts both services without needing npm on PATH:

```powershell
node scripts/dev.mjs
```

Open http://127.0.0.1:3000. Ctrl+C stops both children. Ports default to 3000/8001;
use --web-port=3106 and --api-port=8002 if occupied. The launcher sets matching
API/CORS origins for those ports and refuses invalid or occupied ports.
For a prebuilt frontend use `node scripts/dev.mjs --production` after building.
Production uses the build-time NEXT_PUBLIC_API_URL; automatic API-port overrides
are a development feature. Rebuild after changing public frontend variables.
Development uses frontend/.next; builds and production previews use
frontend/.next-production. This prevents a separately running dev server from
overwriting the production preview's chunks and breaking client interactions.

Separate terminals also work. Backend must start from the repository root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8001
```

Frontend starts from frontend/ with `npm run dev`. Restart the backend after
copying/training model files. A healthy HTTP server can have unavailable models:
/health stays 200, /ready returns 503 and /api/v1/status explains readiness.

## Restore or reproduce models

Final model artifacts use ml/saved_models/final_v1/{validator,body_part,fracture}/.
Tracked model_metadata.json files record their checkpoint filenames, checksums,
input resolution, normalization and policies. Copy the corresponding ignored
checkpoint binaries from a machine with the final artifacts, or reproduce:

```powershell
.\.venv\Scripts\python.exe -u -m ml.datasets.download_public
.\.venv\Scripts\python.exe -u -m ml.datasets.prepare_local
.\.venv\Scripts\python.exe -u -m ml.training.final_run --task body_part
.\.venv\Scripts\python.exe -u -m ml.training.final_run --task fracture
.\.venv\Scripts\python.exe -u -m ml.training.final_run --task validator
```

These commands download public, checksum-verified research datasets, group
duplicates before splitting and train actual custom CNNs. They require time,
disk and memory; they do not run at application startup. Interrupted downloads
resume; a mismatched/partial archive is never extracted as verified data.
No restricted dataset, paid service, account login or DUA is bypassed.
Historical Stage 3/4 checkpoints remain supported as a fallback only when complete.
Never create placeholder weights. See ml-models.md for scientific limitations.

Raw datasets, checkpoints, environment values, temporary files and patient
uploads must remain out of Git. The final completion pass does not connect a
live database, apply remote migrations or deploy any service.
