╔══════════════════════════════════════════════════════════════════════════════╗
║            DOCUMENTAÇÃO COMPLETA - ALERTAS VIA TELEGRAM                       ║
║            Sistema Radar de Licitações PNCP v2.0                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

📋 ÍNDICE
═══════════════════════════════════════════════════════════════════════════════
1. Visão Geral
2. Arquitetura do Sistema
3. Componentes Principais
4. Uso via Dashboard
5. Uso Programático
6. Configuração Avançada
7. Scripts e Automação
8. Monitoramento e Logs
9. Troubleshooting
10. FAQ

═══════════════════════════════════════════════════════════════════════════════
1️⃣  VISÃO GERAL
═══════════════════════════════════════════════════════════════════════════════

O SISTEMA DE ALERTAS VIA TELEGRAM permite que você receba notificações em tempo
real (ou próximo a tempo real) quando novas licitações aparecerem no sistema PNCP,
filtradas por seus critérios específicos.

CARACTERÍSTICAS:

✅ Múltiplos alertas: Crie quantos alertas quiser com diferentes critérios
✅ Filtros avançados: Por UF, órgão, valor, palavras-chave
✅ Monitoramento automático: Executa a cada 5 minutos (configurável)
✅ Interface Streamlit: Configure tudo via dashboard web
✅ Banco de dados SQLite: Armazena alertas e histórico
✅ Múltiplos canais: Envie para chats privados, grupos ou canais
✅ Logging completo: Rastreie tudo que acontece
✅ Testes inclusos: 20+ testes unitários

FLUXO DE FUNCIONAMENTO:

    1. Dashboard (Criar Alerta)
           ↓
    2. AlertasDB (Armazenar em SQLite)
           ↓
    3. monitor_alertas.py (Executar periodicamente)
           ↓
    4. Detectar Novas Licitações (Comparar CSV)
           ↓
    5. Filtrar por Critérios do Alerta
           ↓
    6. TelegramAlerter (Enviar via API Telegram)
           ↓
    7. Registrar no Histórico
           ↓
    8. 🔔 Notificação no Telegram!

═══════════════════════════════════════════════════════════════════════════════
2️⃣  ARQUITETURA DO SISTEMA
═══════════════════════════════════════════════════════════════════════════════

ESTRUTURA DE DIRETÓRIOS

    c:\licitacoes_pncp\
    ├── config/                      # Configurações
    │   ├── alertas_config.json     # Config principal (token, template)
    │   ├── hash_anterior.txt       # Hash do último CSV processado
    │   └── backup_licitacoes.csv   # Backup para comparação
    ├── dados/
    │   ├── licitacoes.csv          # CSV de licitações
    │   └── alertas.db              # Banco SQLite de alertas
    ├── logs/
    │   ├── monitor_alertas.log     # Log do monitor
    │   └── alertas.log             # Log geral de alertas
    ├── tests/
    │   └── test_alertas.py         # Testes unitários (20+)
    ├── dashboard.py                # App Streamlit com UI de alertas
    ├── alerts_db.py                # Gerenciador de banco de dados
    ├── utils_telegram.py           # Core do Telegram API wrapper
    ├── monitor_alertas.py          # Script de monitoramento
    └── requirements.txt            # python-telegram-bot (nova dependency)

ARQUIVOS PRINCIPAIS

