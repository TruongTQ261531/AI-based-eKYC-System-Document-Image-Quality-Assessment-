param([int]$Port = 8005)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$ekycPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $ekycPython)) { throw 'Existing Python environment was not found.' }
Write-Host ('OCR annotation review: http://127.0.0.1:' + $Port + '/')
& $ekycPython -m uvicorn research.labels_web:app --host 127.0.0.1 --port $Port --no-access-log
exit $LASTEXITCODE
