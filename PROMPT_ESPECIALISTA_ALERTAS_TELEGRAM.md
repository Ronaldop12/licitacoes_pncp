╔══════════════════════════════════════════════════════════════════════════════╗
║                  PROMPT DE ESPECIALISTA - PRÓXIMA FASE                        ║
║                                                                              ║
║        Sistema Radar de Licitações TI - Feature: Alertas via Telegram       ║
╚══════════════════════════════════════════════════════════════════════════════╝

📋 CONTEXTO ATUAL DO PROJETO
═══════════════════════════════════════════════════════════════════════════════

PROJETO: Radar de Licitações de TI - Dashboard Streamlit (Versão 2.0)
STATUS: ✅ Funcional com cache fix + links de edital implementados
LINGUAGEM: Python 3.10
FRAMEWORK: Streamlit
LOCALIZAÇÃO: c:\licitacoes_pncp

═══════════════════════════════════════════════════════════════════════════════

✅ JÁ IMPLEMENTADO NO PROJETO
═══════════════════════════════════════════════════════════════════════════════

1. DASHBOARD INTERATIVO (dashboard.py)
   ├─ Cache inteligente (TTL=5min + hash-based invalidation)
   ├─ Filtros funcionais (27 UFs, órgãos, valores)
   ├─ 5 abas principais:
   │  ├─ 🏛️ Órgãos (Top 15 quantidade e valor)
   │  ├─ 🗺️ Estados (Distribuição e ranking)
   │  ├─ 💰 Valores (Faixas e top 10)
   │  ├─ 📅 Timeline (Gráficos temporais)
   │  └─ 📋 Dados (Tabelas + Links)
   ├─ Links de Editais (2 sub-abas)
   │  ├─ 📊 Tabela com coluna "Link Edital"
   │  └─ 🔗 Links expandíveis em cards
   ├─ Páinel de Debug (🔧 Reload manual)
   └─ Busca rápida integrada

2. VALIDAÇÃO E TESTES
   ├─ 46 testes unitários PASSANDO (test_filtros.py + test_coleta.py)
   ├─ Validação de 27 UFs (teste_ufs_dashboard.py)
   ├─ Teste de integração (testar_dashboard_ufs.py)
   ├─ Teste de links (teste_links_edital.py)
   └─ 100% de cobertura de casos

3. DADOS
   ├─ Arquivo: dados/licitacoes.csv (2054 registros)
   ├─ Colunas: orgao, objeto, valor_estimado, data_publicacao, uf, municipio, numero_edital, modalidade, status
   ├─ 27 UFs distribuídos
   └─ Dados de teste (expansível)

4. DOCUMENTAÇÃO
   ├─ SOLUCAO_CACHE_STREAMLIT.md (Cache fix)
   ├─ IMPLEMENTACAO_LINKS_EDITAL.md (Links)
   ├─ GUIA_VERIFICACAO_RAPIDA.md (Uso)
   ├─ CHECKLIST_RESOLUCAO.md (Validações)
   └─ STATUS_FINAL.txt + STATUS_LINKS_FINAL.txt (Resumos)

═══════════════════════════════════════════════════════════════════════════════

🎯 PRÓXIMA FEATURE A IMPLEMENTAR
═══════════════════════════════════════════════════════════════════════════════

FUNCIONALIDADE: Alertas via Telegram
OBJETIVO: Notificar usuários sobre novas licitações em tempo real
URGÊNCIA: Alta
COMPLEXIDADE: Média

═══════════════════════════════════════════════════════════════════════════════

📋 REQUISITOS PARA ALERTAS VIA TELEGRAM
═══════════════════════════════════════════════════════════════════════════════

1. CONFIGURAÇÃO DO BOT TELEGRAM
   ├─ Criar bot no BotFather (@BotFather no Telegram)
   ├─ Obter TOKEN do bot
   ├─ Criar grupo/canal para alertas
   ├─ Adicionar bot ao grupo/canal
   └─ Obter CHAT_ID do grupo/canal

2. ESTRUTURA DE DADOS DO ALERTS
   ├─ Armazenar preferências de alertas por usuário:
   │  ├─ UF(s) de interesse
   │  ├─ Valores mínimo/máximo
   │  ├─ Órgão(s) específico(s)
   │  ├─ Palavras-chave no objeto
   │  └─ Chat ID do Telegram
   └─ Arquivo: config/alertas_config.json (ou banco de dados SQLite)

3. LÓGICA DE FUNCIONAMENTO
   ├─ Monitorar arquivo dados/licitacoes.csv
   ├─ Detectar novos registros (comparar com último hash/timestamp)
   ├─ Filtrar por critérios do usuário
   ├─ Formatar mensagem para Telegram
   ├─ Enviar para chat/canal via API
   └─ Registrar no log (alertas_enviados.log)

