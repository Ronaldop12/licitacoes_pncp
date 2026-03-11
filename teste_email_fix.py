#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Criar licitações SP para teste"""

import pandas as pd
import os

# Carregar CSV
df = pd.read_csv('dados/licitacoes.csv')

# Pegar últimas 3 linhas como modelo
ultimas = df[df['uf'] == 'SP'].tail(3).copy()

# Alterar número do edital para simular novas licitações
for i, idx in enumerate(ultimas.index):
    novo_edital = f"TEST_{999000 + i}_SP_2026"
    ultimas.loc[idx, 'numero_edital'] = novo_edital

# Garantir que está em SP
ultimas['uf'] = 'SP'

# Adicionar ao DF original (sem duplicar o que já existe)
df_novo = pd.concat([df, ultimas], ignore_index=True)
df_novo.to_csv('dados/licitacoes.csv', index=False)

print(f"OK - Licita coes de teste criadas em SP")
print("\nNovas licita coes:")
print(ultimas[['numero_edital', 'orgao', 'valor_estimado', 'uf']].to_string())
