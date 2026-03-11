╔════════════════════════════════════════════════════════════════════════════════╗
║                    FLUXO DE TRANSIÇÃO - VISUAL GUIDE                          ║
║                   De Chat 1 (Cache/Links) → Chat 2 (Alertas)                  ║
╚════════════════════════════════════════════════════════════════════════════════╝


═══════════════════════════════════════════════════════════════════════════════
                        O QUE FOI FEITO - SESSÃO 1
═══════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│                          PROGRESSO VISUAL                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PROBLEMA 1: Cache indefinido em Streamlit                                 │
│  ❌ → ✅ RESOLVIDO: TTL=300s + Hash-based invalidation                      │
│                                                                             │
│  PROBLEMA 2: Sem links para editais                                        │
│  ❌ → ✅ RESOLVIDO: gerar_link_edital() + Cards interface                   │
│                                                                             │
│  PROBLEMA 3: Transição de conhecimento                                     │
│  ❌ → ✅ RESOLVIDO: 4 arquivos de documentação criados                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

↓ ↓ ↓

┌─────────────────────────────────────────────────────────────────────────────┐
│                    ESTADO ATUAL DO PROJETO                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ✅ Dashboard rodando (localhost:8501)                                      │
│  ✅ 27 UFs sendo exibidas corretamente                                      │
│  ✅ 2054 licitações com links funcionais                                    │
│  ✅ Cache inteligente com invalidação automática                            │
│  ✅ Interface "Links de Editais" com cards expandíveis                      │
│  ✅ 46/46 testes passando                                                   │
│  ✅ Documentação de transição pronta                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
                       O QUE FAZER - SESSÃO 2 (VOCÊ)
═══════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│                          TIMELINE ESPERADA                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ⏱️ LEITURA E SETUP (45 min)                                                │
│  ├─ Ler PROMPT_ESPECIALISTA_ALERTAS_TELEGRAM.md ........... 30 min 📖      │
│  ├─ Setup ambiente e verificar tudo funciona ............ 10 min ⚙️        │
│  └─ Entender fluxo de implementação .................... 5 min 🎯          │
│                                                                             │
│  📦 FASE 1 - Setup Telegram (30 min)                                        │
│  ├─ Criar bot no BotFather ............................... 5 min 🤖       │
│  ├─ Obter token e chat_id ............................... 5 min 🔑        │
│  ├─ Teste inicial com python-telegram-bot ............... 15 min ✉️       │
│  └─ Validar conexão funciona ............................ 5 min ✅        │
│                                                                             │
│  💾 FASE 2 - Backend Database (45 min)                                      │
│  ├─ Criar schema SQLite .................................. 15 min 🗄️      │
│  ├─ Funções de CRUD ...................................... 20 min 📝      │
│  └─ Testes database ...................................... 10 min ✅      │
│                                                                             │
│  🎨 FASE 3 - Dashboard Interface (1 hour)                                   │
│  ├─ Sidebar "🔔 ALERTAS" ................................. 20 min 🖼️      │
│  ├─ Formulário de configuração ........................... 20 min 📋      │
│  ├─ Teste de alerta ..................................... 10 min ✉️       │
│  └─ Listar alertas ativos ................................ 10 min 📊      │
│                                                                             │
│  🔍 FASE 4 - Monitor Script (45 min)                                        │
│  ├─ Detectar novos registros .............................. 15 min 🔎      │
│  ├─ Aplicarfiltros ........................................ 15 min 🎯      │
│  ├─ Formatar mensagem HTML ................................ 10 min 📋      │
│  └─ Enviar via Telegram ................................... 5 min ✉️       │
│                                                                             │
│  ✅ FASE 5 - Testes e Documentação (30 min)                                 │
│  ├─ test_alertas.py (20+ testes) ......................... 15 min 🧪      │
│  ├─ ALERTAS_TELEGRAM.md .................................. 10 min 📖      │
│  └─ Validação end-to-end .................................. 5 min ✅      │
│                                                                             │
│  ═════════════════════════════════════════════════════════════════════════  │
│  TOTAL: ~3h 15 min                                                         │
│                                                                             │
│  Margem extra recomendada: 30 min (debugging)                              │
│  → TEMPO TOTAL ESTIMADO: 3h 45 min ⏰                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
                        ARQUITETURA DO PROJETO
