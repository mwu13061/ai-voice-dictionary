@echo off
chcp 65001 > nul
title 語音助手備份與還原工具
cd /d "%~dp0"
if exist ".\venv\Scripts\python.exe" (
    ".\venv\Scripts\python.exe" backup_tool.py
) else (
    python backup_tool.py
)
pause
