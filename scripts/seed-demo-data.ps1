Set-Location "$PSScriptRoot\..\backend"

if (-not (Test-Path .venv)) {
    python -m venv .venv
}

.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python scripts\seed_demo_data.py