═══════════════════════════════════════════════════════════════════════════════

                            ┌─────────────────┐
                            │  Usuário/UI     │
                            │  dashboard.py   │
                            └────────┬────────┘
                                     │
                  ┌──────────────────┼──────────────────┐
                  │                  │                  │
         ┌────────▼────────┐  ┌─────▼────────┐  ┌─────▼────────┐
         │   Sidebar UI    │  │   Filtros    │  │   Tabelas    │
         │  (Alertas Tab)  │  │   Existing   │  │   com Links  │
         └────────┬────────┘  └──────────────┘  └──────────────┘
                  │
                  │ Configuração
                  ↓
         ┌────────────────────────────┐
         │   DB: alertas.db           │
         │  ┌──────────────────────┐  │
         │  │ alertas              │  │
         │  │ ├─ id               │  │
         │  │ ├─ titulo           │  │
         │  │ ├─ ufs              │  │
         │  │ ├─ palavras_chave   │  │
         │  │ ├─ telegram_id      │  │
         │  │ └─ ativo            │  │
         │  └──────────────────────┘  │
         └────────▲───────────────────┘
                  │
                  │ Read config
                  │
         ┌────────┴──────────────────────┐
         │   Monitor Script              │
         │   monitor_alertas.py          │
         │  (Roda a cada 5 minutos)      │
         │                               │
         │  ├─ Ler licitacoes.csv        │
         │  ├─ Filtrar por config        │
         │  ├─ Detectar novos            │
         │  ├─ Formatar mensagem         │
         │  └─ Enviar via Telegram       │
         └────────┬──────────────────────┘
                  │
                  ↓
         ┌────────────────────┐
         │  Telegram API      │
         │  python-telegram   │
         │  -bot              │
         └────────┬───────────┘
                  │
                  ↓
         ┌────────────────────┐
         │  Usuário Chat      │
         │  (Recebe alertas)  │
         └────────────────────┘


═══════════════════════════════════════════════════════════════════════════════
                    ARQUIVOS QUE VOCÊ CRIARÁ
═══════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│  ARQUIVO                    │ LINHAS │ FASE │ COMPLEXIDADE                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  utils_telegram.py          │ ~250  │  1   │ ⭐⭐☆☆☆ (Simples)           │
│  └─ TelegramAlerter class   │       │      │ [wrapper da API oficial]      │
│                                                                             │
│  monitor_alertas.py         │ ~600  │  4   │ ⭐⭐⭐☆☆ (Médio)            │
│  └─ Lógica de monitoramento │       │      │ [core do sistema]             │
│                                                                             │
│  test_alertas.py            │ ~300  │  5   │ ⭐⭐⭐☆☆ (Médio)            │
│  └─ 20+ testes novos        │       │      │ [cobertura robusta]           │
│                                                                             │
│  config/alertas_config.json │ ~50   │  2   │ ⭐☆☆☆☆ (Trivial)           │
│  └─ Exemplo de config       │       │      │ [template JSON]               │
│                                                                             │
│  ALERTAS_TELEGRAM.md        │ ~200  │  5   │ ⭐☆☆☆☆ (Simples)           │
│  └─ Documentação completa   │       │      │ [como usar, setup]            │
│                                                                             │
│  Modificações dashboard.py  │ ~200  │  3   │ ⭐⭐☆☆☆ (Simples)           │
│  └─ Sidebar para alertas    │       │      │ [integração UI]               │
│                                                                             │
│  TOTAL NOVO CÓDIGO          │~1600  │ 1-5  │ ⭐⭐⭐☆☆ (Médio/facível)    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
                    ESTRUTURA DE TRABALHO POR FASE
═══════════════════════════════════════════════════════════════════════════════

FASE 1: SETUP TELEGRAM
╔════════════════════════════════════════════════════════════════════════════╗
║ 1. Criar bot no Telegram (@BotFather)                                    ║
║    └─ Receber: TOKEN_TELEGRAM                                           ║
║                                                                          ║
║ 2. Testar envio básico                                                  ║
║    └─ utils_telegram.py: v0.1                                           ║
║    └─ Script teste: test_telegram_basic.py                              ║
║                                                                          ║
║ 3. Guardar TOKEN em config                                              ║
║    └─ .env ou config/alertas_config.json                                ║
║                                                                          ║
║ Critério de sucesso: ✅ Mensagem recebida no Telegram                    ║
╚════════════════════════════════════════════════════════════════════════════╝

