@echo off
echo Starting Hospital AI Agent System...
echo.
echo Make sure virtual environment is activated!
echo.
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
pause

