@echo off
REM ========================================================
REM super_ai_editor - One-Click Launcher (Windows 10 & 11)
REM ========================================================

title super_ai_editor — AI-Powered Video Studio
echo ==========================================================
echo  Starting super_ai_editor on Windows
echo ==========================================================

if "%1"=="--docker" (
    echo Launching via Docker Compose...
    docker compose up --build
    pause
    exit /b
)

echo Checking System & Memory Profile...
python -c "import sys; sys.path.insert(0, '.'); from backend.app.services.system_detector import get_hardware_profile; hw = get_hardware_profile(); print(f'   • Detected OS: {hw[\"os\"]} ({hw[\"arch\"]})'); print(f'   • System RAM: {hw[\"total_ram_gb\"]} GB'); print(f'   • Recommended Model: {hw[\"recommended_model\"]} ({hw[\"profile_name\"]})')"

curl -s http://localhost:11434/api/tags >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] Ollama is ONLINE at http://localhost:11434
) else (
    echo [INFO] Ollama is not running. (Offline AI Rule Engine is ACTIVE)
    echo        To connect live local LLM, run in another prompt:
    echo        ollama run llama3.2:3b
)

echo.
echo Launching Studio Server at http://localhost:8000 ...
start http://localhost:8000
python backend/run.py
pause
