# NEW PC + STAGE 6 VERIFICATION REPORT

Verified on 21 October 2026 (Asia/Calcutta). This report records this PC's
checks separately from the historical live acceptance results in commit a7b3016.

## 1. Repository

- Existing checkout reused; fetch and fast-forward-only pull were already current.
- Branch: main. Starting HEAD: a7b301609cf73617334b50dce8003fdc9822fc3b.
- Current HEAD: the commit containing this report and the test portability fixes;
  obtain its identifier with `git log -1 --oneline`.
- Starting working tree: clean. Reviewed all stage commits, documentation,
  frontend/auth/data flow, backend, ML architecture/inference/explanation code,
  dataset software and tracked reports/manifests, assets, tests and migrations.
- No repository AGENTS.md was present. No new clone, retraining or Stage 7 work.

## 2. New PC Environment

| Item | Verified value |
| --- | --- |
| OS | Windows 11 Pro, 10.0.26100 |
| Git | 2.53.0.windows.3 |
| Python | 3.12.14, local .venv using Codex's bundled Python |
| pip | 25.0.1 in .venv; bundled base Python has 26.2.1 |
| PyTorch / torchvision | 2.14.1+cpu / 0.29.1+cpu |
| Node / npm | 24.19.0 / 10.9.2 |
| CPU | Intel Core i3-1115G4, 2 cores / 4 logical processors |
| RAM | Approximately 7.80 GiB visible |
| GPU / CUDA | Intel UHD Graphics; torch.cuda.is_available() is false |

Python and npm initially were absent from PATH. Node was already bundled with
Codex. npm was restored outside the repository under
`%LOCALAPPDATA%/xray-dev-tools/package`; no system-wide PATH change was made.
The virtual environment depends on the bundled Python installation remaining
available. A standalone Python installation is not claimed.

## 3. Local Runtime Restoration

- Created .venv and installed the actual root requirements without editing versions.
- Verified Python, PyTorch, torchvision, Pillow 13.0.0, NumPy 2.5.4,
  FastAPI 0.156.1, Uvicorn 0.54.0, pytest 9.1.1 and `pip check`.
- Installed frontend dependencies with the unchanged package-lock via `npm ci`.
- Restored ignored frontend/.env.local from the correct project's public
  configuration. Names: NEXT_PUBLIC_API_URL, NEXT_PUBLIC_SUPABASE_URL,
  NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY. NEXT_PUBLIC_SUPABASE_ANON_KEY is an
  optional legacy alternative, not an additional requirement.
- backend/.env remains absent; current backend defaults work without it.
- Raw FracAtlas data and trained checkpoints are missing. They are intentionally
  ignored runtime artifacts, not repository corruption.
- Recorded this PC's resolved Python dependencies in ignored
  `.venv/installed-requirements.txt`. Root requirements specify lower bounds,
  so installation is not a reconstruction of the previous PC's exact packages.

