# Run Legal Risk Analysis dashboard from project root with rag_env

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

& "$projectRoot\rag_env\Scripts\Activate.ps1"
& "$projectRoot\rag_env\Scripts\python.exe" -m uvicorn legal_dashboard:app --host 127.0.0.1 --port 8000 --reload
