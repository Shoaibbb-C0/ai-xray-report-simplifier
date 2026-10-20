# AI X-Ray

A local patient-support application that helps people understand an X-ray and
prepare for a conversation with a clinician. It uses our own trained PyTorch
models and deterministic explanations. No hosted AI inference or translation API.

**Educational support, not a diagnosis.** A clinician must interpret the image
with symptoms, examination and radiology findings. A negative model signal does
not rule out a fracture.

## Scope and experience

- Upload, drag/drop, preview, replace and remove a PNG/JPG/JPEG (up to 10 MiB).
- Validate image content, decoding, size and dimensions before inference.
- Route through X-ray validation, coarse anatomy and fracture classification.
- Explain suspected/no-signal/uncertain/unsupported/rejected/unavailable/error states.
- Read explanations in English, Hindi or Marathi, using curated local text.
- Keep the uploaded image, model attention and educational anatomy visibly distinct.
- Explore the original keyboard-accessible My X-Ray Map and region filters.
- Use the complete analysis workflow without an account or database connection.

**Supported anatomy:** hand, leg, hip, shoulder. **Supported finding:** fracture
features only. Mixed, unknown and low-confidence inputs are handled cautiously.
The application does not diagnose other diseases or promise reliable detection
of every unsupported body region.
The real local checks observed mixed images routed to supported classes;
the four-class anatomy model cannot reliably exclude all unsupported inputs.

## Architecture

```text
Browser upload → FastAPI image validation → X-ray validator
  → supported-body classifier → fracture classifier
  → deterministic Python explanation → result and educational visuals
```

The validator stops non-X-rays and uncertain inputs before anatomy. The anatomy
model can reject low confidence as UNKNOWN. The fracture model uses recorded
validation-derived decisions/rejection bands. Missing, corrupted or checksum-
mismatched weights fail closed; random weights never become patient predictions.
Models load once per backend process and reuse CPU memory. Files are processed
in memory and temporary multipart resources are closed on every request path.

- Frontend: **JavaScript/JSX**, Next.js 15.5.28, React 19.3.1, Tailwind CSS 3.
- Backend: Python/FastAPI, Pydantic, Pillow; narrow loopback CORS and bounded uploads.
- ML: custom XRayValidatorCNN, BodyPartClassifierCNN and FractureClassifierCNN.
- Explanations: local Python Stage 5 schema, curated translations and owned SVGs.
- Database-ready: Supabase Auth/SSR, profiles/scans/results, owner RLS and private storage.

See [architecture](docs/final-architecture.md), [engineering audit](docs/engineering-audit.md)
and [model/evaluation documentation](docs/ml-models.md). Historical stages remain
under docs/ and retain their original reports; the new run uses final_v1 artifacts.

## Run locally

The restored environment on this PC is ready for the root launcher:

```powershell
node scripts/dev.mjs
```

Open http://127.0.0.1:3000. Ctrl+C stops both services. For another machine:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
cd frontend
npm ci
cd ..
node scripts/dev.mjs
```

The checkpoint binaries are intentionally ignored. Restore the final weights or
run the reproducible public-data/training commands in [local development](docs/local-development.md).
The server can run without models, but analysis returns an explicit unavailable
response. It never makes a placeholder prediction.

Separate-terminal commands:

```powershell
# Repository root
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8001
# A second terminal, from frontend/
npm run dev
```

/health checks the server, /ready checks actual model readiness, and
/api/v1/status reports the loaded engine. POST /api/v1/analyze accepts multipart
file, language (en/hi/mr), and optional attention. See [testing](docs/testing.md).

## Environment and database boundary

Set NEXT_PUBLIC_API_URL in ignored frontend/.env.local (safe local example:
http://127.0.0.1:8001). The frontend example file lists all supported names.
Backend CORS_ORIGINS, HOST and PORT are process environment settings with safe
loopback defaults. Public frontend variables are baked into production builds.

Leave NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY blank
for the local workflow. NEXT_PUBLIC_SUPABASE_ANON_KEY is an optional legacy
alternative. No service-role secret belongs in the browser or repository.

Without database configuration, map/history show honest empty views and saving
is disabled. No patient history or authentication success is fabricated. When
connected later, SSR guards and RLS enforce ownership; the explicit save adapter
uses private owner/scan storage paths and strips transient attention media.

The existing xray-simplifier project was previously migrated. This completion
pass does **not** connect/configure it, create users, apply remote migrations or
deploy. Verify migration history before any future database setup; do not
blindly reapply the Stage 6 migrations.

## Tests and reproducibility

```powershell
.\.venv\Scripts\python.exe -m pytest -q -rs
cd frontend
npm test
npm run build
npm audit --omit=dev
```

The suites cover file/endpoint safety, model availability, cascade gates,
explanations, languages, owned persistence contracts and embedded PostgreSQL
RLS/storage isolation. Optional real-data/model tests explicitly skip if their
ignored prerequisites are absent; a skip is not a learned-model pass.
The final test report separates software checks, actual model evaluation and
browser verification. Tests/mocks do not fabricate clinical results.

Public training data: FracAtlas, CIFAR-10, RetinaMNIST; DermaMNIST is held out
for validator OOD evaluation. Sources, licenses, duplicate-group limitations,
minority-class results, checkpoint hashes and frozen test metrics are documented
in [ML models](docs/ml-models.md). Thresholds/model choices use validation only.
Raw data, patient uploads, checkpoints, environments and package/build caches
must never be committed.

## Limitations and next steps

See [medical limitations](docs/medical-limitations.md). False negatives and false
positives are possible; model scores are not calibrated medical certainty.
The research datasets do not establish clinical validity. Grad-CAM is model
attention, not injury localization. Patient-facing bounding boxes stay disabled.

Remaining integration boundaries are live database credentials/configuration
and deployment. Those actions are deliberately excluded from this local pass.
Before any internet deployment, review configuration, patient privacy, licensing,
capacity, remaining development-tool advisories and real authenticated isolation.
