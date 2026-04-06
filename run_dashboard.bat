@echo off
REM Run Legal Risk Analysis dashboard from project root with rag_env

cd /d "%~dp0"
CALL rag_env\Scripts\activate.bat
rag_env\Scripts\python.exe -m uvicorn legal_dashboard:app --host 127.0.0.1 --port 8000 --reload
