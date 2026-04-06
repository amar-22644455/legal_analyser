# ============================================================
# RAG Application Command File (PowerShell)
# ============================================================
# This file contains commands to run the RAG application

# ============================================================
# 1. ACTIVATE VIRTUAL ENVIRONMENT
# ============================================================
# Run this command first to activate the virtual environment:
# & .\rag_env\Scripts\Activate.ps1

# ============================================================
# 2. RUN LEGAL DASHBOARD WEB APPLICATION
# ============================================================
# To start the dashboard application, use:
# python -m uvicorn legal_dashboard:app --reload --host 127.0.0.1 --port 8000

# ============================================================
# 3. RUN CLI APPLICATION
# ============================================================
# To run the CLI version, use:
# python main.py
# or
# python cli.py

# ============================================================
# 4. RUN VITE REACT UI (DEVELOPMENT)
# ============================================================
# cd .\ui
# npm install
# npm run dev

# ============================================================
# 5. BUILD VITE PRODUCTION BUNDLE
# ============================================================
# cd .\ui
# npm run build

# ============================================================
# Example usage:
# ============================================================
# Option A: Run Legal Dashboard (Web UI)
#   1. Open PowerShell
#   2. Navigate to project directory: cd d:\RAG
#   3. Activate environment: & .\rag_env\Scripts\Activate.ps1
#   4. Run: python -m uvicorn legal_dashboard:app --reload --host 127.0.0.1 --port 8000

# Option B: Run CLI App (Command Line)
#   1. Open PowerShell
#   2. Navigate to project directory: cd d:\RAG
#   3. Activate environment: & .\rag_env\Scripts\Activate.ps1
#   4. Run: python main.py

# ============================================================
# Quick Start Script (uncomment to use):
# ============================================================
# Uncomment the lines below to auto-run the dashboard app:

# & .\rag_env\Scripts\Activate.ps1
# python -m uvicorn legal_dashboard:app --reload --host 127.0.0.1 --port 8000
