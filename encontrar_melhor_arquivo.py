#!/usr/bin/env python
"""Encontra o arquivo com mais dados"""
import pandas as pd
import os

arquivos = [
    'radar_licitacoes_TI_PRO.xlsx',
    'radar_licitacoes_TI_plus.xlsx',
    'radar_licitacoes_TI.xlsx',
    'licitacoes_TI.csv',
    'dados/licitacoes.csv'
]

print("📊 VERIFICANDO ARQUIVOS DE DADOS:\n")

melhor = None
melhor_count = 0

for arquivo in arquivos:
    if not os.path.exists(arquivo):
        continue
    
    try:
        if arquivo.endswith('.xlsx'):
            df = pd.read_excel(arquivo)
        else:
            df = pd.read_csv(arquivo)
        
        count = len(df)
        ufs = df['uf'].nunique() if 'uf' in df.columns else 0
        
        print(f"✓ {arquivo:30} → {count:5} registros | {ufs:2} UFs")
        
        if count > melhor_count:
            melhor_count = count
            melhor = (arquivo, df)
            
    except Exception as e:
        print(f"✗ {arquivo:30} → Erro: {str(e)[:40]}")

print(f"\n✅ MELHOR: {melhor[0]} ({melhor_count} registros)\n")

if melhor:
    df = melhor[1]
    print(f"🗺️  UFs no arquivo:")
    ufs = df['uf'].value_counts()
    for uf, count in ufs.items():
        print(f"   {uf:3} → {count:3} registros")
