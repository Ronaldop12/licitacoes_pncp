"""
Script simples para aguardar conclusão da coleta e mostrar resultado final
"""

import subprocess
import time
import os

print("=" * 70)
print("INICIANDO COLETA DE LICITAÇÕES DE TI")
print("=" * 70)
print()
print("Aguarde... isto pode levar alguns minutos...")
print()

# Executar script de coleta
processo = subprocess.Popen(
    ["python", "pncp_radar_ti_plus.py"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)

# Monitorar saída
ultima_linha_importante = ""
while True:
    linha = processo.stdout.readline()
    if not linha:
        break
    
    # Mostrar apenas linhas importantes
    if "Total coletado:" in linha or "FINALIZADA" in linha or "COLETA FINALIZADA" in linha:
        print(linha.strip())
        ultima_linha_importante = linha
    elif "ERRO" in linha or "Erro" in linha:
        print(f"  ⚠ {linha.strip()}")

# Aguardar conclusão
processo.wait()

print()
print("=" * 70)
print("COLETA CONCLUÍDA!")
print("=" * 70)
print()

# Verificar arquivos de saída
if os.path.exists("radar_licitacoes_TI_PRO.xlsx"):
    tamanho = os.path.getsize("radar_licitacoes_TI_PRO.xlsx") / 1024
    print(f"✓ Arquivo Excel criado: radar_licitacoes_TI_PRO.xlsx ({tamanho:.1f} KB)")

if os.path.exists("dados/licitacoes.csv"):
    tamanho = os.path.getsize("dados/licitacoes.csv") / 1024
    print(f"✓ Arquivo CSV criado: dados/licitacoes.csv ({tamanho:.1f} KB)")

print()
print("Próximo passo: streamlit run dashboard.py")