Run the backend from the repository root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8001
```

Run the frontend from frontend/ using this PC's restored npm CLI:

```powershell
$xrayNpmCli = Join-Path $env:LOCALAPPDATA 'xray-dev-tools/package/bin/npm-cli.js'
node $xrayNpmCli run dev -- --hostname 127.0.0.1 --port 3000
# For the verified production build:
# node $xrayNpmCli run start -- --hostname 127.0.0.1 --port 3000
```

Ports 8001 and 3000 were available and served successfully during verification.
Stop an existing instance before reusing its port.

## 4. Model Checkpoints

**Model checkpoints are missing on the new PC.** Copy these trained files from
the previous PC to the same repository-relative locations:

```text
ml/saved_models/stage3/validator/best_validator.pt
ml/saved_models/stage3/body_part/best_body_part.pt
ml/saved_models/stage4/fracture_classifier/best_fracture_classifier.pt
```

Hashes cannot be verified until those files exist. Tracked Stage 4 metadata
expects SHA256 `6696910128f3c0baf8d1d5725c83f4f85620be89511fda6400593cfc48e8ab31`.
No explicit Stage 3 checksum was found in its tracked model report directory;
retain the previous PC's checksum records when copying those files.

**Real model inference is blocked.** Existing inference loaders silently leave
randomly initialized models when a checkpoint is absent. They were not used for
predictions on this PC. Tests now skip trained-inference cases before running
those loaders' predictions. Software-only architecture/gradient/serialization
tests use synthetic inputs and temporary test weights; these are not trained
model validation. No replacement trained files were created and no retraining ran.

## 5. Supabase

- Selected: xray-simplifier, reference talyttxfpdpfkuascidt, College projects connection.
- Connection: ACTIVE_HEALTHY; public Auth and REST endpoints reachable.
- Both recorded migrations confirmed: 20261016202619_stage6_patient_history
  and 20261016202700_stage6_result_owner_index.
- profiles, xray_scans and analysis_results exist with RLS enabled.
- Reviewed the separate CRUD ownership policies, UPDATE WITH CHECK predicates
  and storage ownership policies. No schema changes or migration reapplication.
- xray-scans bucket exists, is private, permits PNG/JPEG, limit 10 MiB.
- Security advisor: no findings. Performance advisor: no findings.
- Auth users: 0; confirmed users: 0. Only aggregate counts were read.
- Anonymous REST requests to all three patient tables returned HTTP 401.

## 6. Live Authentication

- Signup configuration: email/password and signup enabled; email confirmation required.
- Login/signup HTML served with email/password fields; no account was submitted.
- Missing and invalid callback codes both redirect to verification failure.
- Anonymous map/history/detail/profile routes redirect to login with private/no-store.
- Actual signup, email delivery/verification, login, logout and session persistence
  remain blocked by the absence of verified accounts. The user selected
  "Finish available checks and document the blocker."

## 7. Two-User RLS Verification

- This PC: no authenticated A/B sessions; own CRUD and cross-user API/storage
  tests were not run. No production users were fabricated or confirmation bypassed.
- Bidirectional SELECT/UPDATE/DELETE isolation, ownership changes, foreign result
  associations and storage policies passed the embedded PostgreSQL suite.
- Embedded PostgreSQL models Supabase interfaces; it is not live authenticated
  Supabase API evidence. The SQL connector likewise is not proof of user-session RLS.
- Commit a7b3016 documents historical live checks and cleanup; that evidence
  is preserved, not represented as a fresh run.

## 8. My X-Ray Map

- Hand, leg, hip and shoulder targets present in the existing component.
- Counts, latest dates, region filtering and mixed/unknown handling passed unit checks.
- Eight SVG buttons, tab stops, labels, Enter/Space handlers and responsive viewBox
  passed rendering/handler checks; focus styles and responsive CSS were inspected.
- No personalized anatomy or inferred laterality added.
- Authenticated desktop/mobile browser interaction remains unverified on this PC.

## 9. History

- Repository tests verify owner/region filters, empty history, detail ownership and IDs.
- Source queries sort newest scan_date first, then ID; embedded database isolation passed.
- Stage 5 JSON roundtrip tests pass for hand/leg/hip/shoulder/mixed/unknown.
- Explanation rendering reuses existing Stage 5 components; no JS explanation engine.
- Anonymous direct detail URL redirects. Authenticated own and foreign UUID navigation
  requires the two verified accounts and was not repeated.

## 10. Tests

| Check | Result |
| --- | --- |
| Python full collection | 66: 55 passed, 11 skipped, 0 failed/errors |
| Frontend Node suite | 8 passed, 0 failed |
| Database | Included in Node suite: embedded PostgreSQL migrations/RLS/storage |
| Combined automated suite | 74 collected: 63 passed, 11 skipped |
| Production build | Passed, Next 14.2.35 |
| Backend HTTP | /health, /api/v1/health, /api/v1/status all 200 |
| Frontend HTTP | 10 checks passed: 4 public pages, 4 protected redirects, 2 callbacks |
| Remote anonymous REST | 3 patient tables denied with 401 |
| Dependency consistency | pip check passed; frontend lockfile unchanged |

The 11 skips comprise 4 raw FracAtlas tests and 7 trained inference/Grad-CAM
tests. Software checks passed; real model inference is blocked by missing local
checkpoints. Existing FastAPI/httpx deprecation and Node module-type warnings remain.

Dependency audit: 9 affected packages (1 critical, 6 high, 2 moderate).
Installed Next is already 14.2.35. The Windows RCE advisory explicitly includes
this version; its first fix is 15.5.24, and the October 14 update publishes
15.5.28/16.4.1 for additional issues. No compatible Next 14 patch was identified.
App Router is used, but this app does not configure remote image patterns,
rewrites, CSP nonces, Cache Components or explicit Server Actions; advisory
conditions differ and a package audit is not proof that every issue is exploitable.
The Windows server advisory is directly relevant. Both verification servers bind
only 127.0.0.1. A supported-major upgrade requires separate compatibility work
(including cookies/route API changes); it was not folded into this restoration.
No dependency was arbitrarily upgraded or audit finding suppressed.

Sources: [Windows RCE advisory](https://github.com/vercel/next.js/security/advisories/GHSA-p293-qw3h-jr36),
[October security update](https://nextjs.org/blog/nextjs-security-update-october-14-2026),
[App Router DoS advisory](https://github.com/vercel/next.js/security/advisories/GHSA-q4gf-8mx6-v5v3).

## 11. Changes Made

- Dataset registry test uses temporary directories to verify missing, incomplete
  and available dataset states without changing the global registry.
- Optional real-data tests skip explicitly when the raw FracAtlas dataset is absent.
- Trained inference and Grad-CAM tests skip explicitly when checkpoints are absent.
- Added this restoration report and linked it from setup documentation.
- Application code, ML thresholds, training, explanation schema, database and lockfile unchanged.
- Credentials/configuration, virtual environment, packages and build artifacts remain ignored.

## 12. Git

Review `git diff --check`, the full diff and `git status` before committing.
Commit the test portability fixes and documentation together, then push main
without force. The final chat report records the resulting commit/push status.
No environment file, credential, patient image, raw dataset or trained checkpoint
belongs in the commit.

## 13. Remaining Manual Actions

1. Copy the three trained checkpoints from the previous PC and verify their hashes.
2. Copy raw FracAtlas to ml/datasets/raw/fracatlas if real-data regression checks
   are desired; no download or retraining was initiated.
3. Create and email-verify two test accounts through the application, then provide
   authenticated browser sessions for live auth, persistence, mobile acceptance
   and bidirectional database/storage isolation testing. Keep passwords out of chat.
   The existing live harness only accepts marked disposable example.invalid users;
   it cannot directly consume ordinary email-verified accounts unchanged.

## 14. Stage 6 Decision

**NOT COMPLETE. Overall verified progress: 79%.**

Live verification on this PC is blocked by missing verified test accounts;
authenticated mobile acceptance and real email delivery remain outstanding.
Real ML inference separately requires the local trained checkpoints. Dependency
remediation requires a scoped major-version migration. Do not claim 87% or begin Stage 7.
