$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$workspaceRoot = Split-Path -Parent (Split-Path -Parent $projectRoot)
$pythonExe = Join-Path $workspaceRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) { throw 'Existing Python environment not found.' }
Set-Location -LiteralPath $projectRoot
$existingServer = $null
try { $existingServer = Invoke-RestMethod -Uri 'http://127.0.0.1:8002/api/health' -TimeoutSec 2 } catch { }
if ($existingServer -and $existingServer.app_id -eq 'vlm_lora_research_v1') {
    Write-Host 'Vintern LoRA web is already running: http://127.0.0.1:8002/'
    exit 0
}
Write-Host 'Starting Vintern LoRA web: http://127.0.0.1:8002/ . Press Ctrl+C to stop.'
& $pythonExe -m research.vlm_setup run -- -m uvicorn research.vlm_web:app --host 127.0.0.1 --port 8002 --no-access-log
exit $LASTEXITCODE