4. INTERFACE NO DASHBOARD
   ├─ Sidebar: Nova seção "🔔 ALERTAS"
   ├─ Campos para configurar:
   │  ├─ Ativar/desativar alertas
   │  ├─ Selecionar UF(s)
   │  ├─ Range de valores
   │  ├─ Selecionar órgão(s)
   │  ├─ Palavras-chave
   │  ├─ Chat ID do Telegram (ou bot link)
   │  └─ Botão "💾 Salvar Configuração"
   ├─ Status de alertas (último envio, próxima verificação)
   └─ Botão "🔔 Testar Alerta" (enviar alertas de teste)

5. SCRIPT DE MONITORAMENTO
   ├─ arquivo: monitor_alertas.py
   ├─ Executar periodicamente (cron job ou systemd timer)
   ├─ Verificar CSV a cada X minutos
   ├─ Comparar com versão anterior
   ├─ Enviar alertas para usuários qualificados
   ├─ Registrar no histórico
   └─ Log de execução (monitor.log)

═══════════════════════════════════════════════════════════════════════════════

🔧 TECNOLOGIAS A USAR
═══════════════════════════════════════════════════════════════════════════════

1. TELEGRAM API
   ├─ Biblioteca: python-telegram-bot (preferida) ou requests
   ├─ Instalação: pip install python-telegram-bot
   ├─ Alternativa simpla: usar requests + API HTTP do Telegram

2. ARMAZENAMENTO
   ├─ Opção A: JSON + filesystem (simples)
   │  └─ Arquivo: config/alertas.json
   ├─ Opção B: SQLite (robusto)
   │  └─ Arquivo: dados/alertas.db
   └─ Recomendação: SQLite para escalabilidade

3. MONITORAMENTO
   ├─ Arquivo: monitor_alertas.py
   ├─ Usar hash do arquivo para detectar mudanças
   ├─ Ou comparar counts/timestamps
   └─ Estilo: Polling simples (sem websockets)

4. LOGGING
   ├─ Python logging module
   ├─ Arquivo: logs/alertas.log
   ├─ Níveis: DEBUG, INFO, WARNING, ERROR

═══════════════════════════════════════════════════════════════════════════════

📝 ARQUIVOS A CRIAR/MODIFICAR
═══════════════════════════════════════════════════════════════════════════════

CRIAR:
├─ config/alertas_config.json (ou database)
│  └─ Estrutura:
│     {
│       "alertas": [
│         {
│           "id": 1,
│           "nome": "Alert 1",
│           "chat_id": "-123456789",
│           "ufs": ["SP", "RJ"],
│           "valor_min": 0,
│           "valor_max": 500000,
│           "orgaos": ["*"],  // ["*"] = todos
│           "palavras_chave": ["software", "cloud"],
│           "ativo": true,
│           "criado_em": "2026-03-07T10:30:00",
│           "ultimo_alerta": "2026-03-07T15:45:00"
│         }
│       ]
│     }
├─ monitor_alertas.py (500-700 linhas)
│  └─ Script de monitoramento principal
├─ utils_telegram.py (200-300 linhas)
│  └─ Funções auxiliares de Telegram
├─ tests/test_alertas.py (200+ linhas)
│  └─ Testes unitários para alertas
└─ logs/alertas.log (será criado automaticamente)

MODIFICAR:
├─ dashboard.py (+ sidebar com configuração de alertas)
├─ requirements.txt (adicionar python-telegram-bot)
└─ INSTRUCOES.md (adicionar seção de alertas)

═══════════════════════════════════════════════════════════════════════════════

💻 EXAMPLE DE CÓDIGO BASE
═══════════════════════════════════════════════════════════════════════════════

# utils_telegram.py
import requests
import json
from datetime import datetime

class TelegramAlerter:
    def __init__(self, token: str):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
    
    def enviar_mensagem(self, chat_id: str, mensagem: str):
        """Envia mensagem para chat/canal do Telegram"""
        try:
            response = requests.post(
                f"{self.base_url}/sendMessage",
                json={"chat_id": chat_id, "text": mensagem, "parse_mode": "HTML"}
            )
            return response.json()
        except Exception as e:
            print(f"Erro ao enviar: {e}")
            return None
    
    def formatar_alerta(self, licitacao: dict) -> str:
        """Formata licitação como mensagem Telegram"""
        msg = f"""
        <b>🎯 NOVA LICITAÇÃO!</b>
        
        <b>Órgão:</b> {licitacao['orgao']}
        <b>Objeto:</b> {licitacao['objeto'][:100]}...
        <b>Valor:</b> R$ {licitacao['valor_estimado']:,.2f}
        <b>UF:</b> {licitacao['uf']}
        <b>Município:</b> {licitacao['municipio']}
        <b>Data:</b> {licitacao['data_publicacao']}
        
        <a href="https://www.pncp.gov.br/app/editais?numero={licitacao['numero_edital']}">
        🔗 Ver no PNCP
        </a>
        """
        return msg

