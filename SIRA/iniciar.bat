@echo off
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  echo Python nao encontrado. Instale Python 3.10 ou superior.
  pause
  exit /b 1
)
if not exist .venv py -3 -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python database.py
start "SIRA Backend" cmd /k "cd /d ""%~dp0"" && ""%~dp0.venv\Scripts\python.exe"" ""%~dp0backend.py"""
timeout /t 2 /nobreak >nul
python -m streamlit run frontend.py
