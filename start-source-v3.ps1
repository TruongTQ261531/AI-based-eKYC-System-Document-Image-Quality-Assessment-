$ErrorActionPreference = 'Stop'
$researchRoot = $PSScriptRoot
$workspaceRoot = [System.IO.Path]::GetFullPath((Join-Path $researchRoot '..\..'))
$existingPython = Join-Path $workspaceRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $existingPython)) {
    throw 'Existing Python environment not found. No environment will be created or installed.'
}
Set-Location -LiteralPath $researchRoot
Write-Host 'Open http://127.0.0.1:8003/ in your browser. Press Ctrl+C to stop.'
& $existingPython -m research.vlm_setup run -- -m uvicorn research.v3_web:app --host 127.0.0.1 --port 8003 --no-access-log
if ($LASTEXITCODE -ne 0) { throw ('Source OCR web exited with code ' + $LASTEXITCODE) }
