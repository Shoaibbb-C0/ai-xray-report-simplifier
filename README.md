# AI X-Ray Project

> A patient-support diagnostic radiograph platform powered by dedicated in-house PyTorch machine learning models.

---

## 1. Project Purpose
The **AI X-Ray Project** is an academic mini-project engineered to empower patients with transparent, understandable, and reassurance-focused explanations of their X-ray radiographs. 

Unlike conventional diagnostic tools built solely for radiologists, this platform translates medical imaging into clear visual representations and accessible explanations—helping patients prepare for clinical consultations and comprehend their imaging history.

---

## 2. Locked Core Features

### Feature 1: Smart X-Ray Analysis
- **Intake & Validation**: User uploads an image; system validates whether it is an interpretable radiograph.
- **Anatomical Routing**: Automatically classifies the body region (e.g., Chest, Musculoskeletal).
- **In-House Model Inference**: Evaluates the image using our dedicated trained PyTorch model.
- **Patient-Friendly Explanation**: Pairs findings with intuitive illustrations and simple, non-jargon explanations alongside the original radiograph.

### Feature 2: My X-Ray Map
- **Interactive Anatomical Map**: Visual representation of the human body acting as a spatial health record.
- **Region History**: Clicking an anatomical region displays historical scans, chronological dates, past findings, and educational visuals.
- **Longitudinal Tracking**: Prepares patients for comparisons over time.

*(Note: In Stage 1, only the foundational architecture is established. Feature workflows will be implemented in subsequent stages.)*

---

## 3. Technology Stack

- **Frontend**: Next.js (App Router), JavaScript (ES6+), Tailwind CSS
- **Backend**: Python 3.14, FastAPI, Uvicorn, Pydantic
- **Machine Learning**: PyTorch, Torchvision, NumPy, Pillow
- **Testing**: Pytest, HTTPX TestClient

---

## 4. ML Core Principle: In-House Models Only

- **Strictly No Third-Party AI APIs**: No OpenAI, Anthropic Claude, Google Gemini, or Hugging Face hosted inference endpoints are used for radiograph analysis.
- **Own Trained Models**: All neural networks are built, trained, and benchmarked using PyTorch on public medical research datasets (e.g. NIH ChestX-ray14, CheXpert, MURA).
- **Conservative Scoring**: Models use calibrated decision thresholds; inconclusive scans are explicitly marked as such to avoid misleading speculation.

---

## 5. Repository Structure

```
ai-xray-project/
├── frontend/                     # Next.js frontend (JavaScript + Tailwind CSS)
│   ├── app/                      # App router (layout.js, page.js, globals.css)
│   ├── package.json              # Minimal frontend dependencies
│   ├── tailwind.config.js        # Minimalist modern medical styling
│   └── .env.example              # Frontend environment variables template
│
├── backend/                      # Python FastAPI backend
│   ├── app/
│   │   ├── api/                  # API routers (v1 health and status routes)
│   │   ├── core/                 # Configuration and environment settings
│   │   ├── services/             # Service layer & placeholder ML engine
│   │   └── main.py               # FastAPI entry point
│   ├── requirements.txt          # Backend-specific Python dependencies
│   └── .env.example              # Backend environment variables template
│
├── ml/                           # In-house machine learning pipeline
│   ├── datasets/                 # Manifests & dataset loader documentation
│   ├── preprocessing/            # Image resizing, letterboxing, normalization
│   ├── training/                 # PyTorch model architectures & training loops
│   ├── evaluation/               # Clinical benchmarking (ROC-AUC, calibration)
│   ├── inference/                # Runtime model loading & evaluation
│   ├── saved_models/             # Checkpoint storage (.pth files ignored in git)
│   ├── learning/                 # Preserved early learning experiments
│   ├── config.py                 # Central ML configuration & thresholds
│   └── README.md
│
├── assets/
│   ├── anatomy/                  # Anatomical artwork for My X-Ray Map
│   └── illustrations/            # Visual explanations for abnormalities
│
├── docs/                         # In-depth architectural & safety documentation
│   ├── architecture.md
│   ├── ml-principles.md
│   ├── medical-boundary.md
│   └── roadmap.md
│
├── tests/                        # Backend and integration test suites
│   ├── __init__.py
│   └── test_health.py
│
├── .gitignore                    # Robust gitignore (venv, node_modules, models, data)
├── requirements.txt              # Unified Python requirements
└── README.md                     # Root project documentation
```

---

## 6. Medical Safety Boundary & Privacy

- **Educational Support Only**: This platform is an educational and communication-aid tool, not a medical diagnosis device.
- **Clinical Oversight**: The system explicitly does not replace radiologists or medical practitioners.
- **Language Standard**: Findings are phrased as *possible findings* and *AI-assisted screening indicators*.
- **Data Privacy**: No patient personal data (PHI) or private medical images may ever be committed to the repository. Datasets and user uploads must be kept separate from source code.

---

## 7. Development Setup

### Prerequisites
- Python 3.10+ (Current environment: Python 3.14)
- Node.js 18+ (Current environment: Node.js 24)

### Backend Setup
```powershell
# Activate Python virtual environment
.\.venv\Scripts\Activate.ps1

# Install backend & ML dependencies
pip install -r requirements.txt

# Run backend API server
uvicorn backend.app.main:app --reload --port 8000
```
Verify the API:
```powershell
curl http://localhost:8000/health
```

### Frontend Setup
```powershell
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

### Running Tests
```powershell
# Execute backend test suite
pytest -v
```

---

## 8. Current Stage & Roadmap
 
| Stage | Description | Status |
| :--- | :--- | :--- |
| **Stage 1** | **Repository Foundation & Starter Shell** | **Completed** |
| **Stage 2** | **Public Dataset Curation & Preprocessing Pipeline** | **Completed** |
| **Stage 3** | **X-Ray Validator & Body-Part Classifier PyTorch Models** | **Completed** |
| **Stage 4** | **Abnormality Detection & Specialized Model (Fracture Classifier)** | **Completed (71% Target)** |
| **Stage 5** | **Visual Explanation Engine & Patient-Safe Interface** | **Completed (79% Target)** |
| **Stage 6** | **Database & Persistence Layer (Supabase)** | Planned |



