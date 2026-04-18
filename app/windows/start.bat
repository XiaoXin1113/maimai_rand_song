@echo off
chcp 65001 >nul
cd /d "%~dp0..\.."
python app\windows\maimai_app.py
pause
