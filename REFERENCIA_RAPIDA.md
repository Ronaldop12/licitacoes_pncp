# 🚀 REFERÊNCIA RÁPIDA - Radar de Licitações de TI

## Primeiros Passos (5 minutos)

### 1️⃣ Setup Inicial
```powershell
# Opção A: Script automático (recomendado)
.\setup.bat

# Opção B: Manual
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2️⃣ Testar Sistema
```powershell
python testar_sistema.py
```

### 3️⃣ Executar Coleta
```powershell
# Opção A: Script direto
python pncp_radar_ti_plus.py

# Opção B: Usando .bat
.\executar_coleta.bat
```

### 4️⃣ Abrir Dashboard
```powershell
# Opção A: Streamlit direto
streamlit run dashboard.py

# Opção B: Usando .bat
.\iniciar_dashboard.bat
```

---

## Comandos Essenciais

| Tarefa | Comando |
|--------|---------|
| **Ativar ambiente** | `.\venv\Scripts\Activate.ps1` |
| **Instalar deps** | `pip install -r requirements.txt` |
| **Coletar dados** | `python pncp_radar_ti_plus.py` |
| **Dashboard** | `streamlit run dashboard.py` |
| **Testar sistema** | `python testar_sistema.py` |
| **Sair do ambiente** | `deactivate` |

---

## Troubleshooting Rápido

### ❌ "Python não encontrado"
```
✓ Instale em: https://www.python.org
✓ Marque: "Add Python to PATH"
✓ Reinicie PowerShell
```

### ❌ "ModuleNotFoundError"
```powershell
pip install --upgrade -r requirements.txt
```

### ❌ Erro de execução (Policy)
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### ❌ "API timeout"
```
✓ Aguarde alguns minutos
✓ Verifique internet
✓ Tente novamente depois
```

### ❌ "Acesso negado" ao salvar
```
✓ Feche o arquivo Excel aberto
✓ Aguarde e tente novamente
```

---

## Estrutura de Saída

```
📂 licitacoes_pncp/
├── 📄 radar_licitacoes_TI_PRO.xlsx    ← Dados em Excel
├── 📂 dados/
│   └── 📄 licitacoes.csv              ← Dados em CSV
└── 📄 radar_state.json                 ← Metadados
```

---

## Dashboard - Filtros Disponíveis

```
Estado: São Paulo, Rio de Janeiro, ...
Órgão: Ministério da Fazenda, SERPRO, ...
Valor: R$ 10.000 a R$ 5.000.000
```

---

## Automação Diária (Windows Task Scheduler)

```powershell
# Criar tarefa (PowerShell Administrador)
$Principal = New-ScheduledTaskPrincipal -UserID "$env:USERDOMAIN\$env:USERNAME" -LogonType ServiceAccount -RunLevel Highest

$Trigger = New-ScheduledTaskTrigger -Daily -At 7:00AM

$Action = New-ScheduledTaskAction -Execute "C:\Python311\python.exe" `
  -Argument "C:\licitacoes_pncp\pncp_radar_ti_plus.py" `
  -WorkingDirectory "C:\licitacoes_pncp"

Register-ScheduledTask -TaskName "Radar Licitações TI" `
  -Principal $Principal -Trigger $Trigger -Action $Action -Force

# Ver tarefas agendadas
Get-ScheduledTask | Where-Object {$_.TaskName -like "*Radar*"}

# Deletar tarefa
Unregister-ScheduledTask -TaskName "Radar Licitações TI" -Confirm:$false
```

---

## Visualizações Disponíveis

| Aba | Funçao |
|-----|--------|
| 🏛️ Órgãos | Quem mais licita TI |
| 🗺️ Estados | Onde estão as oportunidades |
| 💰 Valores | Tamanho das licitações |
| 📅 Timeline | Quando são publicadas |
| 📋 Dados | Tabela completa + Busca |

---

## Palavras-Chave Monitoradas

```
software, sistema, tecnologia, informática
desenvolvimento, cloud, nuvem, api, dados
ti, aplicativo, licença, infraestrutura, rede
segurança, banco de dados, python, java
csharp, nodejs, docker, kubernetes, aws, azure, gcp
```

---

## Métricas Principais

```
Total: Total de licitações encontradas
Órgãos: Quantidade de órgãos contratantes
Estados: Quantidade de estados com licitações
Valor Total: Soma de todos valores (R$)
Valor Médio: Média dos valores (R$)
```

---

## Configurações Personalizáveis

Edite no início do `pncp_radar_ti_plus.py`:

```python
MAX_LICITACOES = 5000              # Quantidade máxima
DIAS_ATRAS = 7                     # Período de busca
TEMPO_ESPERA_ENTRE_REQUISICOES = 1 # Segundos entre chamadas
MAX_TENTATIVAS = 5                 # Tentativas em caso de erro
TIMEOUT_REQUISICAO = 120           # Timeout em segundos
```

---

## Dados de Exemplo (por execução)

```
Licitações verificadas: ~2.847
Licitações de TI: ~356
Órgãos: ~89
Estados: ~25
Valor Total: ~R$ 1,2 bilhões
Tempo: 10-15 minutos (primeira) / 2-5 minutos (subsequentes)
```

---

## Links Úteis

- 📊 **PNCP:** https://pncp.gov.br
- 📚 **API PNCP:** https://pncp.gov.br/api/
- 🎓 **Streamlit:** https://streamlit.io
- 📈 **Plotly:** https://plotly.com
- 🐍 **Python:** https://python.org

---

## Suporte e Documentação

- 📖 **INSTRUCOES.md** - Guia completo (45 minutos de setup)
- 📋 **README.md** - Visão geral do projeto
- 🔬 **testar_sistema.py** - Validar ambiente
- 🧪 **API PNCP** - Endpoint oficial

---

## Checklist de Primeira Execução

- [ ] Python 3.10+ instalado
- [ ] `setup.bat` executado com sucesso
- [ ] `testar_sistema.py` passou todos os testes
- [ ] `pncp_radar_ti_plus.py` coletou dados (>0 registros)
- [ ] Arquivo Excel gerado: `radar_licitacoes_TI_PRO.xlsx`
- [ ] Arquivo CSV gerado: `dados/licitacoes.csv`
- [ ] Dashboard abriu no navegador
- [ ] Todos os filtros funcionam

---

## Próximas Ações

1. ✅ Setup concluído?
   → Agende execução diária no Task Scheduler

2. 📊 Analisando dados?
   → Use os filtros do dashboard

3. 💼 Monitorando oportunidades?
   → Prepare propostas baseado em filtros específicos

4. 🤖 Automação completa?
   → Configure email de alertas com VB Script

5. 📈 Histórico de análises?
   → Faça backup mensal dos CSV para análise de tendências

---

## Contatos Úteis

- **PNCP:** compras@planejamento.gov.br
- **Suporte:** Você mesmo! (Sistema sem dependências externas)

---

**Última atualização:** 06/03/2026
**Versão:** 1.0 - Professional Release
