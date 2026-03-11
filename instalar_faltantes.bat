@echo off
REM Script para instalar apenas os pacotes faltantes

echo.
echo Instalando streamlit e plotly...
echo.

call venv\Scripts\activate.bat

pip install streamlit==1.28.1 --no-cache-dir
pip install plotly==5.17.0 --no-cache-dir

echo.
echo Pacotes instalados! Agora teste:
echo   python testar_sistema.py
echo.

pause
