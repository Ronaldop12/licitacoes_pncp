from utils_email import EmailAlerter

print("🔍 Testando configuração de email...\n")

bot = EmailAlerter(
    smtp_server="smtp.gmail.com",
    smtp_port=587,
    email_from="ronaldo.carpediem12@gmail.com",
    senha="lykwqkdktiytrtqe"
)

if bot.validar_configuracao():
    print("✅ SUCESSO!")
    print("   Email: ronaldo.carpediem12@gmail.com")
    print("   Status: Pode enviar mensagens")
else:
    print("❌ Erro na configuração!")
    print("   Verifique senha e email")
