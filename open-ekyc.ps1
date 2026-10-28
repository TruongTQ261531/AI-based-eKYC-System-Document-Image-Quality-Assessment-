# Start the existing local eKYC API if needed, then open it in the default browser.
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

$server = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue |
    Where-Object { $_.LocalAddress -eq '127.0.0.1' } |
    Select-Object -First 1

if (-not $server) {
    $python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $python)) {
        throw 'Existing .venv not found. Check the project directory.'
    }
    Start-Process -FilePath $python `
        -ArgumentList @('-m', 'uvicorn', 'ekyc.api:app', '--host', '127.0.0.1', '--port', '8000') `
        -WorkingDirectory $PSScriptRoot `
        -WindowStyle Hidden

    $ready = $false
    for ($attempt = 0; $attempt -lt 40; $attempt++) {
        Start-Sleep -Milliseconds 500
        $server = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue |
            Where-Object { $_.LocalAddress -eq '127.0.0.1' } |
            Select-Object -First 1
        if ($server) { $ready = $true; break }
    }
    if (-not $ready) { throw 'Server did not start. Run .\start.ps1 to see the error.' }
}

Start-Process 'http://127.0.0.1:8000/'
