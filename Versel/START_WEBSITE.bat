@echo off
pushd "%~dp0"
echo ===================================================
echo     STARTING TRADING INSIGHTS WEB APPLICATION
echo ===================================================

echo.
echo Checking for required Python libraries...
pip install -r requirements.txt -q

echo.
echo Starting FastAPI Server...
start "" "http://localhost:8000"
cd backend
python -m uvicorn main:app --reload

pause
