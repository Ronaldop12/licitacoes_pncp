"""
============================================================================
SCRIPT DE DIAGNÓSTICO DO SISTEMA RADAR DE LICITAÇÕES DE TI
Testa conectividade, API, configurações e dependências
============================================================================
"""

import sys
import requests
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import logging

# Configurar cores para output
class Cores:
    VERDE = '\033[92m'
    VERMELHO = '\033[91m'
    AMARELO = '\033[93m'
    AZUL = '\033[94m'
    RESET = '\033[0m'
    BRANCO = '\033[37m'

    @staticmethod
    def ok(msg):
        return f"{Cores.VERDE}✓ {msg}{Cores.RESET}"
    
    @staticmethod
    def erro(msg):
        return f"{Cores.VERMELHO}✗ {msg}{Cores.RESET}"
    
    @staticmethod
    def aviso(msg):
        return f"{Cores.AMARELO}⚠ {msg}{Cores.RESET}"
    
    @staticmethod
    def info(msg):
        return f"{Cores.AZUL}ℹ {msg}{Cores.RESET}"

def separator(titulo=""):
    print(f"\n{Cores.AZUL}{'='*70}")
    if titulo:
        print(f"{titulo.center(70)}")
        print(f"{'='*70}{Cores.RESET}\n")
    else:
        print(f"{'='*70}{Cores.RESET}\n")

def testa_ambiente_python():
    """Testa configuração do ambiente Python"""
    separator("🐍 AMBIENTE PYTHON")
    
    print(f"Versão Python: {sys.version}")
    
    # Verificar version
    version_major = sys.version_info.major
    version_minor = sys.version_info.minor
    
    if version_major >= 3 and version_minor >= 10:
        print(Cores.ok(f"Python {version_major}.{version_minor} (Suportado)"))
    else:
        print(Cores.aviso(f"Python {version_major}.{version_minor} (Recomendado: 3.10+)"))
    
    # Verificar executável
    print(f"Executável: {sys.executable}")

def testa_dependencias():
    """Testa se todas as dependências estão instaladas"""
    separator("📦 DEPENDÊNCIAS")
    
    dependencias = {
        'requests': 'Requisições HTTP',
        'pandas': 'Processamento de dados',
        'openpyxl': 'Exportação Excel',
        'streamlit': 'Dashboard interativo',
        'plotly': 'Gráficos interativos',
    }
    
    faltam = []
    
    for modulo, descricao in dependencias.items():
        try:
            __import__(modulo)
            print(Cores.ok(f"{modulo:<15} - {descricao}"))
        except ImportError:
            print(Cores.erro(f"{modulo:<15} - {descricao} (NÃO INSTALADO)"))
            faltam.append(modulo)
    
    if faltam:
        print(f"\n{Cores.aviso('Para instalar as dependências faltantes:')}")
        print(f"pip install {' '.join(faltam)}\n")
        return False
    
    return True

def testa_conectividade_internet():
    """Testa conexão com a internet"""
    separator("🌐 CONECTIVIDADE INTERNET")
    
    try:
        print("Testando conexão com Google...")
        resposta = requests.get("https://www.google.com", timeout=5)
        print(Cores.ok("Conexão com a internet OK"))
        return True
    except Exception as e:
        print(Cores.erro(f"Falha de conexão: {e}"))
        return False

def testa_api_pncp():
    """Testa conectividade com a API do PNCP"""
    separator("📡 API DO PNCP")
    
    api_url = "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao"
    
    data_fim = datetime.now()
    data_inicio = data_fim - timedelta(days=1)
    
    params = {
        "dataInicial": data_inicio.strftime("%Y%m%d"),
        "dataFinal": data_fim.strftime("%Y%m%d"),
        "codigoModalidadeContratacao": 1,
        "pagina": 1,
    }
    
    try:
        print(f"Testando endpoint: {api_url}")
        print(f"Período: {data_inicio.date()} a {data_fim.date()}")
        print()
        
        resposta = requests.get(api_url, params=params, timeout=10)
        
        print(f"Status HTTP: {resposta.status_code}")
        
        if resposta.status_code == 200:
            dados = resposta.json()
            
            total_licitacoes = dados.get("totalRegistros", 0)
            registros_pagina = len(dados.get("data", []))
            
            print(Cores.ok(f"Conexão com API OK"))
            print(f"  Total de registros encontrados: {total_licitacoes:,}")
            print(f"  Registros nesta página: {registros_pagina}")
            
            if registros_pagina > 0:
                print(f"\n{Cores.info('Amostra do primeiro registro:')}")
                primeiro = dados.get("data", [])[0]
                print(f"  Órgão: {primeiro.get('orgaoEntidade', {}).get('razaoSocial', 'N/A')}")
                print(f"  Objeto: {primeiro.get('objetoCompra', 'N/A')[:80]}...")
                print(f"  Valor: R$ {primeiro.get('valorTotalEstimado', 0):,.2f}")
            
            return True
            
        elif resposta.status_code == 204:
            print(Cores.aviso("API respondeu sem conteúdo (status 204)"))
            return True
        else:
            print(Cores.erro(f"Erro HTTP {resposta.status_code}"))
            return False
            
    except requests.Timeout:
        print(Cores.erro("Timeout na requisição (API muito lenta)"))
        return False
    except Exception as e:
        print(Cores.erro(f"Erro: {e}"))
        return False

