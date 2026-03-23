param(
    [switch]$ForceSeedDemoData
)

$ErrorActionPreference = "Stop"

$arguments = @()
if ($ForceSeedDemoData) {
    $arguments += "-ForceSeedDemoData"
}

& "$PSScriptRoot\scripts\start-all.ps1" @arguments
