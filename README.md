# 📡 RADAR DE LICITAÇÕES DE TI - VERSÃO 1.0

> Sistema profissional, automatizado e robusto de monitoramento de licitações de software e tecnologia do PNCP

![Status](https://img.shields.io/badge/Status-Ativo-green) ![Python](https://img.shields.io/badge/Python-3.10+-blue) ![Windows](https://img.shields.io/badge/Windows-10%2B-blue)

## 🎯 O Que É?

Um **monitor automático** que identifica, coleta e analisa oportunidades governamentais de **software, cloud, dados e infraestrutura de TI** publicadas no Portal Nacional de Contratações Públicas (PNCP).

## ✨ O Que Você Consegue Fazer

✅ Descobrir **oportunidades de TI** governamentais  
✅ **Monitorar automaticamente** todos os dias  
✅ Analisar com **dashboard interativo**  
✅ Gerar **relatórios em Excel**  
✅ Comparar **valores e tendências**  
✅ Acompanhar **órgãos estratégicos**  

---

## 🚀 Comece em 5 Minutos

```powershell
# 1. PowerShell como Admin
# 2. Navegue ao projeto
cd C:\licitacoes_pncp

# 3. Ative ambiente
.\venv\Scripts\Activate.ps1

# 4. Instale (primeira vez)
pip install -r requirements.txt

# 5. Coleta
python pncp_radar_ti_plus.py

# 6. Dashboard
streamlit run dashboard.py
```

👉 **Veja [INICIO_RAPIDO.md](INICIO_RAPIDO.md) para instruções detalhadas**

---

## 📚 Documentação Rápida
```

### 2. Primeira Execução (Coleta de Dados)
```powershell
python pncp_radar_ti_plus.py
```

### 3. Abrir Dashboard
```powershell
streamlit run dashboard.py
```

**Pronto!** O dashboard abrirá automaticamente em http://localhost:8501

---

## 📋 Estrutura do Projeto

```
licitacoes_pncp/
├── pncp_radar_ti_plus.py       # Script principal de coleta
├── dashboard.py                # Dashboard Streamlit
├── requirements.txt            # Dependências Python
├── INSTRUCOES.md              # Guia completo de uso
├── README.md                  # Este arquivo
├── executar_coleta.bat        # Script para Windows
├── iniciar_dashboard.bat       # Script para Dashboard
├── dados/
│   └── licitacoes.csv         # Dados exportados (CSV)
├── radar_licitacoes_TI_PRO.xlsx    # Dados exportados (Excel)
└── radar_state.json           # Metadados da execução
```

---

## 🎯 Campos de Dados

Cada licitação coletada contém:

| Campo | Descrição |
|-------|-----------|
| `orgao` | Nome do órgão público contratante |
| `objeto` | Descrição completa da licitação |
| `valor_estimado` | Valor em reais (R$) |
| `data_publicacao` | Data em que foi publicada |
| `uf` | Estado (sigla) |
| `municipio` | Município onde será contratado |
| `numero_edital` | Identificador único da licitação |
| `modalidade` | Tipo de licitação (pregão, concorrência, etc) |
| `status` | Status atual da licitação |

---

## 🎨 Dashboard - Análises Disponíveis

### 📊 Abas de Visualização

1. **🏛️ Órgãos**
   - Top 15 órgãos que mais liceitam TI
   - Top 15 órgãos por valor total

2. **🗺️ Estados**
   - Distribuição de licitações por estado
   - Ranking dos top 10 estados

3. **💰 Valores**
   - Distribuição por faixa de valor
   - Top 10 maiores licitações

4. **📅 Timeline**
   - Publicações ao longo do tempo
   - Distribuição por dia da semana
   - Modalidades de licitação

5. **📋 Dados**
   - Tabela completa de licitações
   - Busca rápida por palavra
   - Download em CSV

---

## 🔍 Palavras-Chave Monitoradas

O sistema filtra automaticamente licitações que contenham:

- `software`
- `sistema`
- `tecnologia`, `tecnológico`
- `informática`, `informação`
- `desenvolvimento`
- `cloud`, `nuvem`
- `api`
- `dados`, `banco de dados`
- `ti`, `TI`
- `aplicativo`
- `licença`, `licenciamento`
- `infraestrutura`
- `rede`
- `segurança`
- `python`, `java`, `csharp`, `nodejs`
- `docker`, `kubernetes`
- `aws`, `azure`, `gcp`

---

## 📊 Exemplo de Uso

### Cenário 1: Empresa de Software
```
1. Executar coleta diariamente
2. Filtrar por "software" + "desenvolvimento"
3. Analisar órgãos que mais contratam
4. Identificar oportunidades de negócio
```

### Cenário 2: Consultor de TI
```
1. Acompanhar licitações da sua região
2. Importar dados em Excel para análise
3. Criar propostas com base nas demandas
4. Monitorar concorrência
```

### Cenário 3: Entidade de Governo
```
1. Analisar gastos em TI
2. Benchmarking com outros órgãos
3. Justificar investimentos
4. Planejar próximas contratações
```

---

## ⚙️ Configurações

Todas as configurações estão no topo do arquivo `pncp_radar_ti_plus.py`:

```python
MAX_LICITACOES = 5000              # Máx de registros a coletar
TEMPO_ESPERA_ENTRE_REQUISICOES = 1 # Segundos entre chamadas
TIMEOUT_REQUISICAO = 120           # Timeout em segundos
MAX_TENTATIVAS = 5                 # Tentativas em caso de erro
DIAS_ATRAS = 7                     # Dias retroativos
```

---

## 🔄 Automação com Windows Task Scheduler

### Setup Automático (recomendado)

1. Abra PowerShell como **Administrador**

2. Execute este comando:
```powershell
# Agendar execução diária às 07:00
$Principal = New-ScheduledTaskPrincipal -UserID "DOMAIN\USERNAME" -LogonType ServiceAccount -RunLevel Highest

$Trigger = New-ScheduledTaskTrigger -Daily -At 7:00AM

$Action = New-ScheduledTaskAction -Execute "C:\Python311\python.exe" `
  -Argument "C:\licitacoes_pncp\pncp_radar_ti_plus.py" `
  -WorkingDirectory "C:\licitacoes_pncp"

Register-ScheduledTask -TaskName "Radar Licitações TI" `
  -Principal $Principal -Trigger $Trigger -Action $Action -Force
```

3. Para verificar se foi criado:
```powershell
Get-ScheduledTask -TaskName "Radar Licitações TI"
```

### Execução Manual
Use os scripts `.bat` inclusos:
- `executar_coleta.bat` - Executar coleta de dados
- `iniciar_dashboard.bat` - Abrir dashboard

---

## 🛠️ Requisitos de Sistema

- **SO:** Windows 10/11 (ou Linux/macOS)
- **Python:** 3.10 ou superior
- **RAM:** Mínimo 2GB (4GB+ recomendado)
- **Internet:** Conexão stable (API PNCP online)
- **Privilégios:** Administrador (para Task Scheduler)

---

## 📦 Dependências

| Pacote | Versão | Uso |
|--------|--------|-----|
| `requests` | >=2.31 | Requisições HTTP para API |
| `pandas` | >=2.0 | Processamento e exportação de dados |
| `openpyxl` | >=3.10 | Geração de arquivos Excel |
| `streamlit` | >=1.28 | Framework para dashboard |
| `plotly` | >=5.17 | Gráficos interativos |

---

## 🚨 Tratamento de Erros

O sistema trata automaticamente:

✅ **HTTP 400** - Parâmetros inválidos  
✅ **HTTP 500** - Erro do servidor (com retry)  
✅ **Timeout** - Requisição demorada  
✅ **ConnectionError** - Falha de conexão  
✅ **JSONDecodeError** - Resposta inválida  
✅ **Duplicatas** - Removidas automaticamente  
✅ **Páginas vazias** - Encerram paginação  

---

## 📈 Performance

| Métrica | Valor |
|---------|-------|
| Tempo primeira execução | 10-15 minutos |
| Próximas execuções | 2-5 minutos |
| Máx de registros | 5.000 |
| Período de busca | 7 dias |
| Tentativas em erro | 5 |
| Timeout | 120 segundos |

---

## 💡 Dicas de Uso

1. **Primeira execução é a mais lenta**
   - API precisa buscar muitos dados
   - Deixe completar sem interrupções

2. **Não execute manualmente frequentemente**
   - Máximo 1x a cada 5 minutos
   - Respeite os limites da API PNCP

3. **Use os filtros do dashboard**
   - Reduz processamento de dados
   - Melhora a performance

4. **Monitore o arquivo `radar_state.json`**
   - Confirma última execução bem-sucedida
   - Quantidade de registros processados

5. **Backup dos dados**
   - Salve periodicamente os arquivos Excel
   - Mantenha histórico para análise de tendências

---

## 📞 Troubleshooting

### ❌ "ModuleNotFoundError: No module named 'requests'"
```bash
pip install --upgrade -r requirements.txt
```

### ❌ "ConnectionError" no PNCP
- Verifique internet
- Aguarde alguns minutos
- Tente novamente

### ❌ Arquivo Excel já aberto
- Feche o arquivo antes de executar
- Sistema não consegue sobrescrever

### ❌ Task Scheduler não executa
- Abra como Administrador
- Marque "Executar com maiores permissões"

### ❌ Dashboard não abre
- Pressione Ctrl+C
- Execute novamente: `streamlit run dashboard.py`

---

## 📚 Documentação Adicional

Para instruções completas, consulte:
- 📄 [INSTRUCOES.md](INSTRUCOES.md) - Guia passo a passo
- 📊 [API PNCP](https://pncp.gov.br/api/) - Documentação oficial
- 🎓 [Streamlit Docs](https://docs.streamlit.io/)

---

## 📋 Checklist Final

- [ ] Python 3.10+ instalado
- [ ] `pip install -r requirements.txt` executado
- [ ] Primeira coleta completada
- [ ] Dashboard aberto com sucesso
- [ ] Arquivos Excel/CSV gerados
- [ ] Filtros testados no dashboard
- [ ] Task Scheduler configurado (opcional)

---

## 🎯 Roadmap Futuro

- [ ] Notificações por email
- [ ] Integração Telegram/WhatsApp
- [ ] API própria para integrações
- [ ] Análise de trending topics
- [ ] Previsão de licitações
- [ ] Histórico de licitações
- [ ] Análise de concorrência

---

## ✅ Suporte

Este sistema foi desenvolvido como **solução completa e profissional** para monitoramento de licitações de TI.

**Faça melhor uso da plataforma:**
1. Execute regularmente (diariamente)
2. Analise tendências ao longo do tempo
3. Use filtros para análises específicas
4. Exporte dados para ferramentas de BI

---

## 📄 Licença

**MIT License** - Livre para uso comercial e pessoal

**Fonte de Dados:** Portal Nacional de Contratações Públicas (PNCP)  
Dados públicos do Governo Federal Brasileiro

---

## 👨‍💻 Desenvolvido com ❤️

**Radar de Licitações de TI**  
Sistema automático para oportunidades de TI no Brasil

Última atualização: **06/03/2026**

---

## 📊 Dados de Exemplo

Uma execução típica retorna:

```
Total de licitações verificadas: 2.847
Licitações de TI encontradas: 356
Total de órgãos contratantes: 89
Total de estados: 25
Valor total das licitações: R$ 1.245.678.900,00
Valor médio por licitação: R$ 3.498.535,11

Top Órgãos:
1. Ministério da Defesa - 45 licitações
2. Caixa Econômica Federal - 38 licitações
3. SERPRO - 32 licitações
4. TSE - 29 licitações
5. Bank Central - 27 licitações
```

---

**Aproveite essas oportunidades! 🚀**