┌─ utils_telegram.py (350+ linhas)
│  ├─ TelegramAlerter: Classe principal para envio
│  │  ├─ enviar_mensagem()
│  │  ├─ formatar_alerta_licitacao()
│  │  ├─ formatar_confirmacao_config()
│  │  ├─ formatar_resumo_alertas()
│  │  └─ testar_conexao()
│  ├─ validar_token()
│  ├─ validar_chat_id()
│  └─ criar_link_pncp()
│
├─ alerts_db.py (400+ linhas)
│  ├─ AlertasDB: Gerenciador do SQLite
│  │  ├─ criar_alerta()
│  │  ├─ listar_alertas()
│  │  ├─ atualizar_alerta()
│  │  ├─ deletar_alerta()
│  │  ├─ registrar_alerta_enviado()
│  │  ├─ listar_historico()
│  │  └─ obter_status_monitoramento()
│  └─ Schema SQL:
│     ├─ alertas (id, nome, chat_id, ufs, valor_min/max, ...)
│     ├─ historico_alertas (id, alerta_id, numero_edital, valor, data_envio)
│     └─ monitoramento (intervalo, ativo, ultimo_check, hash_anterior)
│
├─ monitor_alertas.py (500+ linhas)
│  ├─ carregar_csv()
│  ├─ detectar_novas_licitacoes()
│  ├─ filtrar_licitacoes_por_alerta()
│  ├─ enviar_alertas()
│  └─ processar_alertas() [função principal]
│
└─ dashboard.py (integração UI)
   └─ Sidebar "🔔 ALERTAS TELEGRAM"
      ├─ Tabs: ⚙️ Configurar | 📊 Histórico
      └─ Sub-seções:
         ├─ Setup do token
         ├─ Criar novo alerta
         ├─ Gerenciar alertas
         └─ Visualizar histórico

═══════════════════════════════════════════════════════════════════════════════
3️⃣  COMPONENTES PRINCIPAIS
═══════════════════════════════════════════════════════════════════════════════

A) CLASSE TelegramAlerter

Responsável por comunicação com API do Telegram.

EXEMPLO DE USO:

    from utils_telegram import TelegramAlerter
    
    bot = TelegramAlerter(token="123456:ABC...")
    
    # Testar conexão
    if bot.testar_conexao():
        print("✓ Bot conectado")
    
    # Enviar mensagem simples
    resultado = bot.enviar_mensagem(
        chat_id="-987654321",
        mensagem="Olá! Esta é uma mensagem de teste."
    )
    
    # Formatar e enviar alerta de licitação
    licitacao = {
        'orgao': 'PREFEITURA SP',
        'objeto': 'Contratação de serviços de TI',
        'valor_estimado': 250000,
        'uf': 'SP',
        'municipio': 'São Paulo',
        'data_publicacao': '2026-03-07',
        'numero_edital': 'EDITAL-2026-001'
    }
    
    msg = bot.formatar_alerta_licitacao(licitacao)
    bot.enviar_mensagem(chat_id, msg)

MÉTODOS:

    enviar_mensagem(chat_id, mensagem, parse_mode="HTML") → dict|None
        Envia mensagem para chat do Telegram
        Returns: Resposta JSON da API ou None

    formatar_alerta_licitacao(licitacao: dict) → str
        Formata uma licitação como HTML para Telegram

    formatar_confirmacao_config(config: dict) → str
        Formata confirmação de configuração de alerta

    formatar_resumo_alertas(alertas: list) → str
        Formata múltiplos alertas como resumo

    testar_conexao() → bool
        Valida token e conexão com Telegram

    obter_info_bot() → dict
        Obtém informações do bot (@username, etc)

B) CLASSE AlertasDB

Responsável por persistência de alertas em SQLite.

EXEMPLO DE USO:

    from alerts_db import AlertasDB
    
    db = AlertasDB()
    
    # Criar alerta
    db.criar_alerta(
        nome="Meu Primeiro Alerta",
        chat_id="-123456789",
        ufs=["SP", "RJ"],
        valor_min=100000,
        valor_max=500000,
        orgaos=["*"],
        palavras_chave=["software", "cloud"]
    )
    
    # Listar alertas ativos
    alertas = db.listar_alertas(apenas_ativos=True)
    for alerta in alertas:
        print(f"✓ {alerta['nome']}: {', '.join(alerta['ufs'])}")
    
    # Registrar envio de alerta
    db.registrar_alerta_enviado(
        alerta_id=1,
        numero_edital="EDITAL-001",
        valor=250000,
        orgao="PREFEITURA"
    )
    
    # Verificar histórico
    historico = db.listar_historico(alerta_id=1)
    print(f"Editais enviados: {len(historico)}")

