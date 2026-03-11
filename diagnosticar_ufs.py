#!/usr/bin/env python
"""Diagnóstico rápido de UFs nos dados"""
import pandas as pd
import os

# Tentar carregar dados
csv_paths = ['dados/licitacoes.csv', 'licitacoes_TI.csv']

df = None
for path in csv_paths:
    if os.path.exists(path):
        try:
            df = pd.read_csv(path)
            print(f"✓ Carregado: {path}")
            break
        except:
            pass

if df is None:
    print("❌ Nenhum arquivo CSV encontrado!")
    exit(1)

print(f"\n📊 DADOS:")
print(f"  Linhas: {len(df)}")
print(f"  Colunas: {df.columns.tolist()}")

if 'uf' in df.columns:
    print(f"\n🗺️  UFs ÚNICAS (RAW):")
    ufs = df['uf'].dropna().unique()
    print(f"  Contagem: {len(ufs)}")
    for i, uf in enumerate(sorted(ufs)):
        count = (df['uf'] == uf).sum()
        print(f"    {i+1}. {uf:20} → {count:5} registros")
    
    print(f"\n❓ PROBLEMAS:")
    print(f"  Nulos/NaN: {df['uf'].isna().sum()}")
    print(f"  'N/A': {(df['uf'] == 'N/A').sum()}")
else:
    print("❌ Coluna 'uf' não encontrada!")
