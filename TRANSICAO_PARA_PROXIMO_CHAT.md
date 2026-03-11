╔══════════════════════════════════════════════════════════════════════════════╗
║                  INSTRUÇÕES DE TRANSIÇÃO - PRÓXIMO CHAT                      ║
║                                                                              ║
║        Como continuar o desenvolvimento em outro chat                       ║
╚══════════════════════════════════════════════════════════════════════════════╝

📋 GUIA PASSO A PASSO
═══════════════════════════════════════════════════════════════════════════════

PASSO 1: Preparing Para Novo Chat
───────────────────────────────────────────────────────────────────────────────

❌ NÃO ESQUEÇA:
  □ Copiar pasta inteira: c:\licitacoes_pncp
  □ Incluir todos os arquivos (CSV, testes, documentação)
  □ Incluir virtual env (venv/)
  □ Incluir git history (se usando git)

✅ ARQUIVOS IMPORTANTES:
  □ dashboard.py (arquivo principal)
  □ dados/licitacoes.csv (dados de teste)
  □ requirements.txt (dependências)
  □ utils_uf.py (validação)
  □ Todos os test_*.py (testes)
  □ Documentação em *.md

📝 ARQUIVOS PARA PASSAR AO PRÓXIMO ESPECIALISTA:
  □ PROMPT_ESPECIALISTA_ALERTAS_TELEGRAM.md (COMPLETO - passar este!)
  □ PROMPT_CURTO_ALERTAS.txt (resumido - copiar/colar)
  □ STATUS_ATUAL_PROJETO.txt (criar abaixo)

═══════════════════════════════════════════════════════════════════════════════

PASSO 2: Abrir Novo Chat
───────────────────────────────────────────────────────────────────────────────

1. Criar novo chat (nova conversa/thread)
2. Deixar um resumo do projeto para context:

---COMEÇAR NOVO CHAT COM ISTO---

## Contexto do Projeto

Estou desenvolvendo um **Dashboard Streamlit** chamado "Radar de Licitações de TI".

### Status Atual (Fase 2 Completa)
✅ Cache fix implementado (TTL + hash-based invalidation)
✅ Links de edital para PNCP implementados
✅ 27 UFs carregando corretamente
✅ 46 testes unitários passando
✅ 2054 registros de teste distribuídos

### Próxima Tarefa (Fase 3)
Implementar **Alertas via Telegram** para notificar usuários sobre novas licitações.

**Documentação completa**: Ver arquivo `PROMPT_ESPECIALISTA_ALERTAS_TELEGRAM.md`

---FIM---

3. Cole o conteúdo de um desses arquivos como prompt:
   - **Opção A** (Básica): Cole o conteúdo de `PROMPT_CURTO_ALERTAS.txt`
   - **Opção B** (Completa): Cole o conteúdo de `PROMPT_ESPECIALISTA_ALERTAS_TELEGRAM.md`

═══════════════════════════════════════════════════════════════════════════════

PASSO 3: Entregar Contexto Completo
───────────────────────────────────────────────────────────────────────────────

Passe estes arquivos para o novo especialista:

ESSENCIAL:
  ✅ PROMPT_ESPECIALISTA_ALERTAS_TELEGRAM.md (tudo que precisa saber)
  ✅ dashboard.py (código atual)
  ✅ requirements.txt (dependências)
  ✅ dados/licitacoes.csv (dados de teste)

DOCUMENTAÇÃO:
  ✅ SOLUCAO_CACHE_STREAMLIT.md (como já foi feito)
  ✅ IMPLEMENTACAO_LINKS_EDITAL.md (contexto anterior)
  ✅ GUIA_VERIFICACAO_RAPIDA.md (como usar)
  ✅ test_*.py (exemplos de testes)

═══════════════════════════════════════════════════════════════════════════════

PASSO 4: Estrutura do Novo Chat
───────────────────────────────────────────────────────────────────────────────

Primeira mensagem do novo chat deve incluir:

1. Título claro
   "Implementar Alertas via Telegram - Dashboard Radar Licitações TI"

2. Contexto resumido
   "Projeto Streamlit com 2054 registros, 27 UFs, dashboard completo.
    Adicionar notificações via Telegram para novas licitações."

3. Anexar/colar prompt
   Cole o conteúdo completo de PROMPT_ESPECIALISTA_ALERTAS_TELEGRAM.md

4. Deixar espaço para especialista trabalhar

═══════════════════════════════════════════════════════════════════════════════

PASSO 5: Transição de Conhecimento
───────────────────────────────────────────────────────────────────────────────

Informações-chave para passar:

ESTRUTURA PROJETO:
  └─ c:\licitacoes_pncp/
     ├─ dashboard.py (750+ linhas, Streamlit)
     ├─ utils_uf.py (Validação de UF)
     ├─ dados/
     │  └─ licitacoes.csv (2054 registros)
     ├─ tests/
     │  ├─ test_filtros.py (22 testes)
     │  └─ test_coleta.py (24 testes)
     ├─ requirements.txt
     ├─ venv/ (virtual env Python 3.10)
     └─ [muitos docs *.md]

