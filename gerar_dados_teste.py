"""
Criar dados de teste para validar dashboard
"""
import pandas as pd
from datetime import datetime, timedelta
import json

# Dados de teste
dados_teste = {
    'orgao': [
        'MUNICIPIO DE BELA VISTA DO CAROBA',
        'MUNICIPIO DE BAIANOPOLIS', 
        'MUNICIPIO DE REMANSO',
        'GOVERNO DO ESTADO DE SÃO PAULO',
        'SECRETARIA MUNICIPAL DE EDUCAÇÃO',
    ],
    'objeto': [
        'Contratação de serviços de software para gestão educacional',
        'Implementação de sistema de TI para administração municipal',
        'Desenvolvimento de plataforma web cloud para dados públicos',
        'Aquisição de licenças de software e infraestrutura IT',
        'Contratação de consultoria em transformação digital',
    ],
    'valor_estimado': [55800.0, 468000.0, 1560000.0, 385723.0, 750000.0],
    'data_publicacao': [
        '2026-03-01',
        '2026-03-02',
        '2026-03-03',
        '2026-03-04',
        '2026-03-05',
    ],
    'uf': ['SP', 'BA', 'BA', 'SP', 'RJ'],
    'municipio': ['Bela Vista do Caroba', 'Baianópolis', 'Remanso', 'São Paulo', 'Rio de Janeiro'],
    'numero_edital': [
        '01612441000107-1-000008/2026',
        '13654413000131-1-000006/2026',
        '13909247000177-1-000037/2026',
        '08924037000118-1-000007/2026',
        '12345678000190-1-000001/2026',
    ],
    'modalidade': ['Pregão Eletrônico', 'Dispensa de Licitação', 'Leilão Eletrônico', 'Pregão', 'Licitação'],
    'status': ['Divulgada', 'Divulgada', 'Divulgada', 'Divulgada', 'Divulgada'],
}

# Criar DataFrame
df = pd.DataFrame(dados_teste)

# Salvar como CSV na pasta de dados
import os
os.makedirs('dados', exist_ok=True)

df.to_csv('dados/licitacoes.csv', index=False, encoding='utf-8')
print(f"✓ Arquivo criado: dados/licitacoes.csv com {len(df)} registros")

# Salvar como Excel também
df.to_excel('radar_licitacoes_TI_PRO.xlsx', index=False)
print(f"✓ Arquivo criado: radar_licitacoes_TI_PRO.xlsx")

# Salvar estado
estado = {
    'total_ti': len(df),
    'total_licitacoes': len(df) * 5,  # Simulando 5x mais licitações verificadas
    'data_execucao': datetime.now().isoformat(),
}

with open('radar_state.json', 'w', encoding='utf-8') as f:
    json.dump(estado, f, indent=2)

print(f"✓ Arquivo criado: radar_state.json")
print()
print("Dados de teste gerados! Dashboard deve carregar agora.")
