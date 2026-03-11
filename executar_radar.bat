@echo off
REM ============================================================================
REM SCRIPT DE EXECUÇÃO DO RADAR DE LICITAÇÕES DE TI
REM Executa automaticamente a coleta de dados do PNCP
REM ============================================================================

setlocal enabledelayedexpansion

REM Definir diretório do projeto
set PROJETO_DIR=%~dp0
cd /d "%PROJETO_DIR%"

REM Log
set LOG_FILE=%PROJETO_DIR%logs\execucao_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%.log

REM Criar diretório de logs se não existir
if not exist "%PROJETO_DIR%logs" mkdir "%PROJETO_DIR%logs"

echo. >> "%LOG_FILE%"
echo ============================================================================ >> "%LOG_FILE%"
echo EXECUÇÃO DO RADAR DE LICITAÇÕES DE TI >> "%LOG_FILE%"
echo Data e Hora: %date% %time% >> "%LOG_FILE%"
echo ============================================================================ >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

REM Ativar ambiente virtual
echo Ativando ambiente virtual... >> "%LOG_FILE%"
if exist "%PROJETO_DIR%venv\Scripts\activate.bat" (
    call "%PROJETO_DIR%venv\Scripts\activate.bat"
    echo ✓ Ambiente virtual ativado >> "%LOG_FILE%"
) else (
    echo ✗ Ambiente virtual não encontrado! >> "%LOG_FILE%"
    exit /b 1
)

REM Executar coleta de dados
echo. >> "%LOG_FILE%"
echo Iniciando coleta de dados... >> "%LOG_FILE%"
python "%PROJETO_DIR%pncp_radar_ti_plus.py" >> "%LOG_FILE%" 2>&1

if %ERRORLEVEL% equ 0 (
    echo. >> "%LOG_FILE%"
    echo ✓ EXECUÇÃO CONCLUÍDA COM SUCESSO >> "%LOG_FILE%"
    echo. >> "%LOG_FILE%"
) else (
    echo. >> "%LOG_FILE%"
    echo ✗ ERRO NA EXECUÇÃO (Código: %ERRORLEVEL%) >> "%LOG_FILE%"
    echo. >> "%LOG_FILE%"
)

echo Finalizado: %date% %time% >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

endlocal
