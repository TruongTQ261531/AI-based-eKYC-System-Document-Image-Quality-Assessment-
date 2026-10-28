$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) {
    throw "Existing Python environment not found: $python"
}

$listener = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue |
    Select-Object -First 1
if ($listener) {
    $health = $null
    try { $health = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/health' -TimeoutSec 3 } catch {}
    if ($health.status -eq 'ready' -and $health.api_version) {
        Write-Host "eKYC is already running at http://127.0.0.1:8000 (API $($health.api_version), weights $($health.quality_checkpoint))."
        Write-Host 'Open this URL in your browser. No second server is needed.'
        return
    }
    $process = Get-CimInstance Win32_Process -Filter "ProcessId = $($listener.OwningProcess)" -ErrorAction SilentlyContinue
    $details = if ($process) { "PID $($process.ProcessId): $($process.Name)" } else { "PID $($listener.OwningProcess)" }
    throw "Port 8000 is used by $details, but the eKYC health check failed. Stop that server before trying again."
}

Write-Host 'Starting eKYC at http://127.0.0.1:8000 ... Keep this terminal open. Press Ctrl+C to stop.'
& $python -m uvicorn ekyc.api:app --host 127.0.0.1 --port 8000
if ($LASTEXITCODE -ne 0) {
    throw "Uvicorn exited with code $LASTEXITCODE. See the error above."
}