FASE 2: DATABASE LOCAL
╔════════════════════════════════════════════════════════════════════════════╗
║ 1. Criar schema SQLite                                                   ║
║    └─ table: alertas (id, titulo, ufs, palavras_chave, etc)             ║
║                                                                          ║
║ 2. Funções CRUD em utils_telegram.py                                    ║
║    ├─ criar_alerta()                                                    ║
║    ├─ listar_alertas()                                                  ║
║    ├─ atualizar_alerta()                                                ║
║    ├─ deletar_alerta()                                                  ║
║    └─ buscar_alerta_por_id()                                            ║
║                                                                          ║
║ 3. Testes database                                                      ║
║    └─ test_alertas.py (Fase 2 tests)                                    ║
║                                                                          ║
║ Critério de sucesso: ✅ CRUD funções 100% funcionais e testadas         ║
╚════════════════════════════════════════════════════════════════════════════╝

FASE 3: INTERFACE DASHBOARD
╔════════════════════════════════════════════════════════════════════════════╗
║ 1. Novo Sidebar menu item: "🔔 ALERTAS"                                 ║
║    │                                                                     ║
║    ├─ Tab 1: Criar novo alerta                                          ║
║    │  └─ Form: Título, UFs dropdown, Palavras-chave, chat_id           ║
║    │  └─ Botão: "Criar Alerta"                                          ║
║    │  └─ Botão: "Testar" (enviar sample via Telegram)                   ║
║    │                                                                     ║
║    ├─ Tab 2: Meus alertas                                               ║
║    │  └─ Tabela com alertas criados                                     ║
║    │  └─ Botão para ativar/desativar                                    ║
║    │  └─ Botão para deletar                                             ║
║    │                                                                     ║
║    └─ Tab 3: Estatísticas                                               ║
║       └─ Total alertas criados                                          ║
║       └─ Última execução do monitor                                     ║
║       └─ Total de mensagens enviadas                                    ║
║                                                                          ║
║ 2. Testes UI                                                            ║
║    └─ Verificar que form salva em DB                                    ║
║    └─ Verificar que botão test envia msg                                ║
║    └─ Verificar que lista mostra alertas corretos                       ║
║                                                                          ║
║ Critério de sucesso: ✅ UI funcional, dados salvos em DB, msg enviada  ║
╚════════════════════════════════════════════════════════════════════════════╝

FASE 4: MONITOR SCRIPT
╔════════════════════════════════════════════════════════════════════════════╗
║ monitor_alertas.py - executar a cada 5 minutos (cron/TaskScheduler)      ║
║                                                                          ║
║ 1. Ler arquivo de controle (last_run.txt ou DB)                         ║
║    └─ Obter: último ID de licitação processado                          ║
║                                                                          ║
║ 2. Carregar dados/licitacoes.csv                                        ║
║    └─ Filtrar: linhas com ID > last_run                                 ║
║                                                                          ║
║ 3. Buscar alertas ativos no DB                                          ║
║    └─ SELECT * FROM alertas WHERE ativo=1                               ║
║                                                                          ║
║ 4. Para cada alerta:                                                    ║
║    ├─ Filtrar licitações por UF                                         ║
║    ├─ Filtrar por palavras-chave                                        ║
║    ├─ Se encontrou (count > 0):                                         ║
║    │  ├─ Formatar mensagem HTML                                         ║
║    │  ├─ Enviar via TelegramAlerter                                     ║
║    │  └─ Log: "Alerta enviado para {telegram_id}"                       ║
║    └─ Log: status de cada alerta                                        ║
║                                                                          ║
║ 5. Atualizar arquivo de controle                                        ║
║    └─ Novo ID = max(ID processados)                                     ║
║                                                                          ║
║ 6. Log tudo em logs/alertas.log                                         ║
║    └─ Timestamp, ID das licitações, UFs, etc                            ║
║                                                                          ║
║ Critério de sucesso: ✅ Script roda sem erros, checa todos alert, envia ║
╚════════════════════════════════════════════════════════════════════════════╝

