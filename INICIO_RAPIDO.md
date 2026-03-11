# 🚀 INÍCIO RÁPIDO - RADAR DE LICITAÇÕES DE TI

## ⚡ Os 3 Passos Para Começar

### 1️⃣ PREPARAÇÃO (primeira vez)

```powershell
# Abra PowerShell como Administrador

cd C:\licitacoes_pncp

# Configure permissões
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Crie ambiente virtual
python -m venv venv

# Ative ambiente
.\venv\Scripts\Activate.ps1

# Instale dependências
pip install -r requirements.txt
```

**Tempo:** ~3 minutos

---

### 2️⃣ TESTE DO SISTEMA

```powershell
# Certifique-se de estar no diretório correto
cd C:\licitacoes_pncp

# Ative o ambiente virtual (se necessário)
.\venv\Scripts\Activate.ps1

# Execute diagnóstico
python diagnosticar_sistema.py
```

**Esperado:** Todos os testes passarem ✅

---

### 3️⃣ COLETAR DADOS

```powershell
# Ative o ambiente (se necessário)
.\venv\Scripts\Activate.ps1

# Execute coleta
python pncp_radar_ti_plus.py
```

**Esperado:** 
- Arquivos criados: `radar_licitacoes_TI_PRO.xlsx` + `dados/licitacoes.csv`
- Tempo: 2-5 minutos

---

## 📊 VER DADOS NO DASHBOARD

```powershell
# Ative o ambiente (se necessário)
.\venv\Scripts\Activate.ps1

# Abra dashboard
streamlit run dashboard.py
```

**Resultado:** 
- Abre navegador em `http://localhost:8501`
- Explore filtros e gráficos interativos

---

## ⏰ CONFIGURAR AUTOMAÇÃO DIÁRIA

```powershell
# Abra PowerShell como ADMINISTRADOR

cd C:\licitacoes_pncp

# Configure para rodar diariamente às 07:00
.\configurar_agendamento.ps1 -Acao criar

# Verificar status
.\configurar_agendamento.ps1 -Acao status
```

**Resultado:** Coleta automática todos os dias às 07:00

---

## 🎯 EXEMPLOS DE USO

### Coletar dados MANUALMENTE diariamente:
```powershell
.\venv\Scripts\Activate.ps1 && python pncp_radar_ti_plus.py
```

### Abrir dashboard:
```powershell
.\venv\Scripts\Activate.ps1 && streamlit run dashboard.py
```

### Executar teste:
```powershell
.\venv\Scripts\Activate.ps1 && python diagnosticar_sistema.py
```

### Verificar status da automação:
```powershell
.\configurar_agendamento.ps1 -Acao status
```

---

## ❌ ERROS COMUNS

| Erro | Solução |
|------|---------|
| `python not found` | Instale Python em python.org |
| `Permission denied` | Execute PowerShell como Admin |
| `Module not found` | Execute: `pip install -r requirements.txt` |
| `API timeout` | Aguarde e tente novamente |
| `arquivo não encontrado` | Verifique se está em `C:\licitacoes_pncp` |

---

## 📁 ARQUIVOS PRINCIPAIS

| Arquivo | Propósito | Frequência |
|---------|-----------|-----------|
| `pncp_radar_ti_plus.py` | Coleta dados | Manualmente ou Diário |
| `dashboard.py` | Visualização | Sob demanda |
| `radar_licitacoes_TI_PRO.xlsx` | Dados em Excel | Após coleta |
| `dados/licitacoes.csv` | Dados para dashboard | Após coleta |
| `logs/execucao_*.log` | Histórico | Automático |

---

## 🎨 O QUE O DASHBOARD MOSTRA

✅ Total de licitações encontradas  
✅ Órgãos que mais contratam TI  
✅ Distribuição por estado (mapa)  
✅ Valor total e médio das licitações  
✅ Maiores licitações  
✅ Timeline de publicações  
✅ Tabela completa filtrável  

---

## 📞 PRÓXIMAS ETAPAS

1. ✅ Completar instalação
2. ✅ Executar primeiro teste
3. ✅ Coletar dados (manual)
4. ✅ Explorar dashboard
5. ✅ Configurar automação
6. ✅ Agendar visualizações semanais

---

**Dúvidas?** Consulte `GUIA_COMPLETO.md` para documentação detalhada.
