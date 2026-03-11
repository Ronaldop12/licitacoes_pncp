#!/usr/bin/env python3
"""
Teste rápido para validar que todos os 27 UFs estão sendo carregados
"""
import pandas as pd
import os
from utils_uf import normalizar_uf, UF_NOMES

print("=" * 60)
print("TESTE DE VALIDAÇÃO DO DASHBOARD - UFs")
print("=" * 60)

# Caminho dos dados
CSV_PATH_ALT = "dados/licitacoes.csv"
CSV_PATH = "licitacoes_TI.csv"

# Carregar dados
df = None
fonte = None

if os.path.exists(CSV_PATH_ALT):
    try:
        df = pd.read_csv(CSV_PATH_ALT)
        fonte = "dados/licitacoes.csv (PREFERIDO)"
        if 'uf' not in df.columns:
            print(f"⚠️  {CSV_PATH_ALT} existe mas NÃO tem coluna 'uf'")
            print(f"    Colunas disponíveis: {list(df.columns)}")
            df = None
    except Exception as e:
        print(f"❌ Erro ao carregar {CSV_PATH_ALT}: {e}")

if df is None and os.path.exists(CSV_PATH):
    try:
        df = pd.read_csv(CSV_PATH)
        fonte = "licitacoes_TI.csv (FALLBACK)"
        if 'uf' not in df.columns:
            print(f"⚠️  {CSV_PATH} existe mas NÃO tem coluna 'uf'")
            print(f"    Colunas disponíveis: {list(df.columns)}")
            df = None
    except Exception as e:
        print(f"❌ Erro ao carregar {CSV_PATH}: {e}")

if df is None:
    print("❌ Nenhum arquivo de dados encontrado ou com coluna 'uf'")
    exit(1)

print(f"\n✅ Dados carregados: {fonte}")
print(f"   Total de linhas: {len(df)}")
print(f"   Colunas: {list(df.columns)}")

# Analisar UFs
print("\n" + "=" * 60)
print("ANÁLISE DE UFs")
print("=" * 60)

# UFs brutos (antes de normalizar)
ufs_brutos = df['uf'].dropna().unique()
print(f"\n📊 UFs BRUTOS encontrados: {len(ufs_brutos)}")
print(f"   {sorted(ufs_brutos)}")

# UFs normalizados
ufs_normalizadas = set()
for uf_bruto in ufs_brutos:
    uf_norm = normalizar_uf(uf_bruto)
    if uf_norm:
        ufs_normalizadas.add(uf_norm)

ufs_normalizadas = sorted(ufs_normalizadas)
print(f"\n✅ UFs NORMALIZADOS: {len(ufs_normalizadas)} de 27")
print(f"   {ufs_normalizadas}")

# Comparar com 27 UFs esperados
from utils_uf import UFS_VALIDAS
ufs_esperados = sorted(UFS_VALIDAS)
print(f"\n📋 UFs ESPERADOS (ABNT): {len(ufs_esperados)}")
print(f"   {ufs_esperados}")

# Validação
faltando = set(ufs_esperados) - set(ufs_normalizadas)
extras = set(ufs_normalizadas) - set(ufs_esperados)

print(f"\n" + "=" * 60)
if len(ufs_normalizadas) == 27:
    print("✅ SUCESSO: Todos os 27 UFs estão presentes!")
else:
    print(f"⚠️  AVISO: Apenas {len(ufs_normalizadas)} UFs encontrados")
    if faltando:
        print(f"   Faltando: {sorted(faltando)}")
    if extras:
        print(f"   Extras: {sorted(extras)}")

print("=" * 60)

# Distribuição de UFs
print("\n📈 DISTRIBUIÇÃO DE LICITAÇÕES POR UF:")
print("-" * 60)
dfg = df[df['uf'].notna()].copy()
dfg['uf_norm'] = dfg['uf'].apply(lambda x: normalizar_uf(x))
dfg = dfg[dfg['uf_norm'].notna()]

distribuicao = dfg['uf_norm'].value_counts().sort_index()
for uf, count in distribuicao.items():
    pct = (count / len(dfg)) * 100
    nome = UF_NOMES.get(uf, uf)
    print(f"  {uf} ({nome:20s}): {count:4d} registros ({pct:5.2f}%)")

print(f"\n{'TOTAL':40s}: {len(dfg):4d} registros")
print("=" * 60)