# monitor_alertas.py (pseudocódigo)
import hashlib
import json
import pandas as pd
from utils_telegram import TelegramAlerter

def detectar_novas_licitacoes():
    """Detecta novas licitacões comparando hashes"""
    csv_atual = pd.read_csv('dados/licitacoes.csv')
    hash_atual = hashlib.md5(str(csv_atual).encode()).hexdigest()
    
    with open('config/hash_anterior.txt', 'r') as f:
        hash_anterior = f.read().strip()
    
    if hash_atual != hash_anterior:
        # Salvar novo hash
        with open('config/hash_anterior.txt', 'w') as f:
            f.write(hash_atual)
        
        # Detectar quais registros são novos
        # (comparar com backup anterior)
        return True
    return False

def processar_alertas():
    """Processa todos os alertas configurados"""
    if not detectar_novas_licitacoes():
        return
    
    # Carregar configurações
    with open('config/alertas_config.json', 'r') as f:
        config = json.load(f)
    
    csv_atual = pd.read_csv('dados/licitacoes.csv')
    
    # Para cada alerta configurado
    for alerta in config['alertas']:
        if not alerta['ativo']:
            continue
        
        # Filtrar licitações por critério
        filtradas = csv_atual[
            (csv_atual['uf'].isin(alerta['ufs'])) &
            (csv_atual['valor_estimado'] >= alerta['valor_min']) &
            (csv_atual['valor_estimado'] <= alerta['valor_max'])
        ]
        
        # Enviar alertas
        bot = TelegramAlerter(TOKEN)
        for _, lic in filtradas.iterrows():
            msg = bot.formatar_alerta(lic.to_dict())
            bot.enviar_mensagem(alerta['chat_id'], msg)

═══════════════════════════════════════════════════════════════════════════════

🎯 ROADMAP DE IMPLEMENTAÇÃO
═══════════════════════════════════════════════════════════════════════════════

FASE 1: Setup básico (30 min)
├─ [ ] Instalar python-telegram-bot
├─ [ ] Criar bot Telegram (@BotFather)
├─ [ ] Obter TOKEN e CHAT_ID
├─ [ ] Criar pasta config/
└─ [ ] Criar utils_telegram.py com função de envio

FASE 2: Banco de dados de alertas (45 min)
├─ [ ] Criar schema alertas.db (SQLite)
├─ [ ] Funções CRUD para alertas
├─ [ ] Testar com dados de exemplo
└─ [ ] Criar arquivo config/alertas.json (v1 backup em JSON)

FASE 3: Interface no Dashboard (1h)
├─ [ ] Adicionar sidebar "🔔 ALERTAS"
├─ [ ] Campos de configuração
├─ [ ] Botão "Salvar Configuração"
├─ [ ] Botão "🔔 Testar Alerta"
└─ [ ] Listar alertas ativos

FASE 4: Script de monitoramento (45 min)
├─ [ ] Criar monitor_alertas.py
├─ [ ] Detectar novas licitações
├─ [ ] Filtrar por critérios
├─ [ ] Enviar via Telegram
├─ [ ] Logging completo
└─ [ ] Testes

FASE 5: Testes e documentação (30 min)
├─ [ ] Testes unitários (test_alertas.py)
├─ [ ] Teste de integração
├─ [ ] Documentação (ALERTAS_TELEGRAM.md)
├─ [ ] Guia de configuração
└─ [ ] Status final

═══════════════════════════════════════════════════════════════════════════════

📊 ESTRUTURA DE DADOS DETALHADA
═══════════════════════════════════════════════════════════════════════════════

