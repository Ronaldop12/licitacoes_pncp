@echo off
REM ========================================
REM RADAR DE LICACOES TI - Dashboard
REM ========================================
REM Script para iniciar o Streamlit

cd /d %~dp0

REM Ativar ambiente virtual
echo Ativando ambiente virtual...
call venv\Scripts\activate.bat

if errorlevel 1 (
    echo Erro ao ativar ambiente virtual.
    pause
    exit /b 1
)

REM Executar dashboard
echo Iniciando dashboard Streamlit...
echo.

streamlit run dashboard.py

pause
