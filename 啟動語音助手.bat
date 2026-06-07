@echo off
chcp 65001 > nul
title AI Voice Assistant Launcher
cd /d "%~dp0"

echo ==========================================
echo   AI Voice Assistant (Local MiniMind-O)
echo ==========================================
echo.
echo Launching application...
echo.

if not exist ".\venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found! 
    echo Please make sure you are running this from D:\AI VOICE
    pause
    exit /b
)

".\venv\Scripts\python.exe" main.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Application exited with code: %errorlevel%
    pause
)
