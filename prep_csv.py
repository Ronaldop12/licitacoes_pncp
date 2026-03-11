#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Preparar CSV para teste com coluna uf"""

import pandas as pd
import re

# Carregar CSV
df = pd.read_csv('licitacoes_TI.csv')

# Extrair UF de órgão (assumindo que começa com "UF - Nome" ou similar)
# Exemplo: "SAO PAULO SECRETARIA..." -> SP
def extrair_uf(orgao_str):
    """Extrai 2 letras iniciais maiúsculas do órgão"""
    # Tenta encontrar padrões comuns
    if 'SAO PAULO' in str(orgao_str).upper():
        return 'SP'
    elif 'RIO' in str(orgao_str).upper() and 'JANEIRO' in str(orgao_str).upper():
        return 'RJ'
    elif 'MINAS' in str(orgao_str).upper():
        return 'MG'
    elif 'BAHIA' in str(orgao_str).upper():
        return 'BA'
    elif 'SANTA' in str(orgao_str).upper() and 'CATARINA' in str(orgao_str).upper():
        return 'SC'
    elif 'PARANA' in str(orgao_str).upper() or 'PARAN' in str(orgao_str).upper():
        return 'PR'
    else:
        # Tentar extrair código de estado
        match = re.search(r'([A-Z]{2})', str(orgao_str)[:20])
        if match:
            return match.group(1)
    return 'SP'  # Default

df['uf'] = df['orgao'].apply(extrair_uf)

# Adicionar coluna data_publicacao se não existe
if 'data_publicacao' not in df.columns:
    df['data_publicacao'] = pd.to_datetime('2026-03-07')

# Salvar
df.to_csv('dados/licitacoes.csv', index=False)
print(f"OK - CSV preparado com {len(df)} registros")
print(f"Colunas: {list(df.columns)}")
print(f"\nUFs detectadas: {df['uf'].unique()[:5]}")
print(f"Total por UF:\n{df['uf'].value_counts()}")
