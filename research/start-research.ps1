$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot
Set-Location $projectRoot
$candidates = @((Join-Path $projectRoot '.venv\Scripts\python.exe'), (Join-Path $PSScriptRoot '..\..\..\.venv\Scripts\python.exe'))
$researchPython = $null
foreach ($candidate in $candidates) { if (Test-Path -LiteralPath $candidate) { $researchPython = (Resolve-Path -LiteralPath $candidate).Path; break } }
if (-not $researchPython) { throw 'Existing Python environment not found. No new environment was created.' }
$listener = Get-NetTCPConnection -LocalPort 8001 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
if ($listener) {
    $health = $null
    try { $health = Invoke-RestMethod -Uri 'http://127.0.0.1:8001/api/health' -TimeoutSec 3 } catch {}
    if ($health.app_id -eq 'research_recovery_v4') { Write-Host 'Research web is already running: http://127.0.0.1:8001'; return }
    throw 'Port8001 is used by another application. No process was stopped.'
}
Write-Host 'Research web: http://127.0.0.1:8001 . Keep this terminal open. Ctrl+C stops it.'
& $researchPython -m uvicorn research.recovery_web:app --host 127.0.0.1 --port 8001 --no-access-log
if ($LASTEXITCODE -ne 0) { throw "Research server exited with code $LASTEXITCODE" }
