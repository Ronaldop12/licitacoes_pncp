"""
Gerar dados de teste expandidos com distribuição entre múltiplos estados
"""
import pandas as pd
from datetime import datetime, timedelta
import random

# Definir seed para reprodutibilidade
random.seed(42)

# Estados brasileiros principais
ESTADOS = ['SP', 'RJ', 'MG', 'BA', 'SC', 'PR', 'PE', 'PA', 'GO', 'DF']

# Órgãos de exemplo
ORGAOS_BASE = [
    'GOVERNO DO ESTADO DE',
    'SECRETARIA ESTADUAL DE',
    'PREFEITURA DE',
    'SECRETARIA MUNICIPAL DE',
    'UNIVERSIDADE FEDERAL DE',
    'INSTITUTO FEDERAL DE',
]

# Cidades grandes por estado
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

# Palavras-chave de TI
PALAVRAS_TI = [
    'software', 'cloud', 'dados', 'infraestrutura', 'rede', 'servidor',
    'sistema', 'plataforma', 'web', 'aplicativo', 'consultoria', 'tecnologia',
    'infraestrutura de TI', 'transformação digital', 'computadores', 'licenças'
]

# Gerar 100 registros
registros = []
numero_edital_base = 1234567800000
for i in range(100):
    estado = random.choice(ESTADOS)
    cidade = random.choice(CIDADES.get(estado, ['Capital']))
    
    # Gerar órgão
    prefixo = random.choice(ORGAOS_BASE)
    if 'ESTADO' in prefixo or 'Federal' in prefixo or 'Instituto' in prefixo:
        orgao = f"{prefixo} {estado}"
    else:
        orgao = f"{prefixo} {cidade.upper()}"
    
    # Objeto (descrição)
    palavra_ti = random.choice(PALAVRAS_TI)
    quantidade = random.randint(1, 5)
    objeto = f"{'Contratação' if i % 2 == 0 else 'Aquisição'} de {quantidade}x {palavra_ti} para {orgao.lower()}"
    
    # Valor entre 50k e 2M
    valor = round(random.uniform(50000, 2000000), 2)
    
    # Data nos últimos 90 dias
    dias_atras = random.randint(0, 90)
    data_pub = (datetime.now() - timedelta(days=dias_atras)).strftime('%Y-%m-%d')
    
    # Número de edital único
    numero_edital = f"{numero_edital_base + i:020d}-1"
    
    registros.append({
        'origem': 'PNCP API',
        'orgao': orgao,
        'valor_estimado': valor,
        'objeto': objeto,
        'numero_controle_pncp': numero_edital,
        'uf': estado,
        'data_publicacao': data_pub,
    })

df = pd.DataFrame(registros)

# Salvar CSV
import os
os.makedirs('dados', exist_ok=True)
df.to_csv('dados/licitacoes.csv', index=False, encoding='utf-8')

print(f"✓ CSV gerado: dados/licitacoes.csv com {len(df)} registros")
print(f"\nDistribuição por UF:")
print(df['uf'].value_counts().sort_index())
print(f"\nValor mínimo: R$ {df['valor_estimado'].min():,.2f}")
print(f"Valor máximo: R$ {df['valor_estimado'].max():,.2f}")
print(f"Valor médio: R$ {df['valor_estimado'].mean():,.2f}")