MÉTODOS:

    criar_alerta(**kwargs) → bool
        Cria novo alerta com validação de unicidade

    listar_alertas(apenas_ativos=False) → list[dict]
        Lista todos os alertas (ou apenas ativos)

    obter_alerta(alerta_id) → dict|None
        Obtém um alerta específico por ID

    atualizar_alerta(alerta_id, **kwargs) → bool
        Atualiza campos de um alerta

    deletar_alerta(alerta_id) → bool
        Deleta alerta e seu histórico

    registrar_alerta_enviado(alerta_id, numero_edital, valor, orgao) → bool
        Registra que um alerta foi enviado

    listar_historico(alerta_id=None, limite=100) → list[dict]
        Lista histórico de alertas enviados

    atualizar_monitoramento(**kwargs) → bool
        Atualiza status de monitoramento

    obter_status_monitoramento() → dict
        Obtém status atual do monitoramento

SCHEMA SQL:

    CREATE TABLE alertas (
        id INTEGER PRIMARY KEY,
        nome TEXT NOT NULL UNIQUE,
        chat_id TEXT NOT NULL,
        ufs TEXT NOT NULL,              -- JSON: ["SP", "RJ"]
        valor_min REAL DEFAULT 0,
        valor_max REAL DEFAULT 999999999,
        orgaos TEXT DEFAULT '*',        -- JSON: ["*"] ou nomes
        palavras_chave TEXT DEFAULT '', -- JSON: ["software", "cloud"]
        ativo INTEGER DEFAULT 1,
        frequencia_min INTEGER DEFAULT 60,
        criado_em TEXT,
        ultimo_alerta TEXT,
        proxximo_alerta TEXT
    );

    CREATE TABLE historico_alertas (
        id INTEGER PRIMARY KEY,
        alerta_id INTEGER NOT NULL,
        numero_edital TEXT NOT NULL,
        valor REAL NOT NULL,
        orgao TEXT NOT NULL,
        data_envio TEXT DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'enviado'
    );

    CREATE TABLE monitoramento (
        id INTEGER PRIMARY KEY,
        intervalo_segundos INTEGER DEFAULT 300,
        ativo INTEGER DEFAULT 1,
        ultimo_check TEXT,
        hash_anterior TEXT,
        total_licitacoes INTEGER DEFAULT 0,
        total_alertas_enviados INTEGER DEFAULT 0,
        ultimo_erro TEXT
    );

═══════════════════════════════════════════════════════════════════════════════
4️⃣  USO VIA DASHBOARD
═══════════════════════════════════════════════════════════════════════════════

O Dashboard Streamlit oferece uma interface completa para gerenciar alertas.

ACESSARE O DASHBOARD:

    streamlit run dashboard.py

Abrirá em: http://localhost:8501

NAVEGAÇÃO:

    Barra Lateral Direita → Procure "🔔 ALERTAS TELEGRAM"

Você encontrará duas abas:

    1️⃣  ⚙️ CONFIGURAR
    │   ├─ 1️⃣ Configurar Bot
    │   │  ├─ Token do Telegram (validar e salvar)
    │   │  └─ Testar conexão
    │   ├─ 2️⃣ Novo Alerta
    │   │  ├─ Nome
    │   │  ├─ Chat ID
    │   │  ├─ Estados (UFs)
    │   │  ├─ Órgãos
    │   │  ├─ Range de Valores
    │   │  ├─ Palavras-chave
    │   │  └─ Ativar/Desativar
    │   └─ 3️⃣ Seus Alertas
    │      ├─ Listar todos
    │      ├─ Editar (ativar/desativar)
    │      └─ Deletar
    │
    2️⃣  📊 HISTÓRICO
        ├─ Resumo (total, valor, alertas únicos)
        └─ Tabela com últimos 50 alertas enviados

FLUXO RECOMENDADO:

1. Setup Token
   • Clique em "1️⃣ Configurar Bot"
   • Cole seu token (obtenha em @BotFather)
   • Clique "✅ Validar Token" (deve aparecer ✓)
   • Clique "💾 Salvar Token"

2. Criar Primeiro Alerta
   • Preencha "2️⃣ Novo Alerta"
   • Nome: "Teste SP"
   • Chat ID: seu ID (ou -123 para testar)
   • UF: SP
   • Clique "➕ Criar Alerta"

3. Testar
   • Expanda "3️⃣ Seus Alertas"
   • Clique "📤 Testar"
   • Você deve receber mensagem no Telegram!

4. Executar Monitor
   • Abra terminal
   • python monitor_alertas.py
   • Se há novas licitações, receberá alertas

