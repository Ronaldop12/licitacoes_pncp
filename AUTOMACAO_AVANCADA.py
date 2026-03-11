"""
======================================
AUTOMACAO AVANCADA
======================================
Configuracoes avancadas para producao
"""

# ==================== OPCAO 1: EMAIL COM ALERTAS ====================

"""
Criar arquivo: enviar_alertas.py

Este script envia um email quando novas licitacoes sao encontradas.

Requer:
- pip install python-dotenv

Crie arquivo .env:
SMTP_SERVER = smtp.gmail.com
SMTP_PORT = 587
EMAIL_USUARIO = seu.email@gmail.com
EMAIL_SENHA = sua_senha_app (nao a senha normal)
EMAIL_PARA = destinatario@email.com
"""

"""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

def enviar_alerta(total_novas, top_licitacoes):
    sender_email = os.getenv("EMAIL_USUARIO")
    senha = os.getenv("EMAIL_SENHA")
    destinatario = os.getenv("EMAIL_PARA")
    
    # Criar mensagem
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = destinatario
    msg["Subject"] = f"[ALERTA] {total_novas} novas licitacoes de TI!"
    
    # Corpo
    corpo = f"""
    Ola,
    
    Foram encontradas {total_novas} novas licitacoes de TI.
    
    Top 5 Oportunidades:
    
    {chr(10).join(top_licitacoes)}
    
    Acesse o dashboard para mais detalhes:
    http://localhost:8501
    
    Atencao: Nao responda este email.
    """
    
    msg.attach(MIMEText(corpo, "plain"))
    
    # Enviar
    try:
        server = smtplib.SMTP(os.getenv("SMTP_SERVER"), int(os.getenv("SMTP_PORT")))
        server.starttls()
        server.login(sender_email, senha)
        server.send_message(msg)
        server.quit()
        print("Email enviado com sucesso!")
    except Exception as e:
        print(f"Erro ao enviar email: {e}")
"""


# ==================== OPCAO 2: NOTIFICACAO NO TELEGRAM ====================

"""
Enviar alertas via Telegram

Requer:
- pip install python-telegram-bot

Crie:
1. Bot no Telegram: @BotFather
2. Obtenha o TOKEN
3. Envie /start para o bot
4. Obtenha seu CHAT_ID usando: https://api.telegram.org/bot<TOKEN>/getUpdates
"""

"""
import requests

def notificar_telegram(token, chat_id, mensagem):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": mensagem,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print(f"Mensagem enviada para Telegram!")
        else:
            print(f"Erro ao enviar: {response.status_code}")
    except Exception as e:
        print(f"Erro de conexao Telegram: {e}")

# Uso:
# notificar_telegram(TOKEN, CHAT_ID, "🚨 Nova licacao de TI encontrada!")
"""


# ==================== OPCAO 3: BACKUP AUTOMATICO ====================

"""
Fazer backup automatico dos dados

Requer:
- pip install schedule

Crie: backup_automatico.py
"""

"""
import shutil
import os
from datetime import datetime
import schedule
import time

def fazer_backup():
    # Data
    data_backup = datetime.now().strftime("%Y%m%d_%H%M%S")
    pasta_backup = f"backups/backup_{data_backup}"
    
    # Criar pasta de backup
    os.makedirs(pasta_backup, exist_ok=True)
    
    # Copiar arquivos
    arquivos = [
        "radar_licitacoes_TI_PRO.xlsx",
        "dados/licitacoes.csv",
        "radar_state.json"
    ]
    
    for arquivo in arquivos:
        if os.path.exists(arquivo):
            destino = os.path.join(pasta_backup, os.path.basename(arquivo))
            shutil.copy2(arquivo, destino)
            print(f"Backup: {arquivo}")
    
    print(f"Backup concluido em: {pasta_backup}")

# Agendar
schedule.every().day.at("22:00").do(fazer_backup)

while True:
    schedule.run_pending()
    time.sleep(60)
"""


# ==================== OPCAO 4: INTEGRACAO COM BANCO DE DADOS ====================

"""
Armazenar historico em SQLite

Requer:
- pip install sqlite3 (ja vem com Python)
"""

"""
import sqlite3
from datetime import datetime

def criar_banco_dados():
    conn = sqlite3.connect("licitacoes.db")
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS licitacoes (
            id INTEGER PRIMARY KEY,
            numero_edital TEXT UNIQUE,
            orgao TEXT,
            objeto TEXT,
            valor REAL,
            data_publicacao DATE,
            uf TEXT,
            municipio TEXT,
            data_captura DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    return conn

def inserir_licitacao(conn, licitacao):
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO licitacoes 
            (numero_edital, orgao, objeto, valor, data_publicacao, uf, municipio)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            licitacao['numero_edital'],
            licitacao['orgao'],
            licitacao['objeto'],
            licitacao['valor_estimado'],
            licitacao['data_publicacao'],
            licitacao['uf'],
            licitacao['municipio']
        ))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Duplicata

def consultar_historico(conn, uf=None):
    cursor = conn.cursor()
    if uf:
        cursor.execute('SELECT * FROM licitacoes WHERE uf=? ORDER BY data_publicacao DESC', (uf,))
    else:
        cursor.execute('SELECT * FROM licitacoes ORDER BY data_publicacao DESC')
    return cursor.fetchall()
"""


# ==================== OPCAO 5: RELATORIO MENSAL ====================

"""
Gerar relatorio mensal automatico

Requer:
- pip install reportlab
"""

