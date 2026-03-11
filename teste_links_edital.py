#!/usr/bin/env python3
"""
Teste rápido: Validar funcionalidade de links de edital
"""
import pandas as pd
import numpy as np

# Função de gerar link (copiada do dashboard.py)
def gerar_link_edital(numero_edital):
    """Gera link para edital no PNCP portal"""
    if pd.isna(numero_edital) or numero_edital == 0 or numero_edital == '':
        return 'https://www.pncp.gov.br'
    # URL para portal de editais do PNCP
    return f'https://www.pncp.gov.br/app/editais?numero={str(numero_edital).replace(".", "").replace("/", "-")}'

print("=" * 70)
print("TESTE: Links de Edital")
print("=" * 70)

# Testar função
teste_casos = [
    ("123456", "Edital com número"),
    ("123.456/2026", "Edital formatado"),
    (0, "Número zero"),
    ("", "String vazia"),
    (None, "None"),
    (np.nan, "NaN"),
]

print("\nTestando geração de links:")
for numero, descricao in teste_casos:
    link = gerar_link_edital(numero)
    print(f"\n  {descricao}:")
    print(f"    Input: {numero}")
    print(f"    Output: {link}")

# Testar com dados reais
print("\n" + "=" * 70)
print("Teste com dados reais do CSV:")
print("=" * 70)

df = pd.read_csv('dados/licitacoes.csv')
print(f"\nCarregados {len(df)} registros")

if 'numero_edital' in df.columns:
    print(f"\nPrimeiros 5 números de edital e seus links:")
    for i, num in enumerate(df['numero_edital'].head(5), 1):
        link = gerar_link_edital(num)
        print(f"\n  {i}. Número: {num}")
        print(f"     Link: {link}")
    
    # Testar com toda a coluna
    df['link_edital'] = df['numero_edital'].apply(gerar_link_edital)
    print(f"\n✅ Coluna 'link_edital' adicionada com sucesso!")
    print(f"   Total links gerados: {len(df)}")
    print(f"   Links únicos: {df['link_edital'].nunique()}")
    
    # Amostra de dados processados
    print(f"\nAmostra de dados com links:")
    sample = df[['numero_edital', 'objeto', 'link_edital']].head(3)
    for idx, row in sample.iterrows():
        print(f"\n  {idx + 1}. Edital: {row['numero_edital']}")
        print(f"     Objeto: {str(row['objeto'])[:50]}...")
        print(f"     Link: {row['link_edital']}")
else:
    print("❌ Coluna 'numero_edital' não encontrada!")

print("\n" + "=" * 70)
print("✅ TESTE CONCLUÍDO COM SUCESSO!")
print("=" * 70)
