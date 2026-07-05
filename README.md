# Project Green Light

Phase 1: functional data pipeline (image in → metrics + placeholder
recommendation → permanent storage → dashboard). No AI model yet by
design — recommendation logic is deployment-specific and the client's
deployment environment isn't finalized. No login in this phase either
— single-user, offline desktop app.

## Structure

```
project-green-light/
├── app.db                  # created on first run
├── requirements.txt
├── backend/
│   ├── main.py              # FastAPI routes
│   ├── database.py          # SQLite connection + schema
│   ├── models.py             # Pydantic schemas
│   ├── rule_engine.py         # placeholder recommendation, AI seam
│   ├── utils.py               # brightness/blur (OpenCV)
│   └── uploads/                # stored images, UUID-prefixed filenames
└── frontend/
    └── app.py                   # Streamlit dashboard (REST only)
```

## Setup

Known issue: on Python 3.14, Streamlit's protobuf dependency breaks on
import (`Metaclasses with custom tp_new are not supported`). Use a
Python 3.12 or 3.13 venv instead:

```bash
python3.12 -m venv venv        # or python3.13
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run

Two processes, in separate terminals, from the project root (venv
activated in both):

```bash
# Terminal 1 — backend
uvicorn backend.main:app --reload --port 8000

# Terminal 2 — frontend
streamlit run frontend/app.py
```

Open the dashboard at http://localhost:8501 — no login required.

## What's implemented

- Image upload with collision-safe UUID filenames
- Brightness (mean grayscale intensity) + blur (Laplacian variance) via OpenCV
- Placeholder recommendation ("Improvement Requested") for every image
- Permanent storage in SQLite, full history view, manual deletion
- Clean seam (`rule_engine.py`) to swap in a trained model later without
  touching `main.py` or the frontend

## What's intentionally not implemented yet

- Login/auth — dropped for this phase; add back as its own module if
  this ever needs to run multi-user or networked
- Recommendation rules, labeled dataset, IoT/camera integration,
  video/text input, model training — all wait on deployment-environment
  decisions the client hasn't finalized yet