═══════════════════════════════════════════════════════════════════════════════
5️⃣  USO PROGRAMÁTICO
═══════════════════════════════════════════════════════════════════════════════

EXEMPLO 1: Enviar Alerta Manual

    from utils_telegram import TelegramAlerter
    
    bot = TelegramAlerter(token="seu_token_aqui")
    
    # Enviar mensagem simples
    bot.enviar_mensagem(
        chat_id="-123456789",
        mensagem="<b>Olá!</b> Isto é um <i>teste</i>"
    )

EXEMPLO 2: Criar Alerta Programaticamente

    from alerts_db import AlertasDB
    
    db = AlertasDB()
    
    # Criar alerta
    sucesso = db.criar_alerta(
        nome="Licitações Automáticas",
        chat_id="-123456789",
        ufs=["SP", "RJ"],
        valor_min=50000,
        valor_max=1000000,
        palavras_chave=["api", "cloud"]
    )
    
    if sucesso:
        print("✓ Alerta criado!")

EXEMPLO 3: Processar Alertas Customizado

    import pandas as pd
    from alerts_db import AlertasDB
    from utils_telegram import TelegramAlerter
    
    # Carregar dados
    df = pd.read_csv("dados/licitacoes.csv")
    
    # Inicializar
    db = AlertasDB()
    token = "seu_token"  # Obtenha de config
    bot = TelegramAlerter(token)
    
    # Filtrar licitações (ex: SP, > 100k)
    licitacoes = df[(df['uf'] == 'SP') & (df['valor_estimado'] > 100000)]
    
    # Enviar para cada alerta
    for alerta in db.listar_alertas(apenas_ativos=True):
        for _, lic in licitacoes.iterrows():
            msg = bot.formatar_alerta_licitacao(lic.to_dict())
            bot.enviar_mensagem(alerta['chat_id'], msg)
            db.registrar_alerta_enviado(
                alerta['id'],
                lic['numero_edital'],
                lic['valor_estimado'],
                lic['orgao']
            )

═══════════════════════════════════════════════════════════════════════════════
6️⃣  CONFIGURAÇÃO AVANÇADA
═══════════════════════════════════════════════════════════════════════════════

ARQUIVO: config/alertas_config.json

Você pode editar manualmente este arquivo para configurações avançadas:

    {
      "telegram_token": "123456:ABC...",
      "alertas": [
        {
          "id": 1,
          "nome": "Licitações SP - Alta Valor",
          "ativo": true,
          "chat_id": "-123456789",
          "ufs": ["SP"],
          "valor_min": 100000,
          "valor_max": 5000000,
          "orgaos": ["*"],
          "palavras_chave": ["software", "cloud"],
          "notificar_quando": "nova",
          "frequencia_min": 60,
          "criado_em": "2026-03-07T10:00:00",
          "ultimo_alerta": "2026-03-07T15:30:00",
          "proxximo_alerta": "2026-03-07T16:30:00"
        }
      ],
      "monitoramento": {
        "intervalo_segundos": 300,
        "ativo": true,
        "ultimo_check": "2026-03-07T16:25:00",
        "hash_anterior": "abc123def456"
      }
    }

CAMPOS ESPECIAIS:

• orgaos: ["*"] = todos os órgãos
• orgaos: ["PREFEITURA"] = apenas órgãos que contêm "PREFEITURA"
• palavras_chave: [] = sem filtro por palavras
• palavras_chave: ["software"] = apenas licitações com "software" no objeto

VARIÁVEIS DE AMBIENTE (futuro):

Você pode usar variáveis de ambiente para segurança:

    # Windows PowerShell
    $env:TELEGRAM_TOKEN = "seu_token"
    $env:TELEGRAM_CHAT_ID = "-123456789"

    # Linux/Mac
    export TELEGRAM_TOKEN="seu_token"
    export TELEGRAM_CHAT_ID="-123456789"

═══════════════════════════════════════════════════════════════════════════════
7️⃣  SCRIPTS E AUTOMAÇÃO
═══════════════════════════════════════════════════════════════════════════════

EXECUTAR MONITOR MANUALMENTE

    cd c:\licitacoes_pncp
    python monitor_alertas.py

