Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

python -m streamlit run src/ai_glasses_memory/ui/streamlit_app.py `
    --server.port 8501 `
    --server.address 127.0.0.1 `
    --server.headless true
