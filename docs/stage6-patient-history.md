# Stage 6 — Supabase, My X-Ray Map and patient history

## Status

The selected Supabase project is connected and both migrations are applied.
Live SQL isolation plus 57 Auth/PostgREST/Storage/SSR acceptance checks passed
with disposable confirmed accounts. Test objects, rows and accounts were removed.
Real-email verification delivery and authenticated mobile viewport acceptance
remain unverified; do not claim full Stage 6 acceptance or the 87% target yet.
No Stage 7 work is included.

## Repository audit

Started on clean `main` at `ed9dee0`, matching `origin/main`. History consists
of initialization `5b01403`, foundation `e2b7ce9`, datasets `582dc12`, Stage 3
`923197b`, Stage 4 `4e2ff9e`, and Stage 5 `ed9dee0`. Reviewed stage history,
repository layout, architecture/roadmap/safety documentation, dataset and
model metadata, inference gates, explanation contract/components, FastAPI
routes/configuration, frontend configuration and existing tests.

The architecture remains JavaScript Next.js 14 App Router + Tailwind, FastAPI,
and local PyTorch. Stage 3 validates radiographs and classifies coarse anatomy;
Stage 4 evaluates fracture only with its existing uncertainty band; Stage 5
produces deterministic multilingual ExplanationResult JSON and original SVGs.
Training, datasets, checkpoints, thresholds and existing explanation components
are unchanged. The Stage 4 checkpoint hash matches its recorded metadata.
Checkpoints and raw dataset directories remain ignored. Tracked credential-pattern
checks found no secret keys/JWTs/private keys. The two existing ML learning images
were preserved; no patient image or generated attention image was added.

Baseline: 57 Python tests and production build passed before implementation.
Use `.venv/Scripts/python.exe`; the system Python lacks pytest. No repository
AGENTS.md was found. No project Supabase environment or linked CLI state existed.

## Data architecture

Authenticated frontend server reads use the patient's public-key client and
cookie session. RLS enforces ownership independently of UI filters. FastAPI
does not gain a persistence endpoint or service-role key. The new Pydantic
contracts are a boundary for future persistence, not a new upload pipeline.

| Table | Fields |
| --- | --- |
| profiles | id (= auth.users.id), display_name, preferred_language, height_cm, weight_kg, created_at, updated_at |
| xray_scans | id, user_id, created_at, updated_at, scan_date, body_part, body_side, source_filename, storage_path, mime_type, status |
| analysis_results | id, scan_id, user_id, created_at, xray_validation_result/confidence, body_part_result/confidence, fracture_result/confidence, analysis_status, model_versions JSONB, explanation JSONB |

Each scan references auth.users directly: deleting a profile alone does not
delete scan history. Auth user deletion cascades through profiles, scans and
results. Results use a composite `(scan_id,user_id)` foreign key to
`xray_scans(id,user_id)`, preventing cross-owner associations even when a caller
supplies its own valid user ID. One result per scan is enforced by unique scan_id.
Deleting a scan cascades only to its result. Useful indexes cover user/date,
user/body region/date and result owner; the result unique index covers scan lookup. A follow-up covering index on
(scan_id,user_id) resolves the live foreign-key advisor finding.
Profiles and scans have updated_at triggers with empty search_path and revoked
public function execution. Profile initialization on login/callback is an RLS
upsert with ignoreDuplicates; existing preferences are preserved.

RLS is enabled on every patient table, with separate SELECT, INSERT, UPDATE and
DELETE policies. UPDATE has both USING and WITH CHECK ownership predicates.
Anonymous table grants are revoked; authenticated CRUD is explicitly granted.
No security-definer helper, user_metadata authorization or public view is used.
User-editable saved results are educational records, not an immutable clinical
record. Stage 7 must authenticate its caller and control model provenance when
it connects inference to persistence.

Height/weight are nullable metadata and never change anatomy. Canonical regions:
hand, leg, hip, shoulder, mixed, unknown. Unknown values in history navigation
fall back to unknown; persistence validates the enum strictly. Side is only
left/right/unknown/null when supplied, never inferred from screen position.

## Authentication and routes

`@supabase/ssr` and `@supabase/supabase-js` are exactly pinned in the lockfile.
Browser and server clients use public configuration only. Next.js 14 middleware
refreshes cookies, forwards refreshed cookies to both server and browser, and
uses `auth.getUser()` to verify the session with Supabase. Protected layouts
and each data page also verify the patient before reads. Never authorize with
an unverified cookie/getSession result. Personal responses use private/no-store.