Saída esperada:

    ════════════════════════════════════════════════
    INICIANDO PROCESSAMENTO DE ALERTAS - 2026-03-07 16:30:15
    Arquivo CSV: dados/licitacoes.csv
    
    ✓ CSV carregado: 2054 registros
    Detectando novas licitações...
    
    Processando 3 alertas ativos...
    
    ├─ Processando alerta: 'Licitações SP'
    │  ├─ Filtrando por: SP, R$ 0.00 - R$ 1,000,000.00
    │  └─ 2 alerta(s) enviado(s)
    │
    ├─ Processando alerta: 'Licitações RJ'
    │  └─ Nenhuma licitação relevante
    │
    └─ Processando alerta: 'Palavras-chave Cloud'
       ├─ Filtrando por: todas as UFs
       └─ 1 alerta(s) enviado(s)
    
    ════════════════════════════════════════════════
    RESUMO: 3 alerta(s) enviado(s) com sucesso
    ════════════════════════════════════════════════

AGENDAR NO WINDOWS (Task Scheduler)

Arquivo: monitor_alertas.bat

    @echo off
    cd c:\licitacoes_pncp
    call venv\Scripts\activate.bat
    python monitor_alertas.py
    exit /b %errorlevel%

Depois agendar via Task Scheduler a cada 5 minutos.

AGENDAR NO LINUX (Cron)

    # Executar a cada 5 minutos
    */5 * * * * cd /home/user/licitacoes_pncp && python monitor_alertas.py

    # Ou redirecionar output para log
    */5 * * * * cd /home/user/licitacoes_pncp && python monitor_alertas.py >> logs/monitor_alertas.log 2>&1

═══════════════════════════════════════════════════════════════════════════════
8️⃣  MONITORAMENTO E LOGS
═══════════════════════════════════════════════════════════════════════════════

ARQUIVO: logs/monitor_alertas.log

Todos os eventos são registrados:

    2026-03-07 16:30:15,235 - INFO - ════════════════════════════════════════════════
    2026-03-07 16:30:15,236 - INFO - INICIANDO PROCESSAMENTO DE ALERTAS - 2026-03-07 16:30:15
    2026-03-07 16:30:15,237 - INFO - Arquivo CSV: dados/licitacoes.csv
    2026-03-07 16:30:16,450 - INFO - ✓ CSV carregado: 2054 registros
    2026-03-07 16:30:16,451 - INFO - Detectando novas licitações...
    2026-03-07 16:30:16,456 - INFO - Processando 3 alertas ativos...
    2026-03-07 16:30:17,123 - INFO - ✓ Alerta enviado: EDITAL-2026-001 → Licitações SP

VER LOGS:

    # PowerShell
    Get-Content logs/monitor_alertas.log -Tail 50

    # CMD
    type logs/monitor_alertas.log | findstr "ERROR"

    # Linux
    tail -f logs/monitor_alertas.log

MONITORAGEMENT AUTOMÁTICO:

No dashboard, em "🔔 ALERTAS" → "📊 Histórico", você pode ver:

    • Total de alertas enviados
    • Valor total movimentado
    • Alertas ativos
    • Últimes 50 eventos

═══════════════════════════════════════════════════════════════════════════════
9️⃣  TROUBLESHOOTING
═══════════════════════════════════════════════════════════════════════════════

PROBLEMA 1: Token não funciona

SINTOMAS:
    ✗ "Token inválido"
    ✗ "401 Unauthorized"

SOLUÇÕES:
    [ ] Copie o token novamente do @BotFather (há espaços?)
    [ ] Verifique se está inteiro (nunca quebra linha)
    [ ] Regenere o token (/token no BotFather)
    [ ] Teste a conexão: testar_conexao() no bot

TESTE MANUAL:

    from utils_telegram import TelegramAlerter, validar_token
    token = "seu_token"
    
    if validar_token(token):
        bot = TelegramAlerter(token)
        if bot.testar_conexao():
            print("✓ OK!")
        else:
            print("✗ Falhou")

PROBLEMA 2: Não recebe alertas

SINTOMAS:
    ✓ Alerta criado
    ✗ Nenhuma mensagem no Telegram

