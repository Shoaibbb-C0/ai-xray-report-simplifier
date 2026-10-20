# Final local verification

This report separates software correctness, actual learned-model evaluation and
manual browser acceptance. Mocks are explicitly test-only and do not establish
model accuracy. No live database or deployment was used in this completion pass.

## Automated software checks

- Python: **91 passed, 0 failed, 0 skipped** with the real restored datasets and
  all three freshly trained model checkpoints available.
- Frontend Node tests: **14 passed, 0 failed, 0 skipped**. This includes embedded
  PostgreSQL/PGlite migration and two-user RLS/private-storage isolation; auth
  middleware/async SSR cookies; repositories; save/cleanup contracts; upload
  client behavior; result-state rendering; and keyboard map semantics.
- Total automated test cases: **105 passed**. PostgreSQL and other integration
  cases are included in these counts, not added again.
- Next.js 15.5.28 production build passed for every route. Home: 5.62 kB route
  code and 116 kB first-load JavaScript; shared first-load JavaScript 103 kB.
- Python pip check, Python compileall, Node launcher syntax check and Git
  whitespace check passed.

Python emits one Starlette/httpx deprecation warning. Node emits implicit-ESM
package warnings for the existing mixed Next config/module layout. These are
warnings, not ignored test failures. A clean test run does not imply clinical
validity or zero dependency advisories.

API tests cover MIME/content disagreement, SVG, corrupt/truncated files, minimum
dimensions, oversized files, language errors, narrow CORS/Origin checks,
missing/corrupt/checksum-mismatched weights, unavailable readiness, busy inference,
non-finite model output, private response headers, safe error messages and image
cleanup. JPEG EXIF orientation and attention padding alignment have regressions.
Cascade/explanation tests include rejected, unsupported, uncertain, unavailable
and error states, translations, forbidden medical claims and disabled localization.

## Real HTTP acceptance

`scripts/check_local_api.py` called the running local production application with
the actual trained weights. It used **22 public validation/OOD examples**, plus
corrupt-file and unsupported-SVG requests. All 24 upload requests returned their
expected HTTP/schema behavior; /health and /ready also passed, with 3 models
loaded. Outputs were finite, versioned by SHA256, private/no-store and explicitly
not saved. English, Hindi and Marathi were exercised. These selected examples
are acceptance cases, **not a representative accuracy estimate**.

| Actual explanation state | Count |
| --- | ---: |
| Possible fracture-related features | 3 |
| No strong fracture-related signal | 6 |
| Fracture result uncertain | 6 |
| Body part unknown | 1 |
| Non-X-ray rejected | 6 |

All 3 suspected-fracture cases generated real Grad-CAM. Other states suppressed
attention. Initial measured HTTP latency was 11.3–276.8 ms, median 39.4 ms on this
PC; this small warm/local sample is not a throughput or clinical benchmark.
Detailed local evidence is ignored under `.venv/local-api-check.json` and its log.

Important observed failures of the learned models are retained: both mixed-region
examples were assigned supported anatomy and reached fracture scoring; one
supported hand-label example became UNKNOWN; some fracture-label examples got
no-signal/uncertain outputs and some non-fractured examples got suspected outputs.
The unknown UI case therefore demonstrates a real low-confidence rejection, not
proof that every unsupported image is detected. No model or threshold was tuned
after these observations. See ml-models.md for the frozen benchmark errors.

Before training, the genuinely absent checkpoints produced real HTTP 503,
unready status and the browser's unavailable message, with no prediction.
That is separate from deterministic missing/corrupt-file software tests. After
training and restart, /ready returned 200 with all three verified artifacts.

## Browser acceptance and responsive checks

The in-app browser exercised upload/preview, remove/replace, real loading and
successful requests, unavailable-model errors, all five real result states above,
language changes and re-analysis, loaded educational SVGs, actual attention and
its keyboard opacity control. Unsupported files are rejected before submission.
Result focus and polite status/error announcements are present. Saving remains
disabled, and history explicitly says it is unavailable without a database.

Desktop 1280px, tablet 768px and phone 375px layouts were inspected. DOM width
checks found no horizontal overflow; Marathi result content was also checked at
375px. The map was operated with Enter/Space, and the opacity slider with an
arrow key. Native controls, visible focus, a skip link and 44px primary targets
support keyboard/touch access. Reduced-motion behavior is implemented by a
prefers-reduced-motion CSS rule; it is a source-level check, not a claim that a
complete assistive-technology audit was performed.

Screenshots are local Codex evidence outside the repository; no dataset image or
patient screenshot is added to Git. The application remains a local prototype.
Real email delivery, two verified remote accounts, live owner isolation and
connected save/delete operations are deliberately outside this scope. Local
contracts and PostgreSQL checks do not replace those future connected checks.

## Actual model evaluation

Fresh frozen evaluations used 1,092 validator, 500 anatomy and 551 fracture
examples, with an additional 500 DermaMNIST OOD examples. These task cohorts
overlap; do not sum them into a claim about distinct patients. Each final test
was loaded only after validation selected its checkpoint and policy. Reports,
confusion matrices, per-class/per-region metrics, ROC/PR curves, hashes and
limitations are retained under final_v1 and summarized in ml-models.md.

Grad-CAM is tested as a software visualization, not an accurate lesion locator.
The experimental localization head is not presented as trained or validated.

## Repeat the checks

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -rs
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m compileall -q backend ml scripts
node --check scripts/dev.mjs
git diff --check
cd frontend
npm test
npm run build
npm audit --omit=dev
npm audit
```

Use the npm CLI fallback documented in local-development.md if npm is not on
PATH. Run `node scripts/dev.mjs --production` from the root after building,
then in another root terminal:

```powershell
.\.venv\Scripts\python.exe scripts/check_local_api.py
```

The public raw validation images and exact final model files must be available.
On a fresh checkout, real-data/model tests explicitly skip missing prerequisites;
that does not recreate this full 91-test pass. Restore or train the ignored
artifacts first. The API acceptance script intentionally fails if readiness is
unavailable. It never fabricates outputs or contacts Supabase.

The pinned Python pip-audit and runtime npm audit found no known vulnerabilities;
the full development npm audit retains 7 documented
Tailwind-chain advisories. See security-review.md for exact scope and boundaries.
