"""
Teste final da API PNCP com TODOS os parâmetros obrigatórios
"""

import requests
from datetime import datetime, timedelta

print("=" * 70)
print("TESTE DA API - Combinação de parâmetros obrigatórios")
print("=" * 70)
print()

# Datas (últimos 10 dias)
data_fim = datetime.now()
data_inicio = data_fim - timedelta(days=10)

print(f"Data inicial: {data_inicio.strftime('%Y-%m-%d')}")
print(f"Data final:   {data_fim.strftime('%Y-%m-%d')}")
print()

# Teste 1: Com dataInicial + dataFinal + codigoModalidadeContratacao + pagina
print("[Teste 1] Com dataInicial + dataFinal + codigoModalidadeContratacao=0 + pagina")
try:
    params = {
        "dataInicial": data_inicio.strftime("%Y%m%d"),  # Formato: yyyyMMdd
        "dataFinal": data_fim.strftime("%Y%m%d"),      # Formato: yyyyMMdd
        "codigoModalidadeContratacao": 0,
        "pagina": 1
    }
    print(f"Parâmetros: {params}")
    
    r = requests.get(
        "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao",
        params=params,
        timeout=120
    )
    print(f"Status: {r.status_code}")
    
    if r.status_code == 200:
        dados = r.json()
        print(f"✓ SUCESSO!")
        print(f"Tipo: {type(dados)}")
        if isinstance(dados, dict):
            print(f"Chaves: {list(dados.keys())}")
            if 'data' in dados:
                print(f"Registros: {len(dados['data'])}")
                if dados['data']:
                    print(f"Primeiro registro: {dados['data'][0]}")
    else:
        print(f"✗ Erro {r.status_code}")
        print(f"Resposta: {r.text[:500]}")
except Exception as e:
    print(f"✗ Erro de requisição: {str(e)[:200]}")

print()

# Teste 2: Testando diferentes valores de codigoModalidadeContratacao
print("[Teste 2] Testando diferentes códigos de modalidade")
for codigo in [0, 1, 2, 3, 8]:
    try:
        params = {
            "dataInicial": data_inicio.strftime("%Y%m%d"),  # Formato: yyyyMMdd
            "dataFinal": data_fim.strftime("%Y%m%d"),      # Formato: yyyyMMdd
            "codigoModalidadeContratacao": codigo,
            "pagina": 1
        }
        
        r = requests.get(
            "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao",
            params=params,
            timeout=120
        )
        
        if r.status_code == 200:
            dados = r.json()
            count = len(dados.get('data', []))
            print(f"  Código {codigo}: ✓ Status 200 - {count} registros")
        else:
            print(f"  Código {codigo}: Status {r.status_code}")
    except Exception as e:
        print(f"  Código {codigo}: Erro - {str(e)[:50]}")

print()
print("Testes concluídos!")
