#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para testar token Telegram e obter Chat ID
"""

import requests
import sys
from utils_telegram import TelegramAlerter

TOKEN = "8775070167:AAGjAIkwPsyVpw1TyaYDkQVrzk7-IaiFIpw"

print("=" * 70)
print("🔍 TESTANDO TOKEN TELEGRAM")
print("=" * 70)

# 1. Testar conexão com bot
try:
    print("\n1️⃣  Testando conexão com bot...")
    response = requests.get(
        f"https://api.telegram.org/bot{TOKEN}/getMe",
        timeout=5
    )
    
    if response.status_code == 200:
        bot_info = response.json()['result']
        print(f"   ✅ BOT CONECTADO!")
        print(f"   📱 Nome do bot: @{bot_info['username']}")
        print(f"   🆔 Bot ID: {bot_info['id']}")
    else:
        print(f"   ❌ Erro: Status {response.status_code}")
        sys.exit(1)
except Exception as e:
    print(f"   ❌ Erro de conexão: {e}")
    sys.exit(1)

# 2. Instruções para obter Chat ID
print("\n" + "=" * 70)
print("📱 PRÓXIMOS PASSOS PARA OBTER CHAT ID")
print("=" * 70)
print("""
1. Abra TELEGRAM no seu celular ou computador

2. Procure por: @camelusradartibot

3. Clique em "Start" ou envie uma mensagem (ex: "oi")

4. Retorne aqui e rode este comando:

   python -c "import requests; data = requests.get('https://api.telegram.org/bot8775070167:AAGjAIkwPsyVpw1TyaYDkQVrzk7-IaiFIpw/getUpdates').json(); chat = data['result'][0]['message']['chat']['id'] if data['result'] else None; print(f'CHAT_ID: {chat}'); print(f'Copie este número e guarde!' if chat else 'Nenhuma mensagem recebida. Envie mensagem ao bot primeiro!')"
   
OU visite esse link direto:
   https://api.telegram.org/bot8775070167:AAGjAIkwPsyVpw1TyaYDkQVrzk7-IaiFIpw/getUpdates

   Procure por: "id" dentro de "chat"
""")

print("=" * 70)
print("✅ Se você JÁ TEM o CHAT_ID, rode:")
print("=" * 70)
print("""
   python -c "from utils_telegram import TelegramAlerter; bot = TelegramAlerter('8775070167:AAGjAIkwPsyVpw1TyaYDkQVrzk7-IaiFIpw'); bot.enviar_mensagem('SEU_CHAT_ID', '🎯 ALERTA TESTE - Sistema Radar de Licitações TI está funcionando!')"

Substitua 'SEU_CHAT_ID' por seu número!
""")