FASE 5: TESTES E DOCS
╔════════════════════════════════════════════════════════════════════════════╗
║ test_alertas.py - Criar 20+ testes                                      ║
║                                                                          ║
║ Testes esperados:                                                        ║
║  ✅ test_criar_alerta()                                                  ║
║  ✅ test_listar_alertas()                                                ║
║  ✅ test_deletar_alerta()                                                ║
║  ✅ test_filtro_uf()                                                     ║
║  ✅ test_filtro_palavras_chave()                                         ║
║  ✅ test_formatar_mensagem_telegram()                                    ║
║  ✅ test_monitor_detecta_novo_edital()                                   ║
║  ✅ test_telegram_send_mock()                                            ║
║  ... (e mais 12+)                                                        ║
║                                                                          ║
║ ALERTAS_TELEGRAM.md - Documentação de uso                               ║
║  ├─ Como criar um alerta                                                ║
║  ├─ Como testar                                                         ║
║  ├─ Como agendar monitor_alertas.py                                     ║
║  ├─ Troubleshooting                                                     ║
║  └─ Exemplos práticos                                                   ║
║                                                                          ║
║ Critério de sucesso: ✅ 20+ testes PASS, docs completas                 ║
╚════════════════════════════════════════════════════════════════════════════╝

═══════════════════════════════════════════════════════════════════════════════
                        PASSO A PASSO RESUMIDO
═══════════════════════════════════════════════════════════════════════════════

DIA 1 (Você):
├─ 09:00 - Ler PROMPT_ESPECIALISTA_ALERTAS_TELEGRAM.md (30 min)
├─ 09:30 - Setup ambiente: pip install python-telegram-bot (15 min)
├─ 09:45 - FASE 1: Setup Telegram (30 min)
│  └─ Bot criado, TOKEN obtido, teste básico funciona
├─ 10:15 - FASE 2: Database (45 min)
│  └─ SQLite schema criado, CRUD testado
├─ 11:00 - PAUSA (15 min)
├─ 11:15 - FASE 3: Dashboard (1 hour)
│  └─ Sidebar "ALERTAS" funcional, UI completa
├─ 12:15 - ALMOÇO (1 hour)
├─ 13:15 - FASE 4: Monitor (45 min)
│  └─ Script detecta editais, envia via Telegram
├─ 14:00 - FASE 5: Testes + Docs (30 min)
│  └─ 20+ testes passando, documentação pronta
└─ 14:30 - FIM ✅ (Entrega realizada!)

═══════════════════════════════════════════════════════════════════════════════
                    CHECKLIST FINAL DE VALIDAÇÃO
═══════════════════════════════════════════════════════════════════════════════

ANTES DE COMEÇAR:
  □ Projeto recebido
  □ Venv ativo
  □ requirements.txt instalado
  □ dashboard.py roda (localhost:8501)
  □ pytest tests/ = 46/46 PASS

DURANTE IMPLEMENTAÇÃO:
  □ FASE 1: Bot Telegram funcionando
  □ FASE 2: SQLite com dados de teste
  □ FASE 3: UI na sidebar
  □ FASE 4: Monitor enviando mensagens
  □ FASE 5: Testes com cobertura

ENTREGA FINAL:
  □ Todos os arquivos criados
  □ 20+ testes PASS (test_alertas.py)
  □ Dashboard atualizado
  □ Documentação completa
  □ Zero erros em logging
  □ Test end-to-end com sucesso
  □ Pronto para produção

═══════════════════════════════════════════════════════════════════════════════
                            BOA SORTE! 🚀
═══════════════════════════════════════════════════════════════════════════════

Você tem tudo que precisa!
Tempo estimado: 3h 45 min (com margem para debugging)
Complexidade média: ⭐⭐⭐☆☆

COMECE LENDO:
→ PROMPT_ESPECIALISTA_ALERTAS_TELEGRAM.md ←

Quando terminar:
✅ Projeto 2.1 com Alertas Telegram funcional!

═══════════════════════════════════════════════════════════════════════════════
