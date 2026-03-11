@echo off
REM ========================================
REM RADAR DE LICITACOES TI - Executor
REM ========================================
REM Script para executar a coleta de dados

cd /d %~dp0

REM Ativar ambiente virtual
echo Ativando ambiente virtual...
call venv\Scripts\activate.bat

if errorlevel 1 (
    echo Ambiente virtual nao encontrado.
    echo Criando novo ambiente virtual...
    python -m venv venv
    call venv\Scripts\activate.bat
)

REM Instalar dependencias se necessario
echo Verificando dependencias...
pip install -q -r requirements.txt

REM Executar script
echo.
echo ========================================
echo INICIANDO COLETA DE LICACOES DE TI
echo ========================================
echo.

python pncp_radar_ti_plus.py

echo.
echo ========================================
echo COLETA FINALIZADA
echo ========================================
echo.

pause
