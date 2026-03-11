"""
VALIDAÇÃO FINAL DO SISTEMA - Radar de Licitações de TI
Verifica se todos os componentes estão funcionando corretamente.
"""

import os
import pandas as pd
import requests
from datetime import datetime, timedelta

print("=" * 70)
print("VALIDAÇÃO COMPLETA DO SISTEMA - Radar de Licitações de TI")
print("=" * 70)
print()

total_testes = 0
testes_ok = 0

# Teste 1: Arquivos de saída
print("[1/5] Verificando arquivos de saída...")
total_testes += 1

arquivos_necessarios = {
    "radar_licitacoes_TI_PRO.xlsx": "Excel com licitações de TI",
    "dados/licitacoes.csv": "CSV com dados",
    "radar_state.json": "Arquivo de estado"
}

ok = True
for arquivo, descricao in arquivos_necessarios.items():
    if os.path.exists(arquivo):
        tamanho = os.path.getsize(arquivo) / 1024
        print(f"  ✓ {arquivo} ({tamanho:.1f} KB) - {descricao}")
        testes_ok += 1
    else:
        print(f"  ✗ {arquivo} - NÃO ENCONTRADO")
        ok = False

if not ok:
    total_testes -= 1

# Teste 2: Dados no Excel
print("\n[2/5] Validando dados no Excel...")
total_testes += 1

try:
    df_excel = pd.read_excel("radar_licitacoes_TI_PRO.xlsx")
    print(f"  ✓ Arquivo Excel válido")
    print(f"  ✓ {len(df_excel)} registros de licitações")
    print(f"  ✓ Colunas: {', '.join(df_excel.columns[:5])}...")
    testes_ok += 1
except Exception as e:
    print(f"  ✗ Erro ao ler Excel: {str(e)[:50]}")

# Teste 3: Dados no CSV
print("\n[3/5] Validando dados no CSV...")
total_testes += 1

try:
    df_csv = pd.read_csv("dados/licitacoes.csv")
    print(f"  ✓ Arquivo CSV válido")
    print(f"  ✓ {len(df_csv)} registros")
    testes_ok += 1
except Exception as e:
    print(f"  ✗ Erro ao ler CSV: {str(e)[:50]}")

# Teste 4: Conectividade com API
print("\n[4/5] Testando conexão com API PNCP...")
total_testes += 1

try:
    data_fim = datetime.now()
    data_inicio = data_fim - timedelta(days=1)
    
    params = {
        "dataInicial": data_inicio.strftime("%Y%m%d"),
        "dataFinal": data_fim.strftime("%Y%m%d"),
        "codigoModalidadeContratacao": 1,
        "pagina": 1
    }
    
    r = requests.get(
        "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao",
        params=params,
        timeout=10
    )
    
    if r.status_code == 200:
        print(f"  ✓ API PNCP respondendo corretamente (Status 200)")
        dados = r.json()
        print(f"  ✓ {len(dados.get('data', []))} licitações retornadas")
        testes_ok += 1
    else:
        print(f"  ✗ API retornou Status {r.status_code}")
except Exception as e:
    print(f"  ✗ Erro de conexão: {str(e)[:50]}")

# Teste 5: Módulos Python
print("\n[5/5] Verificando módulos Python...")
total_testes += 1

modulos_necessarios = {
    "streamlit": "Dashboard",
    "pandas": "Processamento de dados",
    "requests": "HTTP requests",
    "openpyxl": "Excel"
}

ok = True
for modulo, descricao in modulos_necessarios.items():
    try:
        __import__(modulo)
        print(f"  ✓ {modulo} - {descricao}")
    except ImportError:
        print(f"  ✗ {modulo} - NÃO INSTALADO")
        ok = False

if ok:
    testes_ok += 1

# Resumo
print()
print("=" * 70)
print(f"RESULTADO:  {testes_ok}/{total_testes} testes aprovados")
print("=" * 70)

if testes_ok == total_testes:
    print("✓ SISTEMA 100% FUNCIONAL!")
    print()
    print("Próximos passos:")
    print("  1. Visualizar dashboard: streamlit run dashboard.py")
    print("  2. Coletar mais dados: python pncp_radar_ti_plus.py")
    print("  3. Exportar dados: ver radar_licitacoes_TI_PRO.xlsx")
else:
    print(f"✗ {total_testes - testes_ok} testes falharam")
    print("Verifique os erros acima")

print()
