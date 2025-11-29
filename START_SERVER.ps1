# Start Hospital AI Agent System
Write-Host "Starting Hospital AI Agent System..." -ForegroundColor Green
Write-Host ""
Write-Host "Make sure virtual environment is activated!" -ForegroundColor Yellow
Write-Host ""

# Activate virtual environment if not already activated
if (-not $env:VIRTUAL_ENV) {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & ".\venv\Scripts\Activate.ps1"
}

# Start the server
Write-Host "Starting server on http://localhost:8000" -ForegroundColor Green
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

