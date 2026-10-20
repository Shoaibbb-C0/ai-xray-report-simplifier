# Medical and research limitations

This is educational patient-support software for a college project. It is not
a medical device, diagnosis, radiologist replacement or clinically validated
screening service. Do not use it to decide whether an injury needs care.
The foundational privacy/safety policy remains in medical-boundary.md.

## What the model can and cannot say

The supported finding is fracture-related visual features in hand, leg, hip and
shoulder radiographs. It does not establish a fracture, determine injury age or
severity, predict treatment or diagnose other diseases. Mixed/unknown anatomy
and uncertain validation stop automated routing; classifiers can still make
confident mistakes outside their training distribution.

The four-class anatomy classifier has no learned mixed-anatomy output class.
It rejects low confidence, but cannot guarantee recognition of unsupported or
mixed images. In the real HTTP acceptance run, both mixed validation examples
were assigned supported regions and reached the fracture model. This is an
observed model limitation, not a successful unsupported-anatomy rejection test.
Coarse dataset anatomy labels also cover views beyond a single exact joint.

"No strong fracture-related signal" does not mean no fracture. False negatives,
false positives, implants, overlapping structures, acquisition differences and
dataset shift matter. The frozen-test report in ml-models.md includes actual
missed fracture labels, false positive counts and per-region results. Do not
hide those behind accuracy or an attractive interface.

Model scores are not calibrated medical probabilities. The system uses explicit
uncertainty bands to avoid forcing borderline scores into a confident class.
Binary benchmark metrics at the decision threshold must be distinguished from
the patient-facing three-state rejection policy.

## Data and scientific limits

- FracAtlas is a limited research dataset, not a prospective clinical cohort.
- Verified patient IDs are unavailable. Exact/near-duplicate image clusters
  reduce leakage but cannot prove that every patient/study is isolated.
- Hip/shoulder groups and their fractured subsets are small. Report support,
  precision and recall for each, not only overall accuracy.
- The new CPU-feasible 128px run is distinct from historical 224px results.
  Do not reuse old metrics as proof for new checkpoint binaries.
- CIFAR-10 natural negatives and RetinaMNIST/DermaMNIST medical photographs
  have low original resolution. Uniform upsampling and label-independent
  resolution augmentation reduce simple cues; source/frequency shortcuts and
  arbitrary-photo generalization remain unproven.
- Thresholds and checkpoint/experiment choices use validation only. OOD and
  frozen-test results are research evidence, not clinical validation.

## Visual boundaries

The uploaded image is the user's input. An educational SVG is a standard example
and never a personalized reconstruction. A simulated fracture illustration does
not indicate where a patient's bone is broken.

Grad-CAM is model attention: areas that influenced a prediction. It is neither
a lesion mask nor a confirmed fracture location. Clinical localization remains
false. Uncertain/non-X-ray/unknown cases do not receive patient-facing attention.
The experimental single-box localization code is not sufficiently validated;
patient-facing bounding boxes remain disabled.

## Language and privacy

Critical explanation summaries, next steps, limitations and result headings use
curated English/Hindi/Marathi text. No external translation/LLM API receives
images. A clinical product would still require professional language review.

Local analysis does not permanently save the upload. Previews are temporary
browser object URLs. History is explicitly unavailable without a configured
database and authenticated user. Later connected saving is an explicit action
through private owner-scoped storage, not an automatic side effect of analysis.
No patient image, credential or raw dataset belongs in Git.

Live database configuration and deployment are excluded from this completion
pass. Before any real patient or internet use, conduct separate clinical,
privacy, licensing, operational and authenticated security reviews.
