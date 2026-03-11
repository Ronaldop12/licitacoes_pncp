"""
Testar diferentes endpoints da API PNCP
"""

import requests

print("Testando endpoints alternativos da API PNCP...")
print()

# Teste 1: Endpoint de licitações sem filtros obrigatórios
print("[Teste 1] GET /contratacoes (sem filtros)")
try:
    r = requests.get(
        "https://pncp.gov.br/api/consulta/v1/contratacoes",
        timeout=120
    )
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        dados = r.json()
        print(f"Tipo: {type(dados)}")
        if isinstance(dados, dict):
            print(f"Chaves: {list(dados.keys())[:5]}")
            print(f"Registros: {len(dados.get('data', []))}")
            if dados.get('data'):
                print("✓ Sucesso!")
        else:
            print(f"Quantidade: {len(dados)}")
    else:
        print(f"Erro: {r.text[:200]}")
except Exception as e:
    print(f"✗ Erro: {str(e)[:100]}")

print()

# Teste 2: Versão 2 da API (se existir)
print("[Teste 2] GET /v2/contratacoes")
try:
    r = requests.get(
        "https://pncp.gov.br/api/consulta/v2/contratacoes",
        timeout=120
    )
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        dados = r.json()
        print(f"✓ Sucesso!")
    else:
        print(f"Status: {r.status_code}")
except Exception as e:
    print(f"✗ Erro: {str(e)[:100]}")

print()

# Teste 3: Com parâmetro de limite apenas
print("[Teste 3] GET /contratacoes/publicacao?limit=10")
try:
    r = requests.get(
        "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao",
        params={"limit": 10},
        timeout=120
    )
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        dados = r.json()
        if 'data' in dados:
            print(f"Registros: {len(dados.get('data', []))}")
            print("✓ Sucesso!")
        else:
            print(f"Chaves: {list(dados.keys())}")
    else:
        print(f"Erro: {r.text[:300]}")
except Exception as e:
    print(f"✗ Erro: {str(e)[:100]}")

print()

# Teste 4: Com todas as modalidades (0 = todas)
print("[Teste 4] Com codigoModalidadeContratacao=0 (todas)")
try:
    r = requests.get(
        "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao",
        params={
            "codigoModalidadeContratacao": 0,
            "offset": 0,
            "limit": 10
        },
        timeout=120
    )
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        dados = r.json()
        print(f"Registros: {len(dados.get('data', []))}")
        print("✓ Sucesso!")
    else:
        print(f"Erro: {r.text[:300]}")
except Exception as e:
    print(f"✗ Erro: {str(e)[:100]}")
