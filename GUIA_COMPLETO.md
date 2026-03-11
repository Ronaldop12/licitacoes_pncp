# 📡 GUIA COMPLETO - RADAR DE LICITAÇÕES DE TI

## 🎯 Visão Geral

O **Radar de Licitações de TI** é um sistema de monitoramento automático que coleta, filtra e analisa licitações de software e tecnologia publicadas no **Portal Nacional de Contratações Públicas (PNCP)** do Brasil.

### ✨ Características Principais

- ✅ Coleta automática de licitações de TI
- ✅ Filtro inteligente com 20+ palavras-chave de tecnologia
- ✅ Tratamento robusto de erros e retry automático
- ✅ Exportação em Excel com formatação profissional
- ✅ Dashboard interativo com Streamlit
- ✅ Automação com Windows Task Scheduler
- ✅ Relatórios estatísticos e análises

---

## 📋 Requisitos do Sistema

### Obrigatórios
- **Windows 10+** ou **Windows Server 2016+**
- **Python 3.10+**
- **Conexão com a internet**

### Instalação Recomendada
1. Python 3.10 ou 3.11
2. pip (gerenciador de pacotes Python)
3. Ambiente virtual (venv)

---

## 🚀 Instalação Rápida

### Passo 1: Instalar Python

1. Baixe em: [python.org](https://www.python.org/downloads/)
2. Durante a instalação, **marque**: "Add Python to PATH"
3. Escolha "Install Now"

Teste no PowerShell:
```powershell
python --version
pip --version
```

### Passo 2: Clonar/Baixar o Projeto

```powershell
cd C:\licitacoes_pncp
```

### Passo 3: Criar Ambiente Virtual

```powershell
# Criar ambiente virtual
python -m venv venv

# Ativar ambiente
.\venv\Scripts\Activate.ps1
```

> Se receber erro de permissão, execute:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

### Passo 4: Instalar Dependências

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

### Passo 5: Testar o Sistema

```powershell
python diagnosticar_sistema.py
```

---

## 🎮 Uso do Sistema

### Opção 1: Coleta Manual de Dados

Execute a coleta manualmente sempre que precisar:

```powershell
# Ativar ambiente virtual (se não estiver ativo)
.\venv\Scripts\Activate.ps1

# Executar coleta
python pncp_radar_ti_plus.py
```

**O que acontece:**
1. ✓ Conecta à API do PNCP
2. ✓ Coleta licitações dos últimos 7 dias
3. ✓ Filtra apenas licitações de TI
4. ✓ Remove duplicatas
5. ✓ Exporta para Excel e CSV
6. ✓ Gera relatório estatístico

**Duração:** 2-5 minutos (dependendo de quantas licitações encontrar)

**Saída:**
- `radar_licitacoes_TI_PRO.xlsx` - Dados em Excel com formatação
- `dados/licitacoes.csv` - Dados em CSV para dashboard
- `radar_state.json` - Estado da última execução

### Opção 2: Abrir o Dashboard Interativo

```powershell
# Ativar ambiente virtual (se não estiver ativo)
.\venv\Scripts\Activate.ps1

# Iniciar dashboard
streamlit run dashboard.py
```

O navegador abrirá automaticamente em: `http://localhost:8501`

**Recursos do Dashboard:**

- 📊 **Resumo Executivo**
  - Total de licitações encontradas
  - Número de órgãos e estados
  - Valor total e médio

- 🏛️ **Análise por Órgão**
  - Top 15 órgãos por quantidade
  - Top 15 órgãos por valor total

- 🗺️ **Análise por Estado**
  - Distribuição por estado (pie chart)
  - Ranking dos 10 estados principais

- 💰 **Análise de Valores**
  - Distribuição por faixa de valor
  - Top 10 maiores licitações

- 📅 **Timeline**
  - Publicações ao longo do tempo
  - Distribuição por dia da semana
  - Modalidades de licitação

- 📋 **Tabela de Dados**
  - Visualizar todos os registros
  - Múltiplas opções de ordenação
  - Exportar para CSV

### Opção 3: Automação com Windows Task Scheduler

Configure para executar automaticamente todos os dias:

#### Método Automático (Recomendado)

```powershell
# IMPORTANTE: Abra PowerShell como Administrador

cd C:\licitacoes_pncp

# Criar agendamento (padrão: 07:00 diários)
.\configurar_agendamento.ps1 -Acao criar

# Ver status
.\configurar_agendamento.ps1 -Acao status

# Testar execução
.\configurar_agendamento.ps1 -Acao testar
```

#### Método Manual

1. Pressione `Win + R`
2. Digite `taskschd.msc` e Enter
3. Clique em "Criar Tarefa Básica"
4. Preencha:
   - **Nome:** Radar_Licitacoes_TI
   - **Descrição:** Coleta automática de licitações TI do PNCP
5. Em Gatilhos: Escolha "Diário" às 07:00
6. Em Ações:
   - **Programa:** `C:\licitacoes_pncp\executar_radar.bat`
   - **Pasta inicial:** `C:\licitacoes_pncp`
7. Em Condições: Marque "Executar mesmo com bateria"
8. Clique OK

### Opção 4: Executar Manualmente com Arquivo Batch

```powershell
# Duplo clique em:
C:\licitacoes_pncp\executar_radar.bat
```

Ou via linha de comando:
```powershell
cd C:\licitacoes_pncp
.\executar_radar.bat
```

---

## 🔍 Interpretando os Dados

### Coluna por Coluna

| Coluna | Descrição | Exemplo |
|--------|-----------|---------|
| **Data** | Quando foi publicada no PNCP | 15/01/2026 |
| **Órgão** | Entidade que fez a licitação | Ministério da Saúde |
| **Objeto** | O que está sendo licitado | Sistema de gestão hospitalar |
| **Valor** | Orçamento estimado | R$ 500.000,00 |
| **UF** | Estado | SP, RJ, MG |
| **Município** | Cidade | São Paulo |
| **Número Edital** | ID único | 123456/2026 |

### Interpretando Gráficos

- **Top Órgãos:** Quem mais contrata TI
- **Por Estado:** Onde estão as oportunidades
- **Por Faixa de Valor:** Distribuição de investimentos
- **Timeline:** Tendência de publicações

---

## 📊 Exemplos de Filtros

### Filtrar por Estado
1. Abra o Dashboard
2. Na barra lateral, selecione apenas "SP"
3. Veja apenas licitações de São Paulo

### Filtrar por Valor
1. Defina Mínimo: R$ 100.000
2. Defina Máximo: R$ 1.000.000
3. Verá apenas licitações nessa faixa

### Filtrar por Órgão
1. Selecione os órgãos de interesse
2. Veja apenas suas publicações

---

## 🛠️ Solução de Problemas

### Problema: "Python não encontrado"
**Solução:**
```powershell
# Verifique a instalação
python --version

# Se não funcionar, adicione ao PATH:
# Control Panel > System > Advanced > Environment Variables
# Adicione: C:\Users\SEUNOME\AppData\Local\Programs\Python\Python311
```

### Problema: "Erro ao conectar à API"
**Solução:**
1. Verifique conexão com internet
2. Execute: `python diagnosticar_sistema.py`
3. Teste acesso manual: Abra no navegador:
   ```
   https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao?dataInicial=20260101&dataFinal=20260107&codigoModalidadeContratacao=1&pagina=1
   ```

### Problema: "Módulo não encontrado"
**Solução:**
```powershell
# Ativar ambiente virtual
.\venv\Scripts\Activate.ps1

# Reinstalar dependências
pip install --upgrade -r requirements.txt
```

### Problema: "Dashboard não abre"
**Solução:**
```powershell
# Verifique se os dados foram coletados
ls dados/licitacoes.csv

# Se não existir, execute: python pncp_radar_ti_plus.py

# Tente com IP explícito
streamlit run dashboard.py --server.address localhost
```

### Problema: "Erro de permissão no Task Scheduler"
**Solução:**
1. Abra PowerShell como Administrador
2. Execute: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
3. Tente novamente

---

## 📈 Cas de Uso Reais

### Para Software Houses
- Monitorar oportunidades de desenvolvimento
- Acompanhar competidores
- Identificar tendências de demanda

### Para Consultores
- Identificar clientes potenciais
- Análise de mercado
- Relatórios para propostas

### Para Órgãos Públicos
- Benchmark de preços
- Análise de demanda de TI
- Planejamento orçamentário

### Para Pesquisadores
- Análise de gastos públicos em TI
- Pesquisa de políticas públicas
- Análise de mercado de tecnologia

---

## 📝 Estrutura do Projeto

```
C:\licitacoes_pncp\
├── pncp_radar_ti_plus.py          # Script de coleta (principal)
├── dashboard.py                    # Dashboard Streamlit
├── diagnosticar_sistema.py        # Script de diagnóstico
├── executar_radar.bat              # Batch para execução Windows
├── configurar_agendamento.ps1     # Script PowerShell agendamento
├── requirements.txt                # Dependências Python
├── radar_licitacoes_TI_PRO.xlsx   # Dados exportados (Excel)
├── dados/
│   └── licitacoes.csv             # Dados exportados (CSV)
├── logs/
│   └── execucao_*.log             # Logs de execução
└── venv/                           # Ambiente virtual
    └── Scripts/
        ├── Activate.ps1           # Ativar venv (PowerShell)
        └── python.exe             # Python do venv
```

---

## ⚙️ Configurações Avançadas

### Alterar Período de Coleta

Edite `pncp_radar_ti_plus.py`:

```python
# Linha 50
DIAS_ATRAS = 7  # Mudar para quantos dias você quer
```

### Alterar Limite de Licitações

```python
# Linha 48
MAX_LICITACOES = 5000  # Reduzir para coletar menos
```

### Adicionar Palavras-Chave de Filtro

```python
# Linha 39-47
PALAVRAS_TI = [
    "software", "sistema", "tecnologia",
    # Adicione novas palavras aqui
    "sua_palavra_aqui",
]
```

### Alterar Horário de Automação

```powershell
# Criar agendamento às 14:00 (2 PM)
.\configurar_agendamento.ps1 -Acao criar -Hora "14:00"
```

---

## 📞 Suporte e Manutenção

### Verificar Logs

```powershell
# Ver últimos logs
Get-ChildItem logs/ -Name | Sort-Object | Select-Object -Last 5

# Ler um log específico
Get-Content logs/execucao_20260107_0700.log | Select-Object -Last 50
```

### Resetar Tudo

```powershell
# Remover agendamento
.\configurar_agendamento.ps1 -Acao remover

# Remover dados coletados
Remove-Item radar_licitacoes_TI_PRO.xlsx
Remove-Item dados/licitacoes.csv
Remove-Item radar_state.json

# Remover ambiente virtual
Remove-Item -Recurse venv
```

---

## 🎓 Dicas e Boas Práticas

1. ✅ Execute o diagnóstico regularmente
2. ✅ Verifique os logs para problemas
3. ✅ Mantenha a automação ligada
4. ✅ Exporte dados regularmente
5. ✅ Use filtros para análises específicas
6. ✅ Combine dados com outras ferramentas (Power BI, Tableau)

---

## 📜 Licença e Uso

Este sistema usa dados públicos do PNCP (Portal Nacional de Contratações Públicas).
- Dados são públicos
- API é oficial do governo brasileiro
- Uso é gratuito e irrestrito

---

## 🔗 Links Úteis

- [Portal PNCP](https://pncp.gov.br)
- [API PNCP - Documentação](https://pncp.gov.br/api/consulta)
- [Python.org](https://www.python.org)
- [Streamlit Docs](https://docs.streamlit.io)
- [Pandas Docs](https://pandas.pydata.org/docs)

---

## 📞 Contato e Suporte

Para dúvidas sobre:
- **API PNCP:** www.pncp.gov.br/contato
- **Python:** stackoverflow.com, python.org
- **Streamlit:** streamlit.io/community

---

**Versão:** 1.0  
**Data:** Janeiro 2026  
**Último Atualizado:** 07/01/2026
