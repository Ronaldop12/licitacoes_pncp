# 📡 Radar de Licitações de TI - PNCP

## Instruções de Execução Completas

### 🎯 Objetivo
Sistema automático que monitora oportunidades de software e tecnologia publicadas no Portal Nacional de Contratações Públicas (PNCP) do Brasil.

---

## 📋 Pré-Requisitos

### Sistema Operacional
- **Windows 10/11** (ou Linux/macOS com ajustes menores)
- **Python 3.10+** instalado

### Verificar Python
```powershell
python --version
```

Se não estiver instalado, baixe em: https://www.python.org/downloads/

---

## 🚀 Instalação (Primeira Vez)

### 1️⃣ Abrir PowerShell como Administrador

Clique com botão direito em **PowerShell** e selecione **Executar como administrador**.

### 2️⃣ Navegar para o diretório do projeto

```powershell
cd c:\licitacoes_pncp
```

### 3️⃣ Criar ambiente virtual (recomendado)

```powershell
python -m venv venv
```

### 4️⃣ Ativar ambiente virtual

```powershell
.\venv\Scripts\Activate.ps1
```

Se receber um erro de política de execução, execute:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 5️⃣ Instalar dependências

```powershell
pip install -r requirements.txt
```

---

## 💻 Executar o Sistema

### Opção 1: Coleta de Dados (Script Principal)

```powershell
python pncp_radar_ti_plus.py
```

**O que ele faz:**
- ✓ Coleta licitações dos últimos 7 dias
- ✓ Filtra apenas licitações de TI
- ✓ Remove duplicatas
- ✓ Exporta para `radar_licitacoes_TI_PRO.xlsx`
- ✓ Exporta para `dados/licitacoes.csv`
- ✓ Salva estatísticas em `radar_state.json`

**Tempo estimado:** 5-15 minutos (depende da API)

### Opção 2: Dashboard Interativo

```powershell
streamlit run dashboard.py
```

