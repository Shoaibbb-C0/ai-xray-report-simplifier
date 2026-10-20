# Final local application architecture

The existing Next.js App Router, FastAPI and custom PyTorch architecture is
preserved. Analysis runs locally without Supabase or any external AI API.

1. The browser selects a JPEG/PNG and keeps its preview in a revocable object URL.
2. POST /api/v1/analyze receives a bounded multipart upload. Framework temporary
   spools and decoded images are closed on success and failure. Untrusted browser
   origins, unsupported formats, excessive dimensions/size and corrupt files are rejected.
3. One CPU pipeline per backend process loads verified local model checkpoints.
   Missing, malformed or checksum-mismatched checkpoints fail closed.
4. The validator returns X_RAY, NON_XRAY or UNCERTAIN. Only X_RAY reaches anatomy.
5. The body classifier recognizes hand/leg/hip/shoulder; low confidence becomes
   UNKNOWN. Mixed/unsupported anatomy does not reach fracture analysis.
6. The fracture model returns fracture/no_fracture/uncertain using its recorded
   validation-selected policy. Only fracture is in scope.
7. The existing deterministic Python explanation engine returns the Stage 5
   schema in English, Hindi or Marathi. Local text registries provide the copy.
8. The browser renders the uploaded image, explanation, educational illustration
   and optional model attention as distinct views. Uploads are not permanently saved.

The API returns request_id, status, xray_validation, body_part, abnormality,
explanation, model_versions, timings_ms and an explicit persistence.saved=false.
Model versions identify loaded checkpoint SHA256 values; absolute model paths
are not included. A lock bounds CPU inference concurrency. /health reports
server liveness; /ready and /api/v1/status report actual model availability.

Grad-CAM reuses the loaded fracture model and its actual input resolution.
It is available only for a supported, accepted X-ray with suspected fracture
features. It indicates model influence, not a confirmed injury location.
The experimental bounding-box head remains disabled for patients.

## Database-ready boundary

Supabase remains optional and disconnected in this completion pass. Existing
profiles, xray_scans and analysis_results migrations, ownership RLS, composite
scan/owner relationships and private xray-scans storage policies are retained.
No production migration, user, row or storage object is created by local analysis.

Without public configuration, map/history show explicitly empty offline views.
Counts are zero, not demo patient data. A detail URL cannot expose a fabricated
record. When configured later, the existing verified-user SSR/middleware guards
and owner-scoped repositories apply. Next 15 async cookie/route APIs are used.

The explicit save service derives ownership from auth.getUser(), inserts owned
scan metadata, uploads to a generated private owner/scan path, inserts the Stage 5
result and marks completion. Transient attention media are stripped on a copy.
Failure cleanup removes the private object before scan metadata. If file cleanup
fails, pending metadata is retained for recovery rather than orphaning a hidden file.
It never uses a service-role key. The local UI disables saving when unconfigured.
These connected behaviors are contract-tested without live credentials.

Saved results are educational records, not signed immutable clinical evidence.
Public-client RLS protects ownership; it does not establish clinical provenance.
Any later clinical deployment would require a separate security and clinical review.

## Frontend identity and accessibility

The interface uses a paper/ink/sage reading-room palette, restrained serif
headings and one primary upload workspace. It retains original owned anatomy
SVGs and the existing map interaction. Native buttons, file input, language
select, visible focus, live status/error messages and reduced-motion CSS are used.
Image object URLs and requests are cleaned up on removal/unmount.

No frontend TypeScript conversion, external inference service, deployment,
analytics collection, fake authentication or fake persistence is introduced.
