@echo off
chcp 65001 >nul 2>&1
echo Starting FongMi TV Web...
uvicorn main:app --host 127.0.0.1 --port 8000
pause
