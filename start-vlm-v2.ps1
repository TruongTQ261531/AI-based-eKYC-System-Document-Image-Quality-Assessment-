param([ValidateRange(1024,65535)][int]$Port = 8003)
$ErrorActionPreference = 'Stop'
$researchRoot = $PSScriptRoot
$url = 'http://127.0.0.1:' + $Port + '/'
$probe = [System.Net.Sockets.TcpClient]::new()
$occupied = $false
try { $occupied = $probe.ConnectAsync('127.0.0.1',$Port).Wait(500) -and $probe.Connected } catch {} finally { $probe.Dispose() }
if ($occupied) {
    $service = $null
    try { $service = Invoke-RestMethod -Uri ($url + 'api/health') -TimeoutSec 3 } catch {}
    if ($service.app_id -eq 'vlm_lora_research_v2') {
        Write-Host ('V2 OCR is already running at ' + $url)
        return
    }
    throw ('Port ' + $Port + ' belongs to another service. Use a different -Port or stop the intended old service first.')
}
$workspaceRoot = [System.IO.Path]::GetFullPath((Join-Path $researchRoot '..\..'))
$existingPython = Join-Path $researchRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $existingPython)) { $existingPython = Join-Path $workspaceRoot '.venv\Scripts\python.exe' }
if (-not (Test-Path -LiteralPath $existingPython)) {
    throw 'Existing Python environment not found. This launcher does not create or install one.'
}
Set-Location -LiteralPath $researchRoot
Write-Host ('Open ' + $url + ' in your browser. Press Ctrl+C to stop.')
& $existingPython -m research.vlm_setup run -- -m uvicorn research.v2_web:app --host 127.0.0.1 --port $Port --no-access-log
if ($LASTEXITCODE -ne 0) { throw ('V2 web exited with code ' + $LASTEXITCODE) }
