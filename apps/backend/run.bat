@echo off
REM WAVY.ai Backend Startup Script for Windows

echo Starting WAVY.ai Backend...

REM Check if .env exists
if not exist .env (
    echo .env file not found. Creating from .env.example...
    copy .env.example .env
    echo Please edit .env file with your configuration (especially OPENAI_API_KEY^)
    echo Then run this script again.
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/update dependencies
echo Installing dependencies...
pip install -r requirements.txt --quiet

REM Run the server
echo Starting server on http://localhost:8080
echo API Documentation: http://localhost:8080/docs
echo.
python -m uvicorn src.main:app --reload --port 8080