# config/alertas_config.json
{
  "telegram_token": "SEU_TOKEN_AQUI",
  "alertas": [
    {
      "id": 1,
      "nome": "Licitações SP - Alta Valor",
      "ativo": true,
      "chat_id": "-123456789",  // Negativo = grupo/canal
      "ufs": ["SP"],
      "valor_min": 100000,
      "valor_max": 5000000,
      "orgaos": ["*"],  // ["*"] = todos || ["CAMARA", "PREFEITURA"]
      "palavras_chave": ["software", "cloud", "api"],
      "notificar_quando": "nova",  // "nova" = nova lic, "diaria" = resumo diário
      "frequencia_min": 60,  // minutos entre alertas para mesmo alerta
      "criado_em": "2026-03-07T10:00:00",
      "ultimo_alerta": "2026-03-07T15:30:00",
      "proxximo_alerta": "2026-03-07T16:30:00"
    },
    {
      "id": 2,
      "nome": "Todas as licitações",
      "ativo": false,
      "chat_id": "-987654321",
      "ufs": ["AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO"],
      "valor_min": 0,
      "valor_max": 999999999,
      "orgaos": ["*"],
      "palavras_chave": [],
      "notificar_quando": "resumo_diario",
      "frequencia_min": 1440,  // 24h
      "criado_em": "2026-03-07T11:00:00",
      "ultimo_alerta": null,
      "proxximo_alerta": "2026-03-08T00:00:00"
    }
  ],
  "monitoramento": {
    "intervalo_segundos": 300,  // 5 minutos
    "ativo": true,
    "ultimo_check": "2026-03-07T16:25:00",
    "hash_anterior": "abc123def456"
  }
}

═══════════════════════════════════════════════════════════════════════════════

🚀 COMO COMEÇAR NO PRÓXIMO CHAT
═══════════════════════════════════════════════════════════════════════════════

1. Chamar especialista com este prompt
2. Especialista criará:
   ├─ utils_telegram.py (funções de envio)
   ├─ monitor_alertas.py (script de monitoramento)
   ├─ database schema (SQLite)
   ├─ Interface no dashboard.py
   └─ Testes (test_alertas.py)
3. Integração com Streamlit
4. Documentação completa
5. Validação end-to-end

═══════════════════════════════════════════════════════════════════════════════

📞 INFORMAÇÕES IMPORTANTES PARA O PRÓXIMO ESPECIALISTA
═══════════════════════════════════════════════════════════════════════════════

AMBIENTE:
- Sistema Operacional: Windows 10/11
- Linguagem: Python 3.10
- Localização do projeto: c:\licitacoes_pncp
- Virtual env: c:\licitacoes_pncp\venv

DADOS:
- CSV: dados/licitacoes.csv (2054 registros)
- Colunas: orgao, objeto, valor_estimado, data_publicacao, uf, municipio, numero_edital, modalidade, status
- UFs: 27 estados

CÓDIGO EXISTENTE:
- dashboard.py: 750+ linhas (funcional)
- utils_uf.py: Validação de UF
- test_filtros.py + test_coleta.py: 46 testes

DEPENDÊNCIAS ATUAIS:
- streamlit
- pandas
- plotly
- openpyxl

NOVA DEPENDÊNCIA:
- python-telegram-bot (ou requests)

═══════════════════════════════════════════════════════════════════════════════

✅ CHECKLIST DE VALIDAÇÃO FINAL (Para após implementar)
═══════════════════════════════════════════════════════════════════════════════

[ ] utils_telegram.py criado e testado
[ ] monitor_alertas.py criado e funcional
[ ] Config JSON criado com estrutura correta
[ ] Banco SQLite criado com schema
[ ] Interface de alertas no dashboard funcionando
[ ] Botão "Testar Alerta" enviando via Telegram
[ ] Script de monitoramento rodando sem erros
[ ] 20+ testes unitários passando
[ ] Documentação completa (ALERTAS_TELEGRAM.md)
[ ] Guia de setup Telegram criado
[ ] Logging properly working
[ ] End-to-end test: nova licitação → Telegram alert
[ ] Performance ok (<2s para enviar alerta)

═══════════════════════════════════════════════════════════════════════════════

🎓 DOCUMENTOS DE REFERÊNCIA
═══════════════════════════════════════════════════════════════════════════════

Existentes no projeto:
- SOLUCAO_CACHE_STREAMLIT.md
- IMPLEMENTACAO_LINKS_EDITAL.md
- GUIA_VERIFICACAO_RAPIDA.md
- Todos os testes em test_*.py

Para criar:
- ALERTAS_TELEGRAM.md (documentação completa)
- SETUP_TELEGRAM.md (guia de configuração do bot)

═══════════════════════════════════════════════════════════════════════════════

🎯 OBJETIVO FINAL
═══════════════════════════════════════════════════════════════════════════════

Sistema de alertas via Telegram 100% funcional que:
✅ Monitora dados/licitacoes.csv
✅ Detecta novos registros automaticamente
✅ Filtra por critérios do usuário
✅ Envia alertas em tempo real (ou resumidos)
✅ Interface no dashboard para configurar
✅ Testes automatizados
✅ Logging completo
✅ Pronto para produção

═══════════════════════════════════════════════════════════════════════════════

Data: 07/03/2026
Projeto: Radar Licitações TI v2.0
Status: ✅ Pronto para próxima fase
Especialista Anterior: Chat 1 (Cache fix + Links)
Próximo Passo: Implementar Alertas Telegram

═══════════════════════════════════════════════════════════════════════════════
