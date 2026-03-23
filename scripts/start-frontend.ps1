$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot\..\frontend"

$installStamp = Join-Path (Get-Location) "node_modules\.install-stamp"

function Update-Stamp([string]$Path) {
    New-Item -ItemType File -Path $Path -Force | Out-Null
}

function Test-FileChanged([string]$ReferencePath, [string]$StampPath) {
    if (-not (Test-Path $StampPath)) {
        return $true
    }
    return (Get-Item $ReferencePath).LastWriteTimeUtc -gt (Get-Item $StampPath).LastWriteTimeUtc
}

if ((-not (Test-Path "node_modules")) -or (Test-FileChanged "package.json" $installStamp) -or (Test-FileChanged "package-lock.json" $installStamp)) {
    npm install --cache .npm-cache
    Update-Stamp $installStamp
}

if ((Test-Path ".env.example") -and (-not (Test-Path ".env"))) {
    Copy-Item .env.example .env
}

npm run dev -- --host 0.0.0.0 --port 5173