PADRÕES DE CÓDIGO:
  - Python 3.10 (type hints recomendados)
  - Logging via Python logging module
  - Testes com pytest
  - Documentação em Markdown

CONVENÇÕES:
  - Variáveis em português (compatível com função existente)
  - Funções em português (ex: normalizar_uf, carregar_dados)
  - Comentários em português
  - Docstrings em português

═══════════════════════════════════════════════════════════════════════════════

PASSO 6: Checklist de Início
───────────────────────────────────────────────────────────────────────────────

Novo especialista deve verificar:

[ ] Arquivos do projeto recebidos
[ ] requirements.txt revisado
[ ] Virtual env ativo
[ ] Dashboard.py rodando sem erros
[ ] Testes existentes passando
[ ] Dados (CSV) acessíveis
[ ] PROMPT_ESPECIALISTA_ALERTAS_TELEGRAM.md compreendido
[ ] Perguntas sobre contexto respondidas
[ ] Pronto para começar implementação

═══════════════════════════════════════════════════════════════════════════════

CRONOGRAMA ESTIMADO PARA PRÓXIMA FASE
═══════════════════════════════════════════════════════════════════════════════

TOTAL: ~3-4 horas de trabalho

FASE 1: Setup (30 min)
└─ Telegram bot + Python libs

FASE 2: Backend (45 min)
└─ utils_telegram.py + database

FASE 3: Interface (1 hora)
└─ Dashboard UI para configuração

FASE 4: Monitoramento (45 min)
└─ monitor_alertas.py script

FASE 5: Testes + Docs (30 min)
└─ Testes + Documentação

═══════════════════════════════════════════════════════════════════════════════

DICAS IMPORTANTES
═══════════════════════════════════════════════════════════════════════════════

✅ FAZER:
  ✓ Ler PROMPT_ESPECIALISTA_ALERTAS_TELEGRAM.md inteiro ANTES de começar
  ✓ Entender a estrutura de dados do projeto
  ✓ Rodar os testes existentes para validar ambiente
  ✓ Usar os padrões já estabelecidos
  ✓ Manter logging detalhado
  ✓ Testar end-to-end (nova lic → Telegram)

❌ NÃO FAZER:
  ✗ Modificar código existente sem necessidade
  ✗ Quebrar testes passando
  ✗ Mudar estrutura de dados do CSV
  ✗ Adicionar dependências sem documentar
  ✗ Implementar sem testes
  ✗ Esquecer de documentação

═══════════════════════════════════════════════════════════════════════════════

CONTATO/HANDOFF
═══════════════════════════════════════════════════════════════════════════════

Se o novo especialista tiver dúvidas:

1. Revisar PROMPT_ESPECIALISTA_ALERTAS_TELEGRAM.md
2. Revisar código existente em dashboard.py
3. Revisar exemplos de testes em test_*.py
4. Executar: streamlit run dashboard.py (localhost:8501)
5. Executar: pytest tests/ (validar ambiente)

═══════════════════════════════════════════════════════════════════════════════

VERSIONING
═══════════════════════════════════════════════════════════════════════════════

Versão ATUAL:  2.0 (com cache fix + links)
Versão PRÓXIMA: 2.1 (com alertas Telegram)

Ao terminar alertas:
  └─ Atualizar para v2.1
  └─ Criar tag git (git tag v2.1)
  └─ Documentar mudanças (CHANGELOG)

═══════════════════════════════════════════════════════════════════════════════

✅ STATUS FINAL PARA TRANSIÇÃO
═══════════════════════════════════════════════════════════════════════════════

[✅] Chat 1: Cache fix + Links (COMPLETO)
[🔜] Chat 2: Alertas Telegram (PRÓXIMO)
[⏳] Chat 3: Melhorias futuras (TBD)

Projeto está em bom estado para transição:
✅ Código limpo e documentado
✅ Testes passando (46/46)
✅ Estrutura clara
✅ Próximas features bem definidas
✅ Prompt detalhado pronto

═══════════════════════════════════════════════════════════════════════════════

🎯 RESUMO EM UMA LINHA
─────────────────────────────────────────────────────────────────────────────

"Radar de Licitações TI é um dashboard Streamlit com cache fix + links de edital.
Próximo passo: alertas via Telegram. Tudo documentado. Pronto para começar!"

═══════════════════════════════════════════════════════════════════════════════

Data: 07/03/2026
Status: ✅ Pronto para Transição
Arquivo: TRANSICAO_PARA_PROXIMO_CHAT.md
Próxima Feature: Alertas Telegram
Tempo Estimado: 3-4 horas

═══════════════════════════════════════════════════════════════════════════════
