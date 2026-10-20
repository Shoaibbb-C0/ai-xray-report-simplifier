# Final completion audit

The final brief continues the same project. Starting local HEAD for this
completion scope was d379539 on main (the preceding PC restoration commit).
The historical stages and architecture were read before changes. Live database
connection/configuration and deployment are excluded from this scope.

## Verified starting architecture

- Next 14 App Router, JavaScript/JSX, Tailwind; public landing and developer
  explanation previews, Supabase auth/SSR, protected patient map/history/detail.
- FastAPI health/status endpoints and a placeholder inference service, without
  an upload/analyze application endpoint.
- Three custom PyTorch CNNs, adapters/splitting/metrics/training/evaluation tools,
  Stage 3/4 cascades and deterministic Stage 5 explanations/owned SVG artwork.
- Supabase migrations and local PostgreSQL tests for owner RLS/private storage.
  Live configuration was backed up to an ignored file and is inactive in this pass.
- Trained weights and raw datasets were missing on this PC. Existing model
  reports described a previous computer; their metrics are historical evidence.

## Gaps found and addressed

| Finding | Action |
| --- | --- |
| No real application upload/analysis path | Bounded in-memory FastAPI endpoint and complete browser workspace |
| Missing checkpoints could leave random models active | Fail-closed loading, checksums, explicit readiness and missing-model tests |
| Uncertain validator still ran the anatomy model | Stop before anatomy on uncertain/non-X-ray |
| Mixed anatomy was eligible for fracture routing | Limit routing to the four supported primary regions |
| Real rejected cascade sections can be null | Normalize null sections; preserve eight explanation states |
| Explanation re-applied an old validator confidence cutoff | Respect the explicit cascade decision from the recorded validation policy |
| Unknown/rejected copy implied proven unsupported anatomy or clinical quality criteria | Describe model rejection and possible error without unsupported calibration claims |
| Partial Hindi/Marathi safety/next-step copy | Complete curated local registry and translate result headings |
| Historical "real X-ray" tests used an architecture screenshot | Use verified local FracAtlas radiographs for actual-image checks |
| Missing raw datasets broke machine-dependent tests | Explicit prerequisites plus deterministic temporary registry fixtures |
| Landing described features without an upload CTA | Clear primary analysis task, preview/removal, errors and loading |
| Database-absent map led into unavailable login | Honest zero-count offline map/history; configured routes stay protected |
| No explicit future-connected result save adapter | Owner-derived private upload/result contract and cleanup tests |
| Next 14 critical Windows advisory | Patched Next 15.5.28 / React 19.3.1 and async cookie/route APIs |
| Next nested vulnerable PostCSS | Compatible PostCSS 8.5.29 override; runtime audit is clear |
| Tied ROC scores received arbitrary ranks | Average tie ranks; regression case checks neutral AUC |
| Attention padding misaligned for images smaller than model input | Remove model padding from the transparent overlay; test small/square and portrait images |
| JPEG EXIF orientation could differ between browser and model | Normalize orientation after safe decoding; verify a rotated JPEG |
| Starting two services required missing global npm | Small root Node launcher with port checks and process cleanup |
| A separate dev server overwrote production chunks and broke map hydration | Isolate .next development output from .next-production build/preview output |

## Evidence boundaries

Software mocks explicitly test contracts and do not claim learned model accuracy.
Fresh training/evaluation artifacts are under ml/saved_models/final_v1, separate
from prior Stage 3/4 reports. New manifests group perceptual near duplicates
before splitting. FracAtlas has no verified patient IDs; this is a duplicate
proxy, not a claim of demonstrated patient isolation.

Training uses 128px inputs consistently for practical CPU use; this is not a
direct reproduction of the historical 224px benchmark. One interrupted initial
body training attempt was stopped before any final test evaluation to make that
hardware decision. Final model/checkpoint/threshold choices use validation only.
The fracture pass is bounded to a baseline and one conservative augmentation
candidate. Frozen test results and OOD results must be reported honestly.

The new completion scope makes no live Supabase call or deployment. Repository
auth/persistence/RLS are verified with mocks and embedded PostgreSQL. Real
accounts, email delivery and remote isolation remain outside this pass.

Final consolidated checks, metrics, screenshots, commit and push outcomes belong
in testing.md, ml-models.md and the final engineering report after they finish.
