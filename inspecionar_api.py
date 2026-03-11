"""
Inspecionar a estrutura real dos dados retornados pela API
"""

import requests
from datetime import datetime, timedelta

print("=" * 70)
print("INSPEÇÃO DOS DADOS DA API - Estrutura Real")
print("=" * 70)
print()

# Datas (últimos 7 dias)
data_fim = datetime.now()
data_inicio = data_fim - timedelta(days=7)

params = {
    "dataInicial": data_inicio.strftime("%Y%m%d"),
    "dataFinal": data_fim.strftime("%Y%m%d"),
    "codigoModalidadeContratacao": 1,
    "pagina": 1,
}

print(f"Parâmetros: {params}")
print()

try:
    r = requests.get(
        "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao",
        params=params,
        timeout=120
    )
    
    print(f"Status: {r.status_code}")
    
    if r.status_code == 200:
        dados = r.json()
        
        print(f"Tipo de resposta: {type(dados)}")
        print(f"Chaves principais: {list(dados.keys())}")
        print()
        
        # Inspencionar estrutura
        if 'data' in dados:
            print(f"Total de itens: {len(dados['data'])}")
            
            if dados['data']:
                print("\n--- PRIMEIRO ITEM (estrutura completa) ---")
                primeiro_item = dados['data'][0]
                print(f"Tipo: {type(primeiro_item)}")
                print(f"Chaves: {list(primeiro_item.keys())}")
                print()
                
                # Mostrar cada campo
                print("Conteúdo do primeiro item:")
                for chave, valor in primeiro_item.items():
                    print(f"  {chave}: {str(valor)[:100]}")
                
                print("\n--- EXEMPLOS DE ALGUNS OBJETOS ---")
                for i, item in enumerate(dados['data'][:3]):
                    print(f"\nItem {i+1}:")
                    for chave in ['objeto', 'valor', 'orgao', 'modalidade', 'status']:
                        if chave in item:
                            print(f"  {chave}: {str(item[chave])[:80]}")
                        elif chave == 'orgao' and isinstance(item.get('orgao'), dict):
                            print(f"  orgao.nome: {str(item['orgao'].get('nome', 'N/A'))[:80]}")
        
        # Informações sobre paginação
        print("\n--- INFORMAÇÕES DE PAGINAÇÃO ---")
        for chave in ['pagina', 'totalPaginas', 'total', 'offset', 'limit']:
            if chave in dados:
                print(f"  {chave}: {dados[chave]}")
    
    else:
        print(f"Status: {r.status_code}")
        print(f"Resposta: {r.text[:500]}")

except Exception as e:
    print(f"Erro: {str(e)}")