"""
from datetime import datetime, timedelta
import pandas as pd

def gerar_relatorio_mensal():
    # Carregar CSV
    df = pd.read_csv("dados/licitacoes.csv")
    df['data_publicacao'] = pd.to_datetime(df['data_publicacao'])
    
    # Filtrar mes atual
    agora = datetime.now()
    mes_inicio = agora.replace(day=1)
    mes_fim = (mes_inicio + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    df_mes = df[(df['data_publicacao'] >= mes_inicio) & 
                (df['data_publicacao'] <= mes_fim)]
    
    # Calcular KPIs
    relatorio = {
        "Periodo": f"{mes_inicio.strftime('%m/%Y')}",
        "Total de Licacoes": len(df_mes),
        "Total de Orgaos": df_mes['orgao'].nunique(),
        "Valor Total (R$)": df_mes['valor_estimado'].sum(),
        "Valor Medio (R$)": df_mes['valor_estimado'].mean(),
        "Estado com Mais Licacoes": df_mes['uf'].value_counts().index[0] if len(df_mes) > 0 else "N/A",
        "Orgao Top": df_mes['orgao'].value_counts().index[0] if len(df_mes) > 0 else "N/A",
    }
    
    # Salvar relatorio
    nome_arquivo = f"relatorios/relatorio_{mes_inicio.strftime('%Y%m')}.txt"
    os.makedirs("relatorios", exist_ok=True)
    
    with open(nome_arquivo, 'w', encoding='utf-8') as f:
        f.write("="*60 + "\n")
        f.write("RELATORIO MENSAL - LICACOES DE TI\n")
        f.write("="*60 + "\n\n")
        
        for chave, valor in relatorio.items():
            f.write(f"{chave}: {valor}\n")
    
    print(f"Relatorio gerado: {nome_arquivo}")

# Agendar (ex: dia 1 de cada mes)
# schedule.every().month.do(gerar_relatorio_mensal)
"""


# ==================== OPCAO 6: ANALISE DE TENDENCIAS ====================

"""
Analisar tendencias de mercado

Requer:
- pip install scipy numpy
"""

"""
import numpy as np
from scipy.stats import linregress
import pandas as pd

def analisar_tendencia_valor():
    df = pd.read_csv("dados/licitacoes.csv")
    df['data_publicacao'] = pd.to_datetime(df['data_publicacao'])
    
    # Agrupar por data
    valores_diarios = df.groupby(df['data_publicacao'].dt.date)['valor_estimado'].sum()
    
    # Calcular tendencia
    x = np.arange(len(valores_diarios))
    y = valores_diarios.values
    
    slope, intercept, r_value, p_value, std_err = linregress(x, y)
    
    if slope > 0:
        print(f"📈 Tendencia: ALTA (crescimento de {slope:.0f} R$/dia)")
    elif slope < 0:
        print(f"📉 Tendencia: BAIXA (reducao de {abs(slope):.0f} R$/dia)")
    else:
        print(f"➡️  Tendencia: ESTAVEL")
    
    print(f"Confianca: {r_value**2 * 100:.1f}%")
"""


# ==================== OPCAO 7: VALIDACAO DE DADOS ====================

"""
Validar qualidade dos dados coletados
"""

"""
import pandas as pd
from datetime import datetime

def validar_dados():
    df = pd.read_csv("dados/licitacoes.csv")
    
    print("VALIDACAO DE DADOS")
    print("="*50)
    
    # Verificar valores ausentes
    print("\n1. Dados ausentes:")
    print(df.isnull().sum())
    
    # Verificar duplicatas
    duplicatas = len(df) - len(df.drop_duplicates(subset=['numero_edital']))
    print(f"\n2. Duplicatas encontradas: {duplicatas}")
    
    # Verificar formats de valor
    df['valor_estimado'] = pd.to_numeric(df['valor_estimado'], errors='coerce')
    valores_invalidos = df['valor_estimado'].isnull().sum()
    print(f"\n3. Valores invalidos: {valores_invalidos}")
    
    # Verificar datas
    df['data_publicacao'] = pd.to_datetime(df['data_publicacao'], errors='coerce')
    datas_invalidas = df['data_publicacao'].isnull().sum()
    print(f"\n4. Datas invalidas: {datas_invalidas}")
    
    # Estatisticas
    print(f"\n5. Estatisticas:")
    print(f"   Total de registros: {len(df)}")
    print(f"   Valor minimo: R$ {df['valor_estimado'].min():,.2f}")
    print(f"   Valor maximo: R$ {df['valor_estimado'].max():,.2f}")
    print(f"   Valor medio: R$ {df['valor_estimado'].mean():,.2f}")
    
    print("\n" + "="*50)
    if valor_invalidos == 0 and datas_invalidas == 0:
        print("✓ DADOS VALIDADOS COM SUCESSO")
    else:
        print("⚠ VERIFICAR DADOS COM PROBLEMAS")
"""


# ==================== RESUMO DAS OPCOES DE AUTOMACAO ====================

"""
GRADE DE OPCOES:

┌─────────────────────┬──────┬─────────┬──────────────┐
│ Opcao               │ Diff │ Util    │ Prioridade   │
├─────────────────────┼──────┼─────────┼──────────────┤
│ Email Alertas       │ F    │ Alta    │ Alta         │
│ Telegram Notif.     │ M    │ Alta    │ Media        │
│ Backup Auto         │ F    │ Media   │ Media        │
│ Banco de Dados      │ A    │ Alta    │ Media        │
│ Relatorio Mensal    │ M    │ Media   │ Baja         │
│ Analise Tendencia   │ A    │ Alta    │ Alta         │
│ Validacao Dados     │ F    │ Media   │ Baja         │
└─────────────────────┴──────┴─────────┴──────────────┘

Diff: Dificuldade (F=Facil, M=Medio, A=Avancado)
Util: Utilidade pratica
Prioridade: Recomendacao de implementacao

PROXIMO PASSO: Escolha uma opcao e implemente no seu ambiente!
"""

print(__doc__)
