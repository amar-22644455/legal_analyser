@echo off
REM ============================================================
REM RAG Application Command File
REM ============================================================
REM This file contains commands to run the RAG application

REM ============================================================
REM 1. ACTIVATE VIRTUAL ENVIRONMENT
REM ============================================================
REM Run this command first to activate the virtual environment:
CALL rag_env\Scripts\activate.bat

REM ============================================================
REM 2. RUN LEGAL DASHBOARD WEB APPLICATION
REM ============================================================
REM To start the dashboard application, use:
REM python -m uvicorn legal_dashboard:app --reload --host 127.0.0.1 --port 8000

REM ============================================================
REM 3. RUN CLI APPLICATION
REM ============================================================
REM To run the CLI version, use:
REM python main.py
REM or
REM python cli.py

REM ============================================================
REM 4. RUN VITE REACT UI (DEVELOPMENT)
REM ============================================================
REM cd ui
REM npm install
REM npm run dev

REM ============================================================
REM 5. BUILD VITE PRODUCTION BUNDLE
REM ============================================================
REM cd ui
REM npm run build

REM ============================================================
REM Example usage:
REM ============================================================
REM Option A: Run Legal Dashboard (Web UI)
REM   1. Open Command Prompt
REM   2. Navigate to project directory: cd d:\RAG
REM   3. Activate environment: rag_env\Scripts\activate.bat
REM   4. Run: python -m uvicorn legal_dashboard:app --reload --host 127.0.0.1 --port 8000

REM Option B: Run CLI App (Command Line)
REM   1. Open Command Prompt
REM   2. Navigate to project directory: cd d:\RAG
REM   3. Activate environment: rag_env\Scripts\activate.bat
REM   4. Run: python main.py

REM ============================================================
REM Quick Start Script (uncomment to use):
REM ============================================================
REM Uncomment the lines below to auto-run the dashboard app:

REM CALL rag_env\Scripts\activate.bat
REM python -m uvicorn legal_dashboard:app --reload --host 127.0.0.1 --port 8000
