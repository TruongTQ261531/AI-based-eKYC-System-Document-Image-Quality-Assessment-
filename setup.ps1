$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not (Test-Path '.venv\Scripts\python.exe')) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Could not create virtual environment' }
}
& .\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed' }
& .\.venv\Scripts\python.exe -m ekyc.download_models
if ($LASTEXITCODE -ne 0) { throw 'Model download failed' }
& .\.venv\Scripts\python.exe -m ekyc.dataset
if ($LASTEXITCODE -ne 0) { throw 'Dataset reconciliation failed' }
Write-Host 'Ready. Run .\start.ps1 and open http://127.0.0.1:8000'
