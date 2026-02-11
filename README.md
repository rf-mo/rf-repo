# Softchoice PM Hub

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
