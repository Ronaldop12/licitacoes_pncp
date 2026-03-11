#!/usr/bin/env python
"""
Expande dados/licitacoes.csv com 2054 registros distribuídos entre 27 UFs
Para fins de teste do dashboard
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# UFs brasileiros (27)
UFS = ['AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
       'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
       'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO']

UF_NOMES = {
    'AC': 'Acre', 'AL': 'Alagoas', 'AP': 'Amapá', 'AM': 'Amazonas',
    'BA': 'Bahia', 'CE': 'Ceará', 'DF': 'Distrito Federal', 'ES': 'Espírito Santo',
    'GO': 'Goiás', 'MA': 'Maranhão', 'MT': 'Mato Grosso', 'MS': 'Mato Grosso do Sul',
    'MG': 'Minas Gerais', 'PA': 'Pará', 'PB': 'Paraíba', 'PR': 'Paraná',
    'PE': 'Pernambuco', 'PI': 'Piauí', 'RJ': 'Rio de Janeiro', 'RN': 'Rio Grande do Norte',
    'RS': 'Rio Grande do Sul', 'RO': 'Rondônia', 'RR': 'Roraima',
    'SC': 'Santa Catarina', 'SP': 'São Paulo', 'SE': 'Sergipe', 'TO': 'Tocantins'
}

print("📖 Carregando dados do arquivo principal...")
df_original = pd.read_excel('radar_licitacoes_TI_plus.xlsx')

print(f"✓ Carregado {len(df_original)} registros")
print(f"  Colunas: {df_original.columns.tolist()}")

# Copiar dados
df = df_original.copy()

# Adicionar coluna de UF distribuída aleatoriamente
print("\n🎲 Distribuindo 2054 registros entre 27 UFs...")
df['uf'] = np.random.choice(UFS, size=len(df))

# Renomear coluna 'objeto' se necessário
if 'objeto' not in df.columns and 'Unnamed: 0' in df.columns:
    df.rename(columns={'Unnamed: 0': 'objeto'}, inplace=True)

# Garantir colunas obrigatórias
colunas_obrigatorias = ['orgao', 'objeto', 'valor_estimado', 'data_publicacao', 
                        'uf', 'municipio', 'numero_edital', 'modalidade', 'status']

for col in colunas_obrigatorias:
    if col not in df.columns:
        if col == 'data_publicacao':
            # Gerar datas aleatórias dos últimos 7 dias
            base = datetime.now()
            df[col] = [base - timedelta(days=np.random.randint(0, 7)) for _ in range(len(df))]
        elif col == 'municipio':
            df[col] = 'São Paulo'  # Placeholder
        elif col == 'numero_edital':
            df[col] = df.index.astype(str)
        elif col == 'status':
            df[col] = 'Publicada'
        else:
            df[col] = 'N/A'

# Reordenar colunas
df = df[colunas_obrigatorias]

# Salvar
output_path = 'dados/licitacoes.csv'
df.to_csv(output_path, index=False, encoding='utf-8')

print(f"\n✅ Salvo em: {output_path}")
print(f"📊 Total de registros: {len(df)}")
print(f"🗺️  UFs distribuídas:")

ufs_count = df['uf'].value_counts().sort_index()
for uf, count in ufs_count.items():
    nome = UF_NOMES.get(uf, uf)
    print(f"   {uf} - {nome:20} → {count:3} registros")

print(f"\n💾 Dashboard vai carregar este arquivo automaticamente!")
print(f"🚀 Recarregue o dashboard no navegador para ver as mudanças!")
