@echo off
REM Quick setup script for BARC RAG system on Windows

echo.
echo 🚀 BARC RAG System - Quick Setup
echo ================================
echo.

REM Check Docker
echo ✓ Checking Docker installation...
where docker >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ✗ Docker not found. Please install Docker Desktop first.
    pause
    exit /b 1
)
where docker-compose >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ✗ Docker Compose not found. Please install Docker Desktop first.
    pause
    exit /b 1
)
echo ✓ Docker OK
echo.

REM Check Python
echo ✓ Checking Python installation...
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ✗ Python not found. Please install Python 3.9+ first.
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✓ Python %PYTHON_VERSION% OK
echo.

REM Install dependencies
echo 📦 Installing Python dependencies...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo ✗ Failed to install dependencies
    pause
    exit /b 1
)
echo ✓ Dependencies installed
echo.

REM Start Docker services
echo 🐳 Starting Docker services...
docker-compose up -d
if %ERRORLEVEL% NEQ 0 (
    echo ✗ Failed to start Docker services
    pause
    exit /b 1
)
echo ✓ Docker services started
echo   - Qdrant: http://localhost:6333
echo   - PostgreSQL: localhost:5432
echo.

REM Wait for services
echo ⏳ Waiting for services to be ready (15 seconds)...
timeout /t 15 /nobreak
echo ✓ Services ready
echo.

echo ✅ Setup complete!
echo.
echo Next steps:
echo 1. Edit .env file with your xAI API key
echo 2. Place documents in the ./documents folder
echo 3. Run: streamlit run app/main.py
echo.
pause
