#!/usr/bin/env python3
"""
Teste de integração: Simula carregamento do dashboard sem Streamlit
Valida que a lógica de filtro de UFs funciona corretamente
"""
import pandas as pd
import os
import sys

print("\n" + "="*70)
print("TESTE DE INTEGRAÇÃO - DASHBOARD UFs")
print("="*70)

# Simular importações do dashboard.py
CSV_PATH = "licitacoes_TI.csv"
CSV_PATH_ALT = "dados/licitacoes.csv"
EXCEL_PATH = "radar_licitacoes_TI_PRO.xlsx"

def normalizar_dataframe(df):
    """Simula função do dashboard.py"""
    if df.empty:
        return df
    
    # Garantir coluna 'uf'
    if 'uf' not in df.columns:
        df['uf'] = 'N/A'
    
    return df

# Simular carregar_dados()
print("\n[1/5] Carregando dados...")
df = None
fonte = None

if os.path.exists(CSV_PATH_ALT):
    try:
        df = pd.read_csv(CSV_PATH_ALT)
        fonte = CSV_PATH_ALT
        print(f"     ✅ Carregado: {CSV_PATH_ALT}")
    except Exception as e:
        print(f"     ❌ Erro: {e}")

if df is None and os.path.exists(CSV_PATH):
    try:
        df = pd.read_csv(CSV_PATH)
        fonte = CSV_PATH
        print(f"     ✅ Carregado: {CSV_PATH}")
    except Exception as e:
        print(f"     ❌ Erro: {e}")

if df is None:
    print("     ❌ Nenhum arquivo encontrado")
    sys.exit(1)

print(f"\n[2/5] Normalizando dados...")
df = normalizar_dataframe(df)
print(f"     ✅ {len(df)} linhas carregadas")

# Simular normalizar_lista_ufs()
print(f"\n[3/5] Processando UFs...")
from utils_uf import normalizar_uf, UF_NOMES, contar_ufs_invalidas

def normalizar_lista_ufs(series_uf):
    ufs_normalizadas = {}
    for uf_bruto in series_uf.dropna().unique():
        uf_norm = normalizar_uf(uf_bruto)
        if uf_norm:
            ufs_normalizadas[uf_norm] = UF_NOMES.get(uf_norm, uf_norm)
    return ufs_normalizadas

ufs_dict = normalizar_lista_ufs(df['uf'])
ufs_lista = sorted(ufs_dict.keys())
ufs_invalidas_count = contar_ufs_invalidas(df['uf'])

print(f"     ✅ {len(ufs_lista)} UFs únicos encontrados")
if ufs_invalidas_count > 0:
    print(f"     ⚠️  {ufs_invalidas_count} registros com UF inválida")

# Simular construção do filtro
print(f"\n[4/5] Construindo filtro...")
if len(ufs_lista) > 0:
    opcoes_display = [f"{uf} - {ufs_dict[uf]}" for uf in ufs_lista]
    print(f"     ✅ {len(opcoes_display)} opções no multiselect")
    print(f"     Exemplo: {opcoes_display[0]}")
else:
    print("     ❌ Nenhum UF válido encontrado")
    sys.exit(1)

# Validação final
print(f"\n[5/5] Validação final...")
print(f"     UFs esperados: 27")
print(f"     UFs obtidos: {len(ufs_lista)}")

if len(ufs_lista) == 27:
    print(f"\n" + "="*70)
    print("✅ SUCESSO: Dashboard pode exibir todos os 27 UFs no filtro!")
    print("="*70 + "\n")
    print("UFs disponíveis:")
    for i, uf in enumerate(ufs_lista, 1):
        nome = ufs_dict[uf]
        print(f"    {i:2d}. {uf} - {nome}")
    print("="*70)
    sys.exit(0)
else:
    print(f"\n❌ ERRO: Esperados 27 UFs, mas encontrados {len(ufs_lista)}")
    print(f"Encontrados: {ufs_lista}")
    sys.exit(1)
