param(
    [switch]$ForceSeedDemoData
)

$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot\..\backend"

$venvPython = Join-Path (Get-Location) ".venv\Scripts\python.exe"
$requirementsStamp = Join-Path (Get-Location) ".venv\.requirements-installed"

function Update-Stamp([string]$Path) {
    New-Item -ItemType File -Path $Path -Force | Out-Null
}

function Test-FileChanged([string]$ReferencePath, [string]$StampPath) {
    if (-not (Test-Path $StampPath)) {
        return $true
    }
    return (Get-Item $ReferencePath).LastWriteTimeUtc -gt (Get-Item $StampPath).LastWriteTimeUtc
}

function Test-NeedsSeedData([string]$PythonPath) {
    $seedCheckScript = @'
from app.db.session import SessionLocal
from app.models.patient import Patient

with SessionLocal() as db:
    print(db.query(Patient).count())
'@
    $result = @($seedCheckScript | & $PythonPath -)
    return [int]$result[-1] -eq 0
}

if (-not (Test-Path .venv)) {
    python -m venv .venv
}

if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
}

if (Test-FileChanged "requirements.txt" $requirementsStamp) {
    & $venvPython -m pip install -r requirements.txt
    Update-Stamp $requirementsStamp
}

& $venvPython scripts\init_db.py

if ($ForceSeedDemoData -or (Test-NeedsSeedData $venvPython)) {
    & $venvPython scripts\seed_demo_data.py
}

& $venvPython -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
