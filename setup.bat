@echo off
REM ========================================
REM RADAR DE LICACOES TI - Setup Wizard
REM ========================================
REM Script de configuracao inicial

setlocal enabledelayedexpansion

cls
echo.
echo ========================================
echo   RADAR DE LICACOES DE TI
echo   Setup Wizard v1.0
echo ========================================
echo.

REM Verificar se esta rodando como admin
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [AVISO] Este script funciona melhor como Administrador
    echo.
    echo Para rodar como admin:
    echo 1. Clique com botao direito em setup.bat
    echo 2. Selecione "Executar como administrador"
    echo.
    echo Continuando mesmo assim...
    echo.
    timeout /t 3
)

REM Verificar Python
echo [1/4] Verificando Python...
python --version >nul 2>&1

if errorlevel 1 (
    echo.
    echo [ERRO] Python nao encontrado!
    echo.
    echo Baixe em: https://www.python.org/downloads/
    echo Certifique-se de marcar "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Python %PYTHON_VERSION% encontrado
echo.

REM Criar ambiente virtual
echo [2/4] Criando ambiente virtual...
if not exist venv (
    python -m venv venv
    echo [OK] Ambiente virtual criado
) else (
    echo [OK] Ambiente virtual ja existe
)
echo.

REM Ativar ambiente virtual
echo [3/4] Ativando ambiente virtual...
call venv\Scripts\activate.bat
echo [OK] Ambiente virtual ativado
echo.

REM Instalar dependencias
echo [4/4] Instalando dependencias...
echo Isso pode levar alguns minutos...
echo.

REM Nao tentar atualizar pip (evita erro de permissao)
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [AVISO] Houve um erro ao instalar dependencias
    echo.
    echo Tentando novamente sem quiet mode...
    pip install -r requirements.txt
    
    if errorlevel 1 (
        echo.
        echo [ERRO] Falha ao instalar dependencias!
        echo.
        echo Solucoes:
        echo 1. Feche este prompt
        echo 2. Clique direito em setup.bat
        echo 3. Selecione "Executar como administrador"
        echo.
        pause
        exit /b 1
    )
)

echo.
echo [OK] Dependencias instaladas com sucesso
echo.

REM Criar diretorio de dados
if not exist dados (
    mkdir dados
    echo [OK] Diretorio 'dados' criado
)
echo.

REM Resumo
cls
echo.
echo ========================================
echo   SETUP CONCLUIDO COM SUCESSO!
echo ========================================
echo.
echo Principais arquivos:
echo - pncp_radar_ti_plus.py  (Script de coleta)
echo - dashboard.py           (Dashboard web)
echo - requirements.txt       (Dependencias)
echo.
echo Proximos passos:
echo.
echo 1. COLETA DE DADOS (primeira vez)
echo    Clique duplo em: executar_coleta.bat
echo    ou execute no PowerShell:
echo    python pncp_radar_ti_plus.py
echo.
echo 2. VISUALIZAR DASHBOARD
echo    Clique duplo em: iniciar_dashboard.bat
echo    ou execute no PowerShell:
echo    streamlit run dashboard.py
echo.
echo 3. AUTOMATIZAR (opcional)
echo    Leia os passos em: INSTRUCOES.md
echo.
echo ========================================
echo.

pause