Routes: `/signup`, `/login`, `/auth/callback`, `/map`, `/history`, `/history/[id]`.
Email/password signup handles session/no-session confirmation flows. Callback
exchanges the PKCE code and initializes the profile; failed/expired links return
to login with an explanation. Logout errors remain visible; successful logout
and cross-tab SIGNED_OUT events redirect to login. Auth state subscription is
cleaned up on unmount. Return destinations are restricted to local patient routes.
No tokens, passwords, patient names or image contents are logged.

## Map and history

Original React SVG standard skeleton, responsive viewBox, eight bilateral
48-unit targets for hand/leg/hip/shoulder. Both visual sides select the same
coarse region. SVG targets support focus, Enter/Space, aria-labels, aria-pressed
and visible focus; equivalent text buttons provide counts and filtering.
Mixed/unknown records remain available through text filters instead of being
placed on an invented anatomical location. Counts and latest dates derive
from actual user history, including empty histories. No runtime demo data.

`services/scans.js` centralizes list/region/detail reads and count/latest helpers.
Listing pages through PostgREST avoids silently truncating at its row cap.
Summaries omit large explanation JSON; details retrieve the result for a single
owned scan. Sorting is newest scan date first, then stable ID. The current map
loads all metadata to calculate exact counts; server aggregate/paginated UI can
be introduced if account histories become large.

Detail views reuse the Stage 5 ExplanationCard and AnatomicalIllustration.
Only local allowlisted anatomy SVG URLs render; private storage paths and stored
remote URLs are not rendered as images. Attention/localization metadata is
shown separately. Model confidence is labeled as a model score, not guaranteed
medical probability. Stage 6 copy is centralized in `lib/patient-copy.js` for
future hi/mr catalogs; the existing Stage 5 language registry is preserved.

## Stage 5 JSON and storage

`AnalysisRecord.persistence_payload()` preserves canonical explanation fields,
derives analysis_status/model_versions, and removes transient overlay_base64
and overlay_path on a copy. Attention availability becomes false because no
file was persisted. Python validates the original ExplanationResult schema;
SQL checks required JSON keys, object shapes/status agreement and rejects
inline attention Base64/data-image URLs. No explanation-generation logic was
duplicated in JavaScript.

Private bucket: `xray-scans`, 10 MiB per file, PNG/JPEG only. Object paths:
`<authenticated-user-uuid>/<owned-scan-uuid>/<filename>`. SELECT/INSERT/UPDATE
require both user prefix and an existing scan owned by that user. UPDATE checks
both old and new paths; new object paths must have exactly two folders and no
traversal/backslashes. DELETE permits the owner prefix even after scan deletion,
so leftover objects can be cleaned up through Storage API. No public policy or
public URL helper is added.

Image persistence is not enabled in the product. Stage 7 must delete stored
files via the Storage API before scan metadata, with retries if removal fails.
Database cascades do not delete underlying storage files. Account deletion
likewise needs explicit Storage API cleanup before deleting auth.users, plus
session revocation; no account-deletion workflow is claimed here.

## Local configuration

Node >=22 is required by the pinned Supabase SDK (tested on Node 24).
Copy `frontend/.env.example` to `frontend/.env.local` and set:

```dotenv
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=
```

`NEXT_PUBLIC_SUPABASE_ANON_KEY` is a legacy alternative if no publishable key is
set. Existing `NEXT_PUBLIC_API_URL` remains available. No backend Supabase secret
is needed. Local user-provided URL/key were saved only in ignored .env.local;
templates contain no real Supabase values. The selected project is reachable,
email/password signup is enabled, and email confirmation is required. Its scan
REST table returned 404 before applying the migration and is now available
with authenticated ownership checks.

## Apply and verify remotely

Access was restored through the College projects connection. The initial
project-access denial is resolved. Both migrations were applied and their local
filenames aligned with the recorded remote migration versions. The following
steps document setup for a fresh environment; do not reapply them to the
already migrated project.

1. Reconnect the Supabase connector in Codex using the account that owns the
   selected project, or grant the connected account access. Do not share a
   service-role key in chat. With access restored, the agent can inspect the
   target, apply the migration, run advisors and complete live checks.
2. For a fresh project without connector access, open the selected project's SQL
   Editor and run `supabase/migrations/20261016202619_stage6_patient_history.sql`
   once. Do not run against an unrelated project or an existing conflicting
   schema. The migration is transactional and deliberately not an overwrite.
3. In Authentication → URL Configuration, set the Site URL for the actual
   local app origin and allow its `/auth/callback` URL. Default development:
   `http://localhost:3000`; the verification server used port 3106 because
   3000 was occupied. Confirm email/password and email verification settings.
