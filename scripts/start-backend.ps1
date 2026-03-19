Set-Location "$PSScriptRoot\..\backend"

if (-not (Test-Path .venv)) {
    python -m venv .venv
}

.venv\Scripts\python -m pip install -r requirements.txt

if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
}

.venv\Scripts\python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
