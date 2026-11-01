$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$workspaceRoot = Split-Path -Parent (Split-Path -Parent $projectRoot)
$pythonExe = Join-Path $workspaceRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) { throw 'Existing Python environment not found.' }
Set-Location -LiteralPath $projectRoot
& $pythonExe -m research.vlm_setup run -- -m uvicorn research.vlm_web:app --host 127.0.0.1 --port 8002 --no-access-log
exit $LASTEXITCODE
