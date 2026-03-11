╔══════════════════════════════════════════════════════════════════════════════╗
║               GUIA SETUP - ALERTAS VIA TELEGRAM                               ║
║               Sistema Radar de Licitações PNCP v2.0                           ║
╚══════════════════════════════════════════════════════════════════════════════╝

📋 ÍNDICE
═══════════════════════════════════════════════════════════════════════════════
1. Pré-requisitos
2. Criar Bot Telegram
3. Configurar Token no Sistema
4. Criar Primeiro Alerta
5. Testar Funcionalidade
6. Agendar Monitoramento
7. Troubleshooting

═══════════════════════════════════════════════════════════════════════════════
1️⃣  PRÉ-REQUISITOS
═══════════════════════════════════════════════════════════════════════════════

✅ OBRIGATÓRIO:

• Windows 10/11 ou Linux
• Python 3.10+
• Conta Telegram pessoal (criar em telegram.org se necessário)
• Chave de API do Telegram (bot token)

✅ JÁ INSTALADO:

• python-telegram-bot (adicionado em requirements.txt)
• SQLite (incluso no Python)
• pandas, streamlit (já compatíveis)

═══════════════════════════════════════════════════════════════════════════════
2️⃣  CRIAR BOT TELEGRAM (@BotFather)
═══════════════════════════════════════════════════════════════════════════════

PASSO 1: Abrir Telegram

1. Abra o aplicativo Telegram
2. Se não tiver, baixe em: https://telegram.org

PASSO 2: Conversar com @BotFather

1. Procure por "@BotFather" (busca na aba de chats)
2. Abra a conversa
3. Envie: /start

Você verá uma lista de comandos:

    🤖 BotFather
    ─────────────
    I help you create and manage Telegram bots. Here are all the commands I
    know...
    
    /newbot - create a new bot
    /mybot - edit your bots
    /token - generate bot access token
    ...

PASSO 3: Criar novo bot

1. Envie: /newbot
2. BotFather pedirá um NOME para o bot (use algo descritivo)
   
   Exemplo: "Radar de Licitações SP"
   
3. BotFather pedirá um NOME DE USUÁRIO único (username)
   
   Exemplo: "radar_licitacoes_sp_bot"
   
   (IMPORTANTE: Deve terminar com "_bot")

PASSO 4: Copiar o TOKEN

O BotFather responderá com:

    Done! Congratulations on your new bot. You'll find it at t.me/radar_licitacoes_sp_bot.
    You can now add a description, about section and profile picture for your bot,
    see /help for a list of all commands.
    
    Use this token to access the HTTP API:
    │
    ├─ 123456789:ABCdefGHIjklmNOPqrstuvWXYZ-aBcDeFgHiJkL
    │
    Keep your token secure and store it safely!

✅ COPIE O TOKEN (a parte que começa com números e contém `:`)

═══════════════════════════════════════════════════════════════════════════════
3️⃣  OBTER CHAT_ID DO SEU GRUPO/CANAL
═══════════════════════════════════════════════════════════════════════════════

OPÇÃO A: Chat Privado Pessoal (Recomendado para teste)

Se quiser receber alertas em uma conversa privada com você mesmo:

1. Abra a conversa com seu bot
2. Envie qualquer mensagem
3. Acesse a URL:
   https://api.telegram.org/bot[SEU_TOKEN]/getUpdates
   (Substitua [SEU_TOKEN] pelo token que copiou)
