# Medical Safety Boundary & Privacy Policy

## Patient-Support Boundary
The AI X-Ray Project is an **educational support tool** created to help patients understand radiograph terminology and visual markers before or alongside clinical consultation.

### Non-Diagnostic Guarantee
- **Not a Medical Device**: The application does not provide clinical diagnoses, prescriptive advice, or primary care decisions.
- **No Replacement for Clinicians**: The system explicitly states it cannot replace licensed radiologists, physicians, or medical practitioners.
- **Terminology Standard**: System outputs must never use conclusive diagnostic phrasing (e.g., "Patient has pneumonia"). Instead, all outputs are framed as *possible findings*, *AI-assisted screening markers*, or *educational visual guides*.

## Privacy & Data Handling Guidelines
1. **Repository Hygiene**:
   - Never commit raw patient radiograph files, personal health information (PHI), or DICOM metadata containing patient names/IDs to Git.
   - All sample images in the repository must be anonymized open-access research samples.
2. **Local Data Isolation**:
   - Datasets must reside outside the repository index in local directories (`ml/datasets/raw/`, `ml/datasets/processed/`).
   - Uploaded files in future stages must be processed in ephemeral storage or sandboxed environments following patient privacy best practices.
