# ✅ CHECKLIST - SISTEMA PRONTO PARA USO

## 📋 Antes de Começar

- [ ] Python 3.10+ instalado
- [ ] Conexão com internet disponível
- [ ] Pasta `C:\licitacoes_pncp` existe
- [ ] PowerShell ou CMD disponível
- [ ] Permissões de administrador (para automação)

## 🚀 Configuração Inicial

### 1️⃣ Ambiente Python
- [ ] Abrir PowerShell como Administrador
- [ ] Navegar para `C:\licitacoes_pncp`
- [ ] Criar venv: `python -m venv venv`
- [ ] Ativar venv: `.\venv\Scripts\Activate.ps1`
- [ ] Instalar pacotes: `pip install -r requirements.txt`
- [ ] Verificar instalação: `python --version`

**Tempo esperado:** 3-5 minutos

### 2️⃣ Teste de Conectividade
- [ ] Executar diagnóstico: `python diagnosticar_sistema.py`
- [ ] Verificar status de todos os testes
- [ ] Corrigir problemas se houver
- [ ] Confirmar ✅ "Sistema OK"

**Tempo esperado:** 1 minuto

### 3️⃣ Teste da API
- [ ] Fazer teste de API: `python testar_api_pncp.py`
- [ ] Verificar 6 testes

**Tempo esperado:** 1 minuto

## 📊 Usar o Sistema

### Coleta Manual
- [ ] Ativar venv (se necessário)
- [ ] Executar: `python pncp_radar_ti_plus.py`
- [ ] Aguardar 2-5 minutos
- [ ] Verificar se criou:
   - [ ] `radar_licitacoes_TI_PRO.xlsx`
   - [ ] `dados/licitacoes.csv`
   - [ ] `radar_state.json`

### Dashboard Interativo
- [ ] Ativar venv (se necessário)
- [ ] Executar: `streamlit run dashboard.py`
- [ ] Verificar se abriu navegador
- [ ] Testar filtros
- [ ] Verificar gráficos

### Automação
- [ ] Abrir PowerShell COMO ADMINISTRADOR
- [ ] Executar: `.\configurar_agendamento.ps1 -Acao criar`
- [ ] Confirmar criação da tarefa
- [ ] Verificar status: `.\configurar_agendamento.ps1 -Acao status`

**Resultado esperado:** Execução todos os dias às 07:00

## 📈 Validação de Dados

### Verificações de integridade
- [ ] Excel tem dados (não vazio)
- [ ] CSV tem múltiplas linhas
- [ ] Valores em R$ aparecem corretamente
- [ ] Datas estão formatadas
- [ ] Órgãos públicos listados
- [ ] Estados (UF) preenchidos

### Qualidade dos dados
- [ ] Total de licitações > 0
- [ ] Licitações de TI > 0
- [ ] Valor estimado > 0
- [ ] Sem linhas duplicadas
- [ ] Caracteres especiais OK

## 💾 Arquivos Criados

Verificar se todos foram criados após primeira coleta:

```
C:\licitacoes_pncp\
├── radar_licitacoes_TI_PRO.xlsx  ✅
├── dados/
│   └── licitacoes.csv            ✅
├── radar_state.json              ✅
└── logs/
    └── execucao_*.log            ✅
```

## 🔧 Troubleshooting Rápido

| Problema | Solução | Teste |
|----------|---------|-------|
| "Python não encontrado" | Instalar Python 3.10+ | `python --version` |
| "Módulo não encontrado" | `pip install -r requirements.txt` | `python -c "import pandas"` |
| "Erro 400 da API" | Normal, período sem dados | Testar outro dia |
| "Timeout" | API lenta, aguardar | Tentar novamente em 5min |
| "Permissão negada" | Executar como Admin | Clicar direito > Admin |
| "Dashboard não abre" | Executar coleta primeiro | `python pncp_radar_ti_plus.py` |

## 📚 Documentação

| Documento | Quando Ler | Tempo |
|-----------|-----------|-------|
| INICIO_RAPIDO.md | Primeira vez | 5min |
| GUIA_COMPLETO.md | Dúvidas avançadas | 30min |
| PALAVRAS_CHAVE.md | Entender filtros | 10min |
| README.md | Visão geral | 5min |

## 🎯 Próximas Ações

### Após primeira execução com sucesso:
- [ ] Revisar dados em Excel
- [ ] Explorar dashboard
- [ ] Ajustar filtros conforme necessário
- [ ] Planejar próxima análise

### Para uso contínuo:
- [ ] Configurar automação diária
- [ ] Revisar logs regularmente
- [ ] Atualizar filtros conforme mudanças
- [ ] Compartilhar dashboard com equipe

### Para análises avançadas:
- [ ] Baixar CSV para análise em Python
- [ ] Importar dados em Power BI
- [ ] Criar alertas personalizados
- [ ] Gerar relatórios automáticos

## 🚨 Verificação de Saúde

Executar regularmente para manter sistema saudável:

```powershell
# Diagnóstico completo
python diagnosticar_sistema.py

# Teste de API
python testar_api_pncp.py

# Teste manual de coleta
python pncp_radar_ti_plus.py
```

**Frequência recomendada:** Semana ly

## 📞 Suporte

Se encontrar problemas não listados:

1. Consulte: `GUIA_COMPLETO.md` (Seção: Solução de Problemas)
2. Execute: `python diagnosticar_sistema.py`
3. Verifique: `logs/execucao_*.log` (últimas execuções)
4. Teste: `python testar_api_pncp.py`

## ✨ Performance Esperada

| Operação | Tempo | Status |
|----------|-------|--------|
| Instalação | 3-5min | ✅ Rápido |
| Diagnóstico | 1min | ✅ Rápido |
| Coleta | 2-5min | ✅ Aceitável |
| Dashboard | <1s | ✅ Rápido |
| Exportação | 5-10s | ✅ Rápido |

## 🎉 Sucesso Confirmado Quando:

- ✅ `python diagnosticar_sistema.py` mostra ✓ em todos os testes
- ✅ `python testar_api_pncp.py` completa 6/6 testes
- ✅ `python pncp_radar_ti_plus.py` cria arquivos de saída
- ✅ `streamlit run dashboard.py` abre no navegador
- ✅ `.\configurar_agendamento.ps1 -Acao criar` confirma criação da tarefa
- ✅ Dashboard mostra dados com filtros operacionais
- ✅ Excel tem formatação profissional
- ✅ Automação executa à hora programada

**Se todos os itens acima estão ✓, o sistema está 100% pronto!**

---

## 📋 Checklist de Manutenção Mensal

- [ ] Revisar logs do último mês
- [ ] Confirmar que automação está rodando
- [ ] Executar diagnóstico completo
- [ ] Verificar espaço em disco
- [ ] Revisar qualidade dos dados
- [ ] Atualizar filtros se necessário
- [ ] Compartilhar relatórios com stakeholders

---

## 🚀 Você está pronto!

**✅ Todos os itens acima marcados = Sistema 100% operacional**

**Próximo passo:** Abra [INICIO_RAPIDO.md](INICIO_RAPIDO.md) e comece!

---

**Últimas verificações:**
- Data: ________________
- Responsável: ________________
- Status: ☐ TUDO OK ☐ PROBLEMAS ENCONTRADOS

**Observações:**
_________________________________
_________________________________
_________________________________

---

*Checklist criado para garantir que todo o sistema foi instalado e testado corretamente.*