def testa_arquivos_saida():
    """Testa se os diretórios de saída existem"""
    separator("📁 DIRETÓRIOS DE SAÍDA")
    
    diretorio_dados = "dados"
    arquivo_excel = "radar_licitacoes_TI_PRO.xlsx"
    arquivo_csv = os.path.join(diretorio_dados, "licitacoes.csv")
    arquivo_estado = "radar_state.json"
    
    # Verificar/criar diretório dados
    if not os.path.exists(diretorio_dados):
        try:
            os.makedirs(diretorio_dados)
            print(Cores.ok(f"Diretório criado: {diretorio_dados}"))
        except Exception as e:
            print(Cores.erro(f"Erro ao criar diretório: {e}"))
    else:
        print(Cores.ok(f"Diretório existe: {diretorio_dados}"))
    
    # Verificar direitos de escrita
    try:
        arquivo_teste = os.path.join(diretorio_dados, ".teste_escrita")
        with open(arquivo_teste, 'w') as f:
            f.write("teste")
        os.remove(arquivo_teste)
        print(Cores.ok("Permissões de escrita: OK"))
    except PermissionError:
        print(Cores.erro("Sem permissão de escrita no diretório"))
    except Exception as e:
        print(Cores.aviso(f"Problema ao testar escrita: {e}"))
    
    # Verificar arquivos existentes
    print()
    if os.path.exists(arquivo_excel):
        tamanho = os.path.getsize(arquivo_excel)
        print(Cores.ok(f"Excel encontrado: {arquivo_excel} ({tamanho:,} bytes)"))
    else:
        print(f"Excel não encontrado: {arquivo_excel}")
    
    if os.path.exists(arquivo_csv):
        tamanho = os.path.getsize(arquivo_csv)
        registros = len(pd.read_csv(arquivo_csv))
        print(Cores.ok(f"CSV encontrado: {arquivo_csv} ({tamanho:,} bytes, {registros:,} registros)"))
    else:
        print(f"CSV não encontrado: {arquivo_csv}")
    
    if os.path.exists(arquivo_estado):
        with open(arquivo_estado, 'r') as f:
            estado = json.load(f)
            ultima_exec = estado.get('data_execucao', 'N/A')
            total_ti = estado.get('total_ti', 0)
            print(Cores.ok(f"Estado encontrado: Última execução: {ultima_exec}, Total TI: {total_ti:,}"))
    else:
        print(f"Arquivo de estado não encontrado: {arquivo_estado}")

def testa_scripts():
    """Verifica se os arquivos de script existem"""
    separator("📜 SCRIPTS")
    
    scripts = {
        'pncp_radar_ti_plus.py': 'Script de coleta principal',
        'dashboard.py': 'Dashboard Streamlit',
        'executar_radar.bat': 'Script de execução Windows',
        'configurar_agendamento.ps1': 'Configuração de agendamento',
    }
    
    for script, descricao in scripts.items():
        if os.path.exists(script):
            tamanho = os.path.getsize(script)
            print(Cores.ok(f"{script:<30} - {descricao} ({tamanho:,} bytes)"))
        else:
            print(Cores.aviso(f"{script:<30} - {descricao} (NÃO ENCONTRADO)"))

def testa_dashboard_streamlit():
    """Testa se o dashboard pode ser iniciado"""
    separator("📊 DASHBOARD STREAMLIT")
    
    try:
        import streamlit as st
        print(Cores.ok("Streamlit importado com sucesso"))
        print(f"Para iniciar o dashboard, execute:")
        print(f"{Cores.BRANCO}streamlit run dashboard.py{Cores.RESET}")
        return True
    except ImportError:
        print(Cores.erro("Streamlit não instalado"))
        return False

def relatorio_resumido(resultados):
    """Gera relatório final"""
    separator("📋 RESUMO DO DIAGNÓSTICO")
    
    total = len(resultados)
    sucesso = sum(1 for v in resultados.values() if v)
    
    percentual = (sucesso / total * 100) if total > 0 else 0
    
    if percentual >= 90:
        status = Cores.ok("SISTEMA OK - Pronto para usar")
    elif percentual >= 70:
        status = Cores.aviso("SISTEMA COM RESTRIÇÕES - Tente resolver os problemas")
    else:
        status = Cores.erro("SISTEMA COM PROBLEMAS - Corrija os erros antes de usar")
    
    print(status)
    print(f"Status: {sucesso}/{total} testes passaram ({percentual:.0f}%)\n")

def main():
    """Executa todos os testes"""
    print(f"\n{Cores.AZUL}{'='*70}")
    print("DIAGNÓSTICO DO SISTEMA RADAR DE LICITAÇÕES DE TI".center(70))
    print("="*70 + Cores.RESET)
    print(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
    
    resultados = {}
    
    # Executar testes
    resultados['python'] = testa_ambiente_python() or True
    resultados['dependencias'] = testa_dependencias()
    resultados['internet'] = testa_conectividade_internet()
    resultados['api_pncp'] = testa_api_pncp()
    testa_arquivos_saida()
    testa_scripts()
    resultados['streamlit'] = testa_dashboard_streamlit()
    
    # Relatório
    relatorio_resumido(resultados)
    
    print(f"\nPróximos passos:")
    print(f"1. Execute a coleta: {Cores.BRANCO}python pncp_radar_ti_plus.py{Cores.RESET}")
    print(f"2. Abra o dashboard: {Cores.BRANCO}streamlit run dashboard.py{Cores.RESET}")
    print(f"3. Configure automação: {Cores.BRANCO}.\configurar_agendamento.ps1 -Acao criar{Cores.RESET}")
    print()

if __name__ == "__main__":
    main()
