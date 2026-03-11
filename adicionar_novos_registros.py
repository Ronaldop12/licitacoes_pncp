"""
Adicionar novos registros de teste para simular licitações recém-publicadas
"""
import pandas as pd
from datetime import datetime
import random

# Estados principais
ESTADOS = ['SP', 'RJ', 'MG', 'BA', 'SC', 'PR', 'PE', 'PA', 'GO', 'DF']
CIDADES = {
    'SP': ['São Paulo', 'Campinas', 'Sorocaba', 'Santos'],
    'RJ': ['Rio de Janeiro', 'Niterói', 'Nova Iguaçu'],
    'MG': ['Belo Horizonte', 'Uberlândia', 'Montes Claros'],
    'BA': ['Salvador', 'Feira de Santana', 'Vitória da Conquista'],
    'SC': ['Florianópolis', 'Blumenau', 'Joinville'],
    'PR': ['Curitiba', 'Londrina', 'Maringá'],
    'PE': ['Recife', 'Olinda', 'Caruaru'],
    'PA': ['Belém', 'Santarém', 'Marabá'],
    'GO': ['Goiânia', 'Anápolis', 'Trindade'],
    'DF': ['Brasília'],
}

PALAVRAS_TI = [
    'software', 'cloud', 'dados', 'infraestrutura', 'rede', 'servidor',
    'sistema', 'plataforma', 'web', 'aplicativo', 'consultoria', 'tecnologia',
]

# Carregar dados existentes
df_existente = pd.read_csv('dados/licitacoes.csv')

# Adicionar 20 novos registros
novos_registros = []
numero_edital_base = int(df_existente['numero_controle_pncp'].iloc[-1].split('-')[0]) + 1

for i in range(20):
    estado = random.choice(ESTADOS)
    cidade = random.choice(CIDADES.get(estado, ['Capital']))
    
    orgao = f"SECRETARIA MUNICIPAL DE {cidade.upper()}"
    palavra_ti = random.choice(PALAVRAS_TI)
    objeto = f"{'Contratação' if i % 2 == 0 else 'Aquisição'} de {random.randint(1,5)}x {palavra_ti} para {orgao.lower()}"
    
    valor = round(random.uniform(50000, 2000000), 2)
    numero_edital = f"{numero_edital_base + i:020d}-1"
    
    novos_registros.append({
        'origem': 'PNCP API',
        'orgao': orgao,
        'valor_estimado': valor,
        'objeto': objeto,
        'numero_controle_pncp': numero_edital,
        'uf': estado,
        'data_publicacao': datetime.now().strftime('%Y-%m-%d'),
    })

df_novos = pd.DataFrame(novos_registros)
df_final = pd.concat([df_existente, df_novos], ignore_index=True)

df_final.to_csv('dados/licitacoes.csv', index=False, encoding='utf-8')

print(f"✓ Adicionados 20 novos registros")
print(f"Total agora: {len(df_final)} registros")
print(f"\nDistribuição por UF:")
print(df_final['uf'].value_counts().sort_index())