CHECKLIST:
    [ ] Alerta está marcado como "🟢 Ativo"?
    [ ] Chat ID está correto?
    [ ] Há licitações que batem no filtro?
    [ ] Bot foi adicionado ao grupo/canal?
    [ ] Monitor.alertas.py foi executado?

TESTE:

    # Executar com debug
    python monitor_alertas.py

    # Verificar logs
    type logs/monitor_alertas.log | findstr "ERROR"

    # Testar envio manual
    from utils_telegram import TelegramAlerter
    bot = TelegramAlerter("seu_token")
    resultado = bot.enviar_mensagem("-123456789", "<b>Teste</b>")
    print(resultado)

PROBLEMA 3: "Database is locked"

SINTOMAS:
    ✗ Erro ao salvar alerta
    ✗ "sqlite3.OperationalError: database is locked"

SOLUÇÃO:
    [ ] Feche o dashboard (Ctrl+C)
    [ ] Aguarde 10 segundos
    [ ] Tente novamente
    [ ] Se continuar, reinicie o computador

PROBLEMA 4: CSV não é detectado

SINTOMAS:
    ✗ "CSV não encontrado"
    ✗ 0 registros carregados

SOLUÇÃO:
    [ ] Verifique se dados/licitacoes.csv existe
    [ ] Ou execute: python pncp_radar_ti_plus.py para gerar
    [ ] Verifique caminho correto (relativo ao diretório de projeto)

PROBLEMA 5: Monitoramento não executa automaticamente

SINTOMAS:
    ✗ Alerta configurado, mas nunca executa

SOLUÇÃO (Windows):
    [ ] Task Scheduler está ativo?
    [ ] Verificar histórico de tarefas
    [ ] Executar manualmente: python monitor_alertas.py
    [ ] Adicionar verificação de logs

SOLUÇÃO (Linux):
    [ ] Cron está rodando? systemctl status cron
    [ ] Verificar logs: journalctl -u cron
    [ ] Testar comando manualmente

═══════════════════════════════════════════════════════════════════════════════
🔟 FAQ
═══════════════════════════════════════════════════════════════════════════════

P: Posso enviar alertas para múltiplos chats?
R: Sim! Crie alertas diferentes com chat_ids diferentes, todos serão monitorados.

P: Quantos alertas posso criar?
R: Ilimitado, mas recomendado < 50 para performance.

P: Com que frequência o sistema verifica novas licitações?
R: Padrão: 5 minutos (configurável em monitoramento.intervalo_segundos)

P: Posso pausar alertas sem deletar?
R: Sim! Clique "Desativar" em "🔴 Seus Alertas" no dashboard.

P: E se tiver muitas licitações novas?
R: O sistema enviará uma por vez (com delay de 0.5s entre elas).

P: Onde estão meus dados salvos?
R: dados/alertas.db (SQLite), config/alertas_config.json (config)

P: Posso usar a mesma conta para múltiplos bots?
R: Sim, cada bot tem seu próprio token.

P: O sistema funciona sem internet?
R: Não, precisa de conexão para a API do Telegram.

P: Como exportar histórico de alertas?
R: Acesse: dashboard.py → "🔔 ALERTAS" → "📊 Histórico" → dados aparecem,
   ou execute: db.listar_historico() e exporte como CSV.

P: Posso agendar alertas para horários específicos?
R: Sim, edite monitoramento.intervalo_segundos e use frequencia_min do alerta.

═══════════════════════════════════════════════════════════════════════════════

✅ PRÓXIMOS PASSOS

1. Se é primeira vez: Leia SETUP_TELEGRAM.md
2. Depois de configurar: Crie seu primeiro alerta no Dashboard
3. Para automação: Agende o monitor em Task Scheduler (Windows) ou Cron (Linux)
4. Para debug: Verifique logs/monitor_alertas.log

═══════════════════════════════════════════════════════════════════════════════

📞 SUPORTE

Problemas não resolvidos? Verifique:
1. logs/monitor_alertas.log (erros detalhados)
2. Seção de TROUBLESHOOTING acima
3. Teste com pytest tests/test_alertas.py -v

═══════════════════════════════════════════════════════════════════════════════

Data: 07/03/2026
Versão: 2.0
Projeto: Radar de Licitações PNCP
Status: ✅ Documentação Completa
