@echo off
REM ========================================
REM RADAR DE LICACOES TI - Recovery
REM ========================================
REM Script para recuperacao de setup com problemas

setlocal enabledelayedexpansion

cls
echo.
echo ========================================
echo   RECOVERY - Limpeza e Reinstalacao
echo ========================================
echo.

REM Verificar admin
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Este script REQUER permissoes de Administrador!
    echo.
    echo Por favor:
    echo 1. Feche este prompt
    echo 2. Clique direito em recovery.bat
    echo 3. Selecione "Executar como administrador"
    echo.
    pause
    exit /b 1
)

echo [1/5] Desativando ambiente virtual...
call venv\Scripts\deactivate.bat 2>nul
timeout /t 1 /nobreak >nul

echo [2/5] Removendo ambiente virtual antigo...
rmdir /s /q venv 2>nul
if exist venv (
    echo [AVISO] Nao foi possivel remover venv completamente
    echo Tente fechar todos os programas de Python
) else (
    echo [OK] Ambiente virtual removido
)

timeout /t 2 /nobreak >nul

echo.
echo [3/5] Limpando cache do pip...
rmdir /s /q "%TEMP%\pip" 2>nul
%APPDATA%\Python\Python310\site-packages 2>nul

echo [OK] Cache do pip limpo
echo.

echo [4/5] Criando novo ambiente virtual...
python -m venv venv

if errorlevel 1 (
    echo [ERRO] Falha ao criar ambiente!
    pause
    exit /b 1
)

echo [OK] Ambiente criado
echo.

echo [5/5] Instalando dependencias...
call venv\Scripts\activate.bat
pip install --no-cache-dir -r requirements.txt

if errorlevel 1 (
    echo.
    echo [ERRO] Falha ao instalar!
    echo.
    echo Tente:
    echo 1. pip install requests
    echo 2. pip install pandas
    echo 3. pip install openpyxl
    echo 4. pip install streamlit
    echo 5. pip install plotly
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   RECOVERY CONCLUIDO!
echo ========================================
echo.
echo Agora execute:
echo   python testar_sistema.py
echo.

pause
