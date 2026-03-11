╔════════════════════════════════════════════════════════════════╗
║                  QUICK START - 5 MINUTOS                        ║
║             Configurar Alertas Telegram no Dashboard             ║
╚════════════════════════════════════════════════════════════════╝

🚀 INÍCIO RÁPIDO
═══════════════════════════════════════════════════════════════

1️⃣  ABRIR DASHBOARD
    
    Abra terminal e execute:
    streamlit run dashboard.py
    
    Acesse: http://localhost:8501

2️⃣  CONFIGURAR TOKEN
    
    Lado direito da tela → 🔔 ALERTAS TELEGRAM
    
    Clique: ⚙️ Configurar
    
    Expanda: 🤖 Token do Telegram
    
    Cole seu token:
    8775070167:AAGjAIkwPsyVpw1TyaYDkQVrzk7-IaiFIpw
    
    Clique: ✅ Validar Token
    
    Clique: 💾 Salvar Token

3️⃣  OBTER CHAT ID
    
    Abra Telegram → Pesquise seu bot
    
    Inicie conversa e envie qualquer mensagem
    
    Abra navegador e acesse:
    https://api.telegram.org/bot8775070167:AAGjAIkwPsyVpw1TyaYDkQVrzk7-IaiFIpw/getUpdates
    
    Procure por: "chat": {"id": xxx
    
    Copie o número (ex: -123456789)

4️⃣  CRIAR ALERTA
    
    Dashboard → 🔔 ALERTAS TELEGRAM → ⚙️ Configurar
    
    Preencha:
    • Nome: "Teste SP"
    • Chat ID: [seu número]
    • Estados: SP
    • Clique: ➕ Criar Alerta
    
    ✅ Pronto! Alerta criado.

5️⃣  TESTAR
    
    Expanda seu alerta em "3️⃣ Seus Alertas"
    
    Clique: 📤 Testar
    
    🔔 Receba mensagem no Telegram!

═══════════════════════════════════════════════════════════════

✅ CONCLUSÃO EM 5 MIN

Seu sistema de alertas já está funcionando!

PRÓXIMO: Ler SETUP_TELEGRAM.md para configuração completa.

═══════════════════════════════════════════════════════════════
