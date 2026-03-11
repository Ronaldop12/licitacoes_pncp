# ✅ INSTALAÇÃO DOS PACOTES FALTANTES

# Copie e execute EXATAMENTE estes comandos no PowerShell
# (NÃO precisa de Admin, mas é recomendado)

# PASSO 1: Ativar ambiente virtual
.\venv\Scripts\Activate.ps1

# PASSO 2: Instalar streamlit
pip install streamlit==1.28.1

# PASSO 3: Instalar plotly  
pip install plotly==5.17.0

# PASSO 4: Testar
python testar_sistema.py

# PASSO 5: Se tudo OK, rodar coleta
python pncp_radar_ti_plus.py

# PASSO 6: Abrir dashboard
streamlit run dashboard.py
