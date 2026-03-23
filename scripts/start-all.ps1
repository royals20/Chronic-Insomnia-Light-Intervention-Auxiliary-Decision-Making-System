param(
    [switch]$ForceSeedDemoData
)

$ErrorActionPreference = "Stop"

$backendScript = Join-Path $PSScriptRoot "start-backend.ps1"
$frontendScript = Join-Path $PSScriptRoot "start-frontend.ps1"

function Test-PortAvailable([int]$Port) {
    $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $Port)
    try {
        $listener.Start()
        return $true
    }
    catch {
        return $false
    }
    finally {
        $listener.Stop()
    }
}

function Start-Window([string]$ScriptPath, [string[]]$Arguments) {
    $argumentList = @(
        "-NoExit",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        $ScriptPath
    ) + $Arguments

    Start-Process -FilePath "powershell.exe" -ArgumentList $argumentList | Out-Null
}

if (Test-PortAvailable 8000) {
    $backendArguments = @()
    if ($ForceSeedDemoData) {
        $backendArguments += "-ForceSeedDemoData"
    }
    Start-Window $backendScript $backendArguments
}
else {
    Write-Host "Port 8000 is already in use. Backend was not started."
}

if (Test-PortAvailable 5173) {
    Start-Window $frontendScript @()
}
else {
    Write-Host "Port 5173 is already in use. Frontend was not started."
}

Write-Host "Backend:  http://127.0.0.1:8000"
Write-Host "Frontend: http://127.0.0.1:5173"
Write-Host "Demo user: research_demo / Demo@123456"
