# Local security review

Scope: repository changes for local educational use, with no live database or
deployment. This is a focused engineering review and regression testing, not
a penetration-test certificate or clinical compliance assessment.

## Input, output and privacy boundaries

- Upload filenames are display text only. React escapes them; the backend never
  joins a supplied filename to a filesystem path. Save paths use generated UUIDs
  and the verified authenticated owner.
- JPEG/PNG MIME allowlisting is followed by actual decoded-format validation,
  verification and full decoding. SVG, animation, truncation, damaged images,
  excessive dimensions and excessive file size are rejected.
- The file limit is 10 MiB, multipart request limit 11 MiB, image dimensions
  64–8192 pixels per side and at most 16 megapixels. A declared upload length is
  required. Files may use the framework's temporary spool; UploadFile and decoded
  images are closed in a finally block, including failures. No permanent upload
  folder is created by analysis.
- Local browser origins are explicitly allowlisted. Untrusted supplied Origin
  headers are rejected before analysis. The server binds loopback by default.
  CORS is not authentication: scripts on the same computer can call the API.
- Missing/corrupt/checksum-mismatched weights fail closed. Inference loads use
  PyTorch weights_only=True. Model binaries are trusted local build artifacts;
  checksums detect changes, not malicious provenance in an already altered repo.
- Responses exclude local model/image paths and tracebacks, reject non-finite
  model output, and use private/no-store and nosniff headers for analysis.
  Access logs contain routes/status, not image bytes. Do not enable body logging.
- No external AI/translation service or image analytics is used. Previews are
  revocable browser object URLs. Saving is a separate explicit operation;
  disconnected mode always reports saved=false and shows zero history counts.
- Educational SVGs are owned static assets rendered as images, with accessible
  descriptions. Uploaded SVG or arbitrary HTML is never inserted into the DOM.
- Public Supabase configuration is optional. No service-role key belongs in the
  browser. RLS, owner filters, private storage and verified-user guards retain
  their existing boundaries and have local contract/PostgreSQL tests.

## Dependencies

The original Next 14 version was affected by a Windows-specific critical issue
with no patched 14.x line. The smallest supported fixed major was adopted;
Next 15.5.28, React 19.3.1 and compatible async APIs pass the application tests
and production build. See the [Windows advisory](https://github.com/vercel/next.js/security/advisories/GHSA-p293-qw3h-jr36)
and [October 2026 security update](https://nextjs.org/blog/nextjs-security-update-october-14-2026).
Next's nested PostCSS uses a compatible 8.5.29 override.

The final npm production dependency audit reports **zero vulnerabilities**.
The full development audit reports **7**: 5 high and 2 moderate, through the
Tailwind 3 build chain (braces, chokidar, micromatch, fast-glob,
postcss-selector-parser, postcss-nested and the parent Tailwind package).
The underlying issues are pattern/selector denial of service:
[braces](https://github.com/advisories/GHSA-vfj7-8cjw-p6xm) and
[selector parser](https://github.com/advisories/GHSA-rj75-hqrm-r3gf).
The offered overall fix is a Tailwind 4 major migration. No untested forced
overrides or unrelated CSS migration are applied. These build tools must process
trusted repository sources, not user-supplied CSS/glob patterns. They are a
recorded residual development risk, not a claim of a completely clean full audit.

Python's pip check verifies dependency consistency. A separate pip-audit scan of
the fully pinned requirements-lock.txt found **no known vulnerabilities** in its
advisory database at verification time. The audit tool ran in an isolated ignored
environment, without adding application dependencies. This is not a guarantee
against unknown vulnerabilities. The tested versions are recorded in the lock.
Environments, raw
data, checkpoints and credentials are ignored and excluded from commits.

## Limits before internet use

This local API is deliberately unauthenticated and synchronous, with one active
CPU inference per process. It is not an internet-facing multi-user service.
Deployment would require an authenticated perimeter, transport/upload limits,
appropriate rate/resource limits, operational monitoring and privacy review.
No such deployment or live database change was performed in this completion pass.