4. Procure por "chat":
   {
     "ok": true,
     "result": [
       {
         "update_id": 123456789,
         "message": {
           "message_id": 1,
           "date": 1234567890,
           "chat": {
             "id": -987654321,    ← ESTE É SEU CHAT_ID
             "type": "private",
             ...

✅ Copie o número do campo "id" (pode ser positivo ou negativo)

OPÇÃO B: Grupo/Canal (Para alertas compartilhados)

1. Crie um grupo ou canal novo no Telegram
2. Adicione seu bot ao grupo/canal
3. Envie uma mensagem no grupo
4. Siga os passos da OPÇÃO A (getUpdates)

⚠️ IMPORTANTE:

• IDs de GRUPOS E CANAIS são NEGATIVOS (ex: -1234567890)
• IDs de CHATS PRIVADOS podem ser positivos ou negativos
• Chat_ID é DIFERENTE do nome do grupo

═══════════════════════════════════════════════════════════════════════════════
4️⃣  CONFIGURAR TOKEN NO SISTEMA
═══════════════════════════════════════════════════════════════════════════════

MÉTODO 1: Via Dashboard (Recomendado)

1. Abra o dashboard:
   streamlit run dashboard.py

2. Lado esquerdo → procure "🔔 ALERTAS TELEGRAM"

3. Clique em "⚙️ Configurar"

4. Expanda "🤖 Token do Telegram"

5. Cole seu token no campo de texto

6. Clique "✅ Validar Token"
   • Se aparecer ✓ verde: sucesso!
   • Se aparecer ✗ vermelho: token inválido ou sem conexão

7. Clique "💾 Salvar Token"

MÉTODO 2: Manual (config/alertas_config.json)

1. Abra o arquivo: config/alertas_config.json

2. Substitua "SEU_TOKEN_AQUI" pelo seu token real:

   {
     "telegram_token": "123456789:ABCdefGHIjklmNOPqrstuvWXYZ-aBcDeFgHiJkL",
     "alertas": [...]
   }

3. Salve o arquivo (Ctrl+S)

═══════════════════════════════════════════════════════════════════════════════
5️⃣  CRIAR PRIMEIRO ALERTA
═══════════════════════════════════════════════════════════════════════════════

VIA DASHBOARD (Recomendado):

1. Abra dashboard.py (se já não está aberto)

2. Clique em "🔔 ALERTAS TELEGRAM" → "⚙️ Configurar"

3. Seção "2️⃣ Novo Alerta"

4. Preencha os campos:

   • Nome: "Licitações SP - Teste"
   • Chat ID: seu chat_id (ex: -123456789)
   • Estados: Selecione "SP"
   • Órgãos: deixe em branco (=todos)
   • Valor mínimo: 0
   • Valor máximo: 1000000
   • Palavras-chave: deixe vago para teste
   • Ativar: ✓ (marque)

5. Clique "➕ Criar Alerta"

6. Marque "Enviar alerta de teste?" para verificar

7. Você deve receber uma mensagem no Telegram confirmando! 🎉

═══════════════════════════════════════════════════════════════════════════════
6️⃣  TESTAR FUNCIONALIDADE
═══════════════════════════════════════════════════════════════════════════════

TESTE 1: Enviar Alerta Manual

1. No dashboard, expanda seu alerta em "3️⃣ Seus Alertas"

2. Clique "📤 Testar"

3. Você deve receber a mensagem no Telegram em segundos

TESTE 2: Executar Monitor (Simular Nova Licitação)

1. Abra PowerShell/Terminal

2. Ative o venv:
   c:\licitacoes_pncp\venv\Scripts\Activate.ps1

3. Execute o monitor:
   python monitor_alertas.py

4. Se houver novas licitações no CSV, você receberá alertas! 📬

TESTE 3: Agendar Execução Automática (Windows)

Veja seção 7️⃣ abaixo.

═══════════════════════════════════════════════════════════════════════════════
7️⃣  AGENDAR MONITORAMENTO AUTOMÁTICO (Windows)
═══════════════════════════════════════════════════════════════════════════════

OPÇÃO A: Task Scheduler (Recomendado)

1. Pressione Windows + R

2. Digite: taskschd.msc (e Enter)

3. Task Scheduler abreAR

4. À direita, clique "Create Basic Task"

5. Nome: "PNCP_Alertas_Monitor"
   Descrição: "Verifica novas licitações e envia alertas"

6. Clique "Next"

7. Trigger: Selecione "Daily" (ou "Hourly" para mais frequência)
   Tempo: defina para executar a cada 5 minutos

8. Clique "Next"

9. Action: "Start a program"
   Program: C:\licitacoes_pncp\venv\Scripts\python.exe
   
   Arguments: monitor_alertas.py
   
   Start in: C:\licitacoes_pncp

10. Clique "Next" e "Finish"

✅ Pronto! O script executará automaticamente nos horários definidos

OPÇÃO B: Batch Script Simplificado

1. Crie arquivo: monitor_alertas.bat

   @echo off
   cd c:\licitacoes_pncp
   call venv\Scripts\activate.bat
   python monitor_alertas.py
   pause

2. Agende este .bat no Task Scheduler (mesmos passos acima)

═══════════════════════════════════════════════════════════════════════════════
8️⃣  TROUBLESHOOTING
═══════════════════════════════════════════════════════════════════════════════

PROBLEMA: "Token inválido"
└─ SOLUÇÃO:
   • Copie novamente do @BotFather (pode ter espaços em branco)
   • Certifique-se que está inteiro (começa com números, tem :)
   • Verifique se não há quebras de linha

PROBLEMA: "Chat ID não encontrado" / "400 Bad Request"
└─ SOLUÇÃO:
   • Certifique-se que adicionou o bot ao grupo/canal
   • Verifique se o Chat ID está correto (getUpdates)
   • Para grupos, o ID deve ser NEGATIVO

PROBLEMA: Nenhum alerta é recebido
└─ SOLUÇÃO:
   • Verifique se o alerta está marcado como "🟢 Ativo"
   • Certifique-se que tem licitações que batem no filtro
   • Execute "python monitor_alertas.py" de forma manual para debug
   • Verifique logs em: logs/monitor_alertas.log

PROBLEMA: "Erro de conexão" ao enviar
└─ SOLUÇÃO:
   • Verifique conexão de internet
   • Firewall pode estar bloqueando - adicione exceção
   • Tente testar em outro dispositivo

PROBLEMA: Sqlite database locked
└─ SOLUÇÃO:
   • Feche o dashboard
   • Aguarde 10 seg
   • Execute monitor_alertas.py novamente

═══════════════════════════════════════════════════════════════════════════════

✅ PRÓXIMOS PASSOS

Acesse: ALERTAS_TELEGRAM.md para documentação completa
         (inclui exemplos avançados, filtering, etc)

═══════════════════════════════════════════════════════════════════════════════

📞 SUPORTE

Se encontrar problemas não listados acima:

1. Verifique logs/monitor_alertas.log
2. Consulte ALERTAS_TELEGRAM.md (seção de troubleshooting)
3. Tente executar testes: pytest tests/test_alertas.py -v

═══════════════════════════════════════════════════════════════════════════════

Data: 07/03/2026
Projeto: Radar de Licitações TI v2.0
Status: ✅ Setup Alertas Telegram Completo
