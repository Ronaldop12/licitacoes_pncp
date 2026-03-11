"""
========================================
TESTES INICIAIS - Verificação do Sistema
========================================
Este script testa se tudo está funcionando corretamente
"""

import os
import sys
from pathlib import Path

print("\n" + "="*60)
print("TESTE DO SISTEMA - Radar de Licitações de TI")
print("="*60 + "\n")

# Testes
testes_ok = 0
testes_erro = 0

# 1. Verificar Python
print("[1/7] Verificando versão Python...")
try:
    if sys.version_info >= (3, 10):
        print(f"  ✓ Python {sys.version.split()[0]} OK")
        testes_ok += 1
    else:
        print(f"  ✗ Python {sys.version.split()[0]} - Require 3.10+")
        testes_erro += 1
except Exception as e:
    print(f"  ✗ Erro: {e}")
    testes_erro += 1

# 2. Verificar arquivos principais
print("\n[2/7] Verificando arquivos principais...")
arquivos_obrigatorios = [
    "pncp_radar_ti_plus.py",
    "dashboard.py",
    "requirements.txt",
]

for arquivo in arquivos_obrigatorios:
    if os.path.exists(arquivo):
        tamanho = os.path.getsize(arquivo) / 1024  # KB
        print(f"  ✓ {arquivo} ({tamanho:.1f} KB)")
        testes_ok += 1
    else:
        print(f"  ✗ {arquivo} NÃO ENCONTRADO")
        testes_erro += 1

# 3. Verificar módulos
print("\n[3/7] Verificando módulos Python...")
modulos = {
    'requests': 'HTTP requests',
    'pandas': 'Processamento de dados',
    'openpyxl': 'Exportação Excel',
    'streamlit': 'Dashboard',
    'plotly': 'Gráficos',
}

for modulo, descricao in modulos.items():
    try:
        __import__(modulo)
        print(f"  ✓ {modulo:15} - {descricao}")
        testes_ok += 1
    except ImportError:
        print(f"  ✗ {modulo:15} - NÃO INSTALADO")
        testes_erro += 1

# 4. Verificar diretórios
print("\n[4/7] Verificando diretórios...")
diretorios = ['dados']

for diretorio in diretorios:
    if os.path.exists(diretorio):
        print(f"  ✓ Diretório '{diretorio}' existe")
        testes_ok += 1
    else:
        print(f"  ⚠ Diretório '{diretorio}' será criado na primeira execução")

# 5. Verificar conexão (opcional)
print("\n[5/7] Testando conexão com API PNCP...")
try:
    import requests
    resposta = requests.get(
        "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao",
        params={"offset": 0, "limit": 1},
        timeout=10
    )
    
    if resposta.status_code in [200, 204]:
        print(f"  ✓ API PNCP respondendo (HTTP {resposta.status_code})")
        testes_ok += 1
    else:
        print(f"  ⚠ API retornou HTTP {resposta.status_code}")
        
except requests.Timeout:
    print("  ⚠ Timeout na API PNCP (pode estar lenta)")
except requests.ConnectionError:
    print("  ⚠ Erro de conexão - verifique internet")
except Exception as e:
    print(f"  ⚠ Erro ao testar API: {e}")

# 6. Verificar permissões de escrita
print("\n[6/7] Verificando permissões de escrita...")
try:
    arquivo_teste = Path("teste_permissao.tmp")
    arquivo_teste.write_text("teste")
    arquivo_teste.unlink()
    print("  ✓ Permissão de escrita OK")
    testes_ok += 1
except Exception as e:
    print(f"  ✗ Sem permissão de escrita: {e}")
    testes_erro += 1

# 7. Verificar espaço em disco
print("\n[7/7] Verificando espaço em disco...")
try:
    import shutil
    disco = shutil.disk_usage(".")
    livre_gb = disco.free / (1024**3)
    
    if livre_gb > 1:
        print(f"  ✓ {livre_gb:.1f} GB livres")
        testes_ok += 1
    else:
        print(f"  ⚠ Apenas {livre_gb:.1f} GB livres - pode precisar mais")
        
except Exception as e:
    print(f"  ⚠ Erro ao checar disco: {e}")

# Resumo
print("\n" + "="*60)
print(f"RESULTADO: {testes_ok} OK, {testes_erro} ERRO")
print("="*60)

if testes_erro == 0:
    print("\n✓ SISTEMA PRONTO! Você pode começar a usar.\n")
    print("Próximas ações:")
    print("  1. Executar: python pncp_radar_ti_plus.py")
    print("  2. Abrir:    streamlit run dashboard.py")
    sys.exit(0)
else:
    print("\n✗ EXISTEM PROBLEMAS. Por favor, resolva antes de continuar.\n")
    print("Dicas:")
    print("  - Reinstale dependências: pip install -r requirements.txt")
    print("  - Verifique sua internet")
    print("  - Leia INSTRUCOES.md para mais detalhes")
    sys.exit(1)
