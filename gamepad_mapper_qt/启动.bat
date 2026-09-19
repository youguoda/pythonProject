@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\pythonw.exe" (
    echo 找不到虚拟环境：.venv\Scripts\pythonw.exe
    echo 请先执行：
    echo   python -m venv .venv
    echo   .venv\Scripts\pip.exe install -r requirements.txt
    pause
    exit /b 1
)

start "" ".venv\Scripts\pythonw.exe" main.py