**Resultado:**
- Abre automaticamente no navegador (http://localhost:8501)
- Dashboard interativo com gráficos
- Filtros por Estado, Órgão, Valor
- Exportação de dados

---

## 📊 Saídas Geradas

### Arquivos Criados

| Arquivo | Descrição |
|---------|-----------|
| `radar_licitacoes_TI_PRO.xlsx` | Excel com todas as licitações formatadas |
| `dados/licitacoes.csv` | CSV para processamento/análise |
| `radar_state.json` | Metadados da última execução |

### Estrutura dos Dados

Cada licitação contém:
- **orgao** - Órgão público contratante
- **objeto** - Descrição da licitação
- **valor_estimado** - Valor em R$
- **data_publicacao** - Data de publicação
- **uf** - Estado (sigla)
- **municipio** - Município
- **numero_edital** - Identificador único
- **modalidade** - Tipo de licitação
- **status** - Status atual

---

## 🔄 Automatizar no Windows Task Scheduler

### Agendar execução diária às 07:00

#### 1️⃣ Abrir Task Scheduler
- Pressione `Win + R`
- Digite: `taskschd.msc`
- Pressione Enter

#### 2️⃣ Criar nova tarefa
1. Clique em **Criar Tarefa Básica**
2. Nome: `Radar Licitações TI`
3. Descrição: `Coleta diária de licitações de TI do PNCP`
4. Clique em **Próximo**

#### 3️⃣ Configurar agendamento
1. Selecione **Diária**
2. Início: Data/horário (ex: 2026-03-06 07:00)
3. Recorrência: 1 dia
4. Clique em **Próximo**

#### 4️⃣ Ação
1. Selecione **Iniciar um programa**
2. Programa: `C:\Python311\python.exe` (ou seu caminho)
3. Argumentos: `C:\licitacoes_pncp\pncp_radar_ti_plus.py`
4. Início em: `C:\licitacoes_pncp`
5. Clique em **Próximo**

#### 5️⃣ Finalizar
1. Marque "Executar com as maiores permissões"
2. Clique em **Concluir**

---

## 🛠️ Troubleshooting

### ❌ Erro: "ModuleNotFoundError"
```
Solução: Reinstale as dependências
pip install --upgrade -r requirements.txt
```

### ❌ Erro: "ConnectionError" ou timeout
```
Solução: A API PNCP pode estar indisponível
- Aguarde alguns minutos
- Verifique sua conexão de internet
- Tente novamente com: python pncp_radar_ti_plus.py
```

### ❌ Erro: "Acesso negado" ao salvar arquivo
```
Solução: Feche o arquivo Excel se estiver aberto
- Feche: radar_licitacoes_TI_PRO.xlsx
- Tente novamente
```

### ❌ Dashboard não abre
```
Solução: Reinicie o Streamlit
1. Pressione Ctrl + C no terminal
2. Execute: streamlit run dashboard.py
```

### ❌ Task Scheduler não executa
```
Solução:
1. Abra Task Scheduler
2. Procure a tarefa "Radar Licitações TI"
3. Clique com botão direito > Propriedades
4. Aba "Geral": Marque "Executar com maiores permissões"
5. Aba "Executar": Clique em "Alterar usuário ou grupo"
6. Selecione seu usuário atual
```

---

## 📈 Interpretando os Dados

### Resumo Executivo (Dashboard)

| Métrica | Significado |
|---------|------------|
| **Total** | Quantidade de licitações de TI encontradas |
| **Órgãos** | Quantidade de órgãos públicos que liceitam TI |
| **Estados** | Quantidade de estados com licitações |
| **Valor Total** | Soma de todos os valores estimados (R$) |
| **Valor Médio** | Média dos valores (R$) |

### Análises Disponíveis

1. **Órgãos**
   - Quem mais licita TI
   - Valor total por órgão

2. **Estados**
   - Distribuição geográfica
   - Estados com mais oportunidades

3. **Valores**
   - Faixas de licitação
   - Top 10 maiores valores

4. **Timeline**
   - Publicações por data
   - Padrões de publicação

5. **Dados Brutos**
   - Tabela completa
   - Busca por palavra-chave
   - Exportação de filtros

---

## 🔍 Filtros Disponíveis

### No Dashboard

- **Estado (UF)** - Filtrar por um ou mais estados
- **Órgão** - Filtrar por órgãos específicos (Top 50)
- **Valor mínimo/máximo** - Faixa de valores

### Exemplo de Filtro
```
Estado: São Paulo
Órgão: Ministério da Fazenda
Valor: R$ 100.000 a R$ 1.000.000
```

---

## 📝 Palavras-chave Monitoradas

O sistema filtra automaticamente licitações que contenham:

**Desenvolvimento:**
- software, sistema, aplicativo, desenvolvimento, código

**Infraestrutura:**
- cloud, nuvem, infraestrutura, rede, segurança, dados

**Tecnologias:**
- api, banco de dados, python, java, csharp, nodejs

**Licenses:**
- licença, licenciamento

**Cloud & DevOps:**
- docker, kubernetes, aws, azure, gcp

---

## 📞 Support e Manutenção

### Logs
- Os logs da execução são exibidos no console
- Conteúdo salvo em `radar_state.json`

### Problemas Comuns

**A API retorna dados vazios?**
- Pode ser fim de semana/feriado
- Período sem publicações novas

**Duplicatas nos dados?**
- Sistema remove automaticamente
- Baseado no número do edital

**Dashboard lento?**
- Depende da quantidade de dados
- Redobre o número de registros nos filtros

---

## 🎯 Próximas Melhorias

- [ ] Email com alertas de novas licitações
- [ ] Integração com Telegram/WhatsApp
- [ ] Análise de trending topics de TI
- [ ] Previsão de próximas licitações
- [ ] API própria para integração

---

## 📄 Licença e Uso

**Licença:** MIT
**Fonte:** Portal Nacional de Contratações Públicas (PNCP)
**Data:** 2026
**Manutenção:** Sistema Automático

---

## ✅ Checklist de Verificação

- [ ] Python 3.10+ instalado
- [ ] Dependências instaladas (`pip install -r requirements.txt`)
- [ ] Primeira coleta executada sem erros
- [ ] Dashboard abre corretamente
- [ ] Arquivo Excel gerado
- [ ] Arquivo CSV gerado
- [ ] Task Scheduler configurado (opcional)

---

## 🚨 IMPORTANTE

1. **Respeite os Limites da API**
   - Não execute o script manualmente mais de 1x a cada 5 minutos
   - Se agendar no Task Scheduler, máximo 2-3x por dia

2. **Uso de Dados**
   - Dados são públicos do PNCP
   - Respeite os termos de serviço

3. **Performance**
   - Primeira execução pode levar 10-15 minutos
   - Próximas são mais rápidas

---

## 🎓 Exemplo de Fluxo de Uso

### Dia 1: Setup
1. Instalar Python
2. Executar `pip install -r requirements.txt`
3. Executar `python pncp_radar_ti_plus.py`
4. Abrir `streamlit run dashboard.py`

### Dia 2+: Uso Diário
1. Executar coleta manualmente ou via Task Scheduler
2. Abrir dashboard para análise
3. Filtrar e exportar dados conforme necessário

---

**Desenvolvido com ❤️ para oportunidades de TI no Brasil**

Última atualização: 06/03/2026
