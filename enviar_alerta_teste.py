#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para enviar alerta de teste ao Telegram
"""

from utils_telegram import TelegramAlerter
from datetime import datetime

TOKEN = "8775070167:AAGjAIkwPsyVpw1TyaYDkQVrzk7-IaiFIpw"
CHAT_ID = "411444359"

bot = TelegramAlerter(TOKEN)

# Criar mensagem de teste formatada
mensagem = """<b>🎯 ALERTA TESTE - Sistema Radar TI ✅</b>

<b>Status:</b> Sistema funcionando perfeitamente!

<b>Bot:</b> @camelusradartibot
<b>Data/Hora:</b> """ + datetime.now().strftime("%d/%m/%Y %H:%M:%S") + """

<b>Próximas Ações:</b>
✅ Configurar alertas no Dashboard
✅ Definir critérios de filtragem  
✅ Ativar monitoramento automático

<i>Você receberá notificações aqui quando novas licitações forem encontradas!</i>"""

print("📤 Enviando alerta de teste...\n")
resultado = bot.enviar_mensagem(CHAT_ID, mensagem)

if resultado:
    print("✅ SUCESSO! Alerta enviado para Telegram!")
    print(f"\n📊 Resposta da API:")
    print(f"   Message ID: {resultado['result']['message_id']}")
    if 'first_name' in resultado['result']['chat']:
        print(f"   Chat: {resultado['result']['chat']['first_name']}")
    print(f"\n🔔 Verifique seu Telegram!")
else:
    print("❌ Falha ao enviar!")
