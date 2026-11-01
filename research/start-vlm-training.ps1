param(
    [ValidateSet('Prepare','Smoke','Train','Development','Seal','Test')]
    [string]$Stage = 'Smoke'
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$workspaceRoot = Split-Path -Parent (Split-Path -Parent $projectRoot)
$pythonExe = Join-Path $workspaceRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) { throw 'Existing Python environment not found.' }
Set-Location -LiteralPath $projectRoot
function Invoke-TrainingPython {
    param([string[]]$PythonArguments)
    & $pythonExe @PythonArguments
    if ($LASTEXITCODE -ne 0) { throw "Training command failed with exit code $LASTEXITCODE. Check the preceding output." }
}
if ($Stage -eq 'Prepare') {
    Invoke-TrainingPython -PythonArguments @('-m','research.vlm_setup','all')
    exit
}
if ($Stage -eq 'Smoke') {
    Invoke-TrainingPython -PythonArguments @('-m','research.vlm_setup','run','--','-m','research.vlm_train','smoke')
    exit
}
if ($Stage -eq 'Train') {
    foreach ($trainingSeed in @('42','31415')) {
        Invoke-TrainingPython -PythonArguments @('-m','research.vlm_setup','run','--','-m','research.vlm_train','train','--seed',$trainingSeed)
    }
    exit
}
if ($Stage -eq 'Development' -or $Stage -eq 'Test') {
    $evaluationRole = if ($Stage -eq 'Test') { 'test' } else { 'development' }
    foreach ($modelChoice in @('original','seed_42','seed_31415')) {
        Invoke-TrainingPython -PythonArguments @('-m','research.vlm_setup','run','--','-m','research.vlm_train','evaluate','--role',$evaluationRole,'--model',$modelChoice)
    }
    exit
}
if ($Stage -eq 'Seal') {
    Invoke-TrainingPython -PythonArguments @('-m','research.vlm_setup','run','--','-m','research.vlm_train','seal')
}
