"""Teste de URL de edital"""
from utils_telegram import TelegramAlerter
import json

# Criar um alertador (apenas para acessar a função de formatação)
bot = TelegramAlerter(token="teste_token")

# Dados de teste
teste_licitacao = {
    'orgao': 'SECRETARIA MUNICIPAL DE SANTARÉM',
    'objeto': 'Aquisição de 2x licenças para secretaria municipal de santarém',
    'valor_estimado': 420300.84,
    'uf': 'PA',
    'municipio': 'Santarém',
    'data_publicacao': '2026-02-08',
    'numero_edital': '00000001234567800039-1'
}

# Formatar mensagem
msg = bot.formatar_alerta_licitacao(teste_licitacao)

print("=" * 80)
print("MENSAGEM FORMATADA PARA TELEGRAM:")
print("=" * 80)
print(msg)
print("\n" + "=" * 80)
print("TESTANDO LINK:")
print("=" * 80)

# Extrair o link da mensagem
import re
link_match = re.search(r'href="([^"]+)"', msg)
if link_match:
    link = link_match.group(1)
    print(f"✓ Link encontrado: {link}")
    print(f"\nVocê pode testar abrindo: {link}")
else:
    print("✗ Nenhum link encontrado")
