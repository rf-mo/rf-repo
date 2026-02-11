# Local-First Worklog App

Offline-first web app to capture daily work in seconds and auto-generate weekly/monthly updates for Teams, email, and slide bullets.

## Stack
- Backend: FastAPI + SQLModel + SQLite
- Frontend: React + TypeScript + Vite
- Export: Markdown, CSV, and server-side PDF (ReportLab)

## Features implemented
- One-screen daily mode (Home) with quick capture, chips, account/deal selection, duration shortcuts, Ctrl+Enter save
- Auto-suggestions: play, tags, intention bucket (A/B/C/D), outcomes, follow-up extraction
- Today-at-a-glance and due-this-week panel
- One-click generation buttons:
  - Generate Weekly Update (Teams + Email + Slides generated together, copied, and snapshot saved)
  - Generate Monthly Summary (same pattern)
  - Generate Slide Bullets
- Minimal additional pages: Deals, Search, Reports, Settings
- Exports:
  - Weekly/monthly Markdown + PDF
  - CSV for entries/deals/assets
- Seed data including cadence routines and sample entries across intention buckets/cadence context

## Run locally

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Open: http://localhost:5173

## Initialize DB / seed data
- Frontend calls `POST /api/init` on startup.
- Or run manually:
```bash
curl -X POST http://localhost:8000/api/init
```

SQLite DB file is stored at `backend/worklog.db`.

## Tests
```bash
cd backend
pytest
```

## Build frontend
```bash
cd frontend
npm run build
```
