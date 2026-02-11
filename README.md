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
A lightweight personal project management tool with:
- FastAPI backend (`uvicorn`) on port `8000`
- React + Vite frontend on port `5173`

## Prerequisites (Windows)
- Python **3.11+**
- Node.js **18+**

## First-time setup
From the repository root, run either:

```powershell
.\setup.ps1
```

or:

```powershell
npm run setup
```

This will:
1. Create `.venv` (if missing)
2. Install backend Python dependencies from `backend/requirements.txt`
3. Install root npm dependencies (for `concurrently`)
4. Install frontend npm dependencies

## Daily run (one command)
From the repository root:

```powershell
npm run dev
```

This starts both services in parallel:
- Backend: `uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000`
- Frontend: `vite` on port `5173`

## Optional PowerShell shortcut
You can also use:

```powershell
.\dev.ps1
```

`dev.ps1` checks for `.venv` and runs setup automatically if needed, then runs `npm run dev`.

## Troubleshooting
- If backend startup fails because the Uvicorn import target is different, update the backend script in root `package.json`:
  - Current target: `backend.main:app`
  - Example alternate target: `main:app` or `src.main:app`
