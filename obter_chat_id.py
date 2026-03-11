import requests

TOKEN = "8775070167:AAGjAIkwPsyVpw1TyaYDkQVrzk7-IaiFIpw"

try:
    response = requests.get(
        f"https://api.telegram.org/bot{TOKEN}/getUpdates",
        timeout=5
    )
    data = response.json()
    
    if data['result']:
        chat_id = data['result'][0]['message']['chat']['id']
        print(f"\n✅ CHAT_ID ENCONTRADO!")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"Seu Chat ID: {chat_id}")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
        
        # Guardar em arquivo
        with open("chat_id.txt", "w") as f:
            f.write(str(chat_id))
        print(f"✓ Chat ID salvo em 'chat_id.txt'")
    else:
        print("❌ Nenhuma mensagem encontrada.")
        print("Certifique-se de enviar uma mensagem a @camelusradartibot no Telegram!")
        
except Exception as e:
    print(f"❌ Erro: {e}")
