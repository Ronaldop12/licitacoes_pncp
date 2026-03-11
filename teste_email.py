#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script para testar envio de email com novas licitações"""

import pandas as pd
import os

# Carregar CSV
df = pd.read_csv('dados/licitacoes.csv')
print(f"CSV atual: {len(df)} registros\n")

# Pegar últimas 3 linhas como modelo
ultimas = df.tail(3).copy()

# Alterar número do edital para simular novas licitações
for i, idx in enumerate(ultimas.index):
    novo_edital = f"TEST_{999000 + i}_2026"
    ultimas.loc[idx, 'numero_edital'] = novo_edital

# Salvar backup atual em outro lugar
if os.path.exists('config/backup_licitacoes.csv'):
    df.to_csv('config/backup_licitacoes.csv', index=False)

# Adicionar novas licitações ao CSV
df_novo = pd.concat([df, ultimas], ignore_index=True)
df_novo.to_csv('dados/licitacoes.csv', index=False)

print(f"CSV atualizado: {len(df_novo)} registros (adicionadas 3 licitações de teste)\n")
print("Novas licitações:")
print(ultimas[['numero_edital', 'orgao', 'valor_estimado']].to_string())
print("\n✓ Agora execute: python monitor_alertas.py")