4. Run `supabase/tests/stage6_isolation.sql` in SQL Editor in a test project.
   It uses isolated DEMO UUIDs and rolls all rows back. Run the local test
   suite below too; SQL tests alone do not exercise Auth/Storage HTTP APIs.
5. With two disposable verified test accounts, confirm login/logout/reload,
   own history/detail access, foreign profile/scan/result reads returning no
   rows, foreign updates/deletes affecting no rows, forbidden ownership changes
   and mismatched result inserts rejected. Upload a harmless TEST PNG through
   Storage API to each owned scan path; verify the other account and anonymous
   caller cannot download, list, replace or delete it. Verify owner cleanup.
   Clean up object files, rows and test accounts. Never seed production patients.

Supabase CLI is available through `npx supabase`; no Docker/Postgres service or
linked CLI project was found. Migration filenames were generated by the CLI,
then aligned with the live MCP migration versions to avoid duplicate application.
Live migration, SQL isolation and API isolation checks passed on 17 October
2026 (Asia/Calcutta). The security advisor now reports leaked-password protection
disabled; performance advisors are clear. Enable leaked-password protection in
Supabase Auth settings if available on the project plan. No Auth protection was
disabled for testing. Confirmed test accounts were provisioned directly without
sending email or changing the email-confirmation requirement.

The opt-in `frontend/tests/live-stage6.mjs` harness exercises real login, own
profile/scan/result writes, bidirectional foreign read/update/delete rejection,
owner reassignment and mismatched associations, private file upload/download,
foreign download/list/replacement/deletion and signed-URL denial, anonymous
denial, authenticated Next.js pages, foreign detail 404 and logout redirect.
It accepts a temporary JSON file with two disposable confirmed accounts and
never prints credentials or tokens. It is not part of default npm test.

[Leaked-password protection remediation](https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection).

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest -q
cd frontend
npm ci
npm test
npm run build
npm run start -- --port 3106
```

66 Python tests pass (57 preserved + 9 Stage 6). The existing health tests
exercise `/health`, `/api/v1/health` and ML status with FastAPI TestClient.
8 Node tests pass, covering auth helpers, middleware redirection/cookie refresh,
region handling/filter/count/latest, scoped repositories/profile initialization,
keyboard map rendering and real embedded PostgreSQL migration/RLS execution.
Embedded PostgreSQL uses modeled auth/storage interfaces; it is not live
Supabase verification. Both directions of user isolation, owner reassignment,
composite foreign key rejection, anonymous denial, storage isolation, cascades,
JSON Base64 rejection and the portable SQL script execute locally.

Production build passes. HTTP checks: home/login/signup and `/dev/explanations`
200; unauthenticated map/history/detail 307 to login; invalid callback 307 to
verification failure message. Browser checks confirmed real Supabase login, authenticated map rendering,
hand-region selection, history navigation, logout returning to login, login
form appearance and protected map redirect. Map SSR/keyboard render is tested; authenticated
mobile browser testing remains part of live acceptance. CSS provides a single
column below 640px, flexible filters and bounded map sizing.

An initial generated Next build hit OneDrive readlink/manifest errors; moving
the generated .next tree to a temporary backup and rebuilding passed. No source
workaround or architecture change was needed. Existing warnings: FastAPI's
httpx deprecation and Node's implicit ES module detection for service tests.

`npm audit` reports 9 dependency issues, including a critical Next.js advisory
on the existing Next 14 line; suggested fixes include major Next/Tailwind
upgrades. Those upgrades were not silently folded into this stage. This
repository is not ready for production deployment; resolve dependency advisories
and complete live security testing before deployment.

## Files

- `.gitignore`, frontend environment template, package/lockfile, home navigation and CSS.
- `frontend/lib/{auth,patient-copy}.js` and `lib/supabase/{config,client,server}.js`.
- `frontend/middleware.js`, `services/{scans,profiles}.js`.
- AuthForm, PatientNav, BodyMap and ScanHistory components.
- Login/signup/callback and protected layout/map/history/detail/not-found routes.
- Backend `schemas/patient_history.py` and package initializer.
- Python Stage 6 tests and frontend history/middleware/render/database tests.
- Migration and portable SQL isolation tests under `supabase/`.
- This document plus README, architecture and roadmap updates.

## Intentionally deferred

No new abnormality models, retraining, threshold changes, final analyze endpoint,
upload-to-model workflow, appointment search, final premium UI or deployment.
The project stops at Stage 6 integration readiness. No Stage 7 implementation.

Sources: [Supabase SSR client setup](https://supabase.com/docs/guides/auth/server-side/creating-a-client)
and [Storage access control](https://supabase.com/docs/guides/storage/security/access-control).
