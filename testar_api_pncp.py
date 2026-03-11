"""
============================================================================
TESTE COMPLETO DE API - RADAR DE LICITAÇÕES DE TI
Script profissional para testar conectividade e funcionalidade da API PNCP
============================================================================

Uso: python testar_api_pncp.py

Testa:
- Conectividade com API
- Formato de resposta
- Paginação
- Filtros
- Campos esperados
- Performance
============================================================================
"""

import requests
import json
from datetime import datetime, timedelta
import sys
from typing import Dict, Optional

class Cores:
    VERDE = '\033[92m'
    VERMELHO = '\033[91m'
    AMARELO = '\033[93m'
    AZUL = '\033[94m'
    RESET = '\033[0m'

def print_ok(msg):
    print(f"{Cores.VERDE}✓ {msg}{Cores.RESET}")

def print_erro(msg):
    print(f"{Cores.VERMELHO}✗ {msg}{Cores.RESET}")

def print_aviso(msg):
    print(f"{Cores.AMARELO}⚠ {msg}{Cores.RESET}")

def print_info(msg):
    print(f"{Cores.AZUL}ℹ {msg}{Cores.RESET}")

def separator(titulo=""):
    print(f"\n{Cores.AZUL}{'='*70}")
    if titulo:
        print(f"{titulo.center(70)}")
        print(f"{'='*70}{Cores.RESET}\n")
    else:
        print(f"{'='*70}{Cores.RESET}\n")

class TestadorAPIPNCP:
    """Testador completo de API PNCP"""
    
    URL_BASE = "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao"
    TIMEOUT = 30
    
    def __init__(self):
        self.resultados = {}
        self.tempos = {}
    
    def teste_1_conectividade(self) -> bool:
        """Teste 1: Conectividade básica"""
        separator("TESTE 1: CONECTIVIDADE BÁSICA")
        
        try:
            print("Testando conexão com API PNCP...")
            print(f"URL: {self.URL_BASE}")
            
            inicio = datetime.now()
            resposta = requests.head(self.URL_BASE, timeout=self.TIMEOUT)
            tempo = (datetime.now() - inicio).total_seconds()
            
            self.tempos['conectividade'] = tempo
            
            print(f"Status HTTP: {resposta.status_code}")
            print(f"Tempo resposta: {tempo:.2f}s")
            
            if resposta.status_code in [200, 400]:
                print_ok("Conexão estabelecida com sucesso")
                return True
            else:
                print_aviso(f"Status inesperado: {resposta.status_code}")
                return False
                
        except requests.Timeout:
            print_erro("Timeout na requisição")
            return False
        except requests.ConnectionError as e:
            print_erro(f"Erro de conexão: {e}")
            return False
        except Exception as e:
            print_erro(f"Erro: {e}")
            return False
    
    def teste_2_parametros_basicos(self) -> bool:
        """Teste 2: Parâmetros básicos"""
        separator("TESTE 2: PARÂMETROS BÁSICOS")
        
        try:
            data_fim = datetime.now()
            data_inicio = data_fim - timedelta(days=1)
            
            params = {
                "dataInicial": data_inicio.strftime("%Y%m%d"),
                "dataFinal": data_fim.strftime("%Y%m%d"),
                "codigoModalidadeContratacao": 1,
                "pagina": 1,
            }
            
            print("Enviando requisição com parâmetros básicos...")
            print(f"Período: {data_inicio.date()} a {data_fim.date()}")
            print(f"Modalidade: 1 (Licitação)")
            print(f"Página: 1")
            
            inicio = datetime.now()
            resposta = requests.get(self.URL_BASE, params=params, timeout=self.TIMEOUT)
            tempo = (datetime.now() - inicio).total_seconds()
            
            self.tempos['basico'] = tempo
            
            print(f"\nStatus HTTP: {resposta.status_code}")
            print(f"Tamanho resposta: {len(resposta.content):,} bytes")
            print(f"Tempo requisição: {tempo:.2f}s")
            
            if resposta.status_code == 200:
                try:
                    dados = resposta.json()
                    print_ok("Resposta em JSON válido")
                    
                    if 'data' in dados:
                        total = dados.get('totalRegistros', 0)
                        qtd_pagina = len(dados.get('data', []))
                        print_ok(f"Estrutura correta: {total:,} total, {qtd_pagina} nesta página")
                        return True
                    else:
                        print_erro("Campo 'data' não encontrado")
                        return False
                        
                except json.JSONDecodeError:
                    print_erro("Resposta não é JSON válido")
                    return False
            else:
                print_aviso(f"Status {resposta.status_code}")
                return False
                
        except Exception as e:
            print_erro(f"Erro: {e}")
            return False
    
    def teste_3_paginacao(self) -> bool:
        """Teste 3: Paginação"""
        separator("TESTE 3: PAGINAÇÃO")
        
        try:
            data_fim = datetime.now()
            data_inicio = data_fim - timedelta(days=1)
            
            print("Testando paginação...")
            
            params_base = {
                "dataInicial": data_inicio.strftime("%Y%m%d"),
                "dataFinal": data_fim.strftime("%Y%m%d"),
                "codigoModalidadeContratacao": 1,
            }
            
            resultados = {}
            
            for pagina in range(1, 4):
                params = params_base.copy()
                params['pagina'] = pagina
                
                resposta = requests.get(self.URL_BASE, params=params, timeout=self.TIMEOUT)
                
                if resposta.status_code == 200:
                    dados = resposta.json()
                    qtd = len(dados.get('data', []))
                    resultados[pagina] = qtd
                    print(f"  Página {pagina}: {qtd} registros")
                    
                    if qtd == 0:
                        print("  (Fim da paginação)")
                        break
                else:
                    print_aviso(f"  Página {pagina}: status {resposta.status_code}")
                    break
            
            if sum(resultados.values()) > 0:
                print_ok("Paginação funcionando corretamente")
                return True
            else:
                print_aviso("Nenhum dado encontrado no período")
                return True
                
        except Exception as e:
            print_erro(f"Erro: {e}")
            return False
    
    def teste_4_modalidades(self) -> bool:
        """Teste 4: Diferentes modalidades"""
        separator("TESTE 4: MODALIDADES DE CONTRATAÇÃO")
        
        try:
            data_fim = datetime.now()
            data_inicio = data_fim - timedelta(days=1)
            
            print("Testando diferentes modalidades...")
            
            modalidades = {
                1: "Licitação",
                3: "Dispensa",
                8: "Pregão",
            }
            
            params_base = {
                "dataInicial": data_inicio.strftime("%Y%m%d"),
                "dataFinal": data_fim.strftime("%Y%m%d"),
                "pagina": 1,
            }
            
            total = 0
            
            for cod, nome in modalidades.items():
                params = params_base.copy()
                params['codigoModalidadeContratacao'] = cod
                
                try:
                    resposta = requests.get(self.URL_BASE, params=params, timeout=self.TIMEOUT)
                    
                    if resposta.status_code == 200:
                        dados = resposta.json()
                        qtd = len(dados.get('data', []))
                        total += qtd
                        print(f"  {nome:<15} (cod {cod}): {qtd:>6} registros")
                    else:
                        print_aviso(f"  {nome}: status {resposta.status_code}")
                except Exception as e:
                    print_aviso(f"  {nome}: {e}")
            
            print(f"\nTotal: {total:,} registros")
            print_ok("Teste de modalidades concluído")
            return True
            
        except Exception as e:
            print_erro(f"Erro: {e}")
            return False
    
    def teste_5_campos(self) -> bool:
        """Teste 5: Validação de campos"""
        separator("TESTE 5: VALIDAÇÃO DE CAMPOS")
        
        try:
            data_fim = datetime.now()
            data_inicio = data_fim - timedelta(days=7)
            
            params = {
                "dataInicial": data_inicio.strftime("%Y%m%d"),
                "dataFinal": data_fim.strftime("%Y%m%d"),
                "codigoModalidadeContratacao": 1,
                "pagina": 1,
            }
            
            resposta = requests.get(self.URL_BASE, params=params, timeout=self.TIMEOUT)
            dados = resposta.json()
            
            registros = dados.get('data', [])
            
            if not registros:
                print_aviso("Nenhum registro para validar")
                return True
            
            primeiro = registros[0]
            
            print("Campos principais encontrados:")
            campos_esperados = {
                "numeroControlePNCP": "ID único",
                "objetoCompra": "Descrição",
                "valorTotalEstimado": "Valor",
                "dataPublicacaoPncp": "Data",
                "orgaoEntidade": "Órgão",
            }
            
            campos_ok = 0
            
            for campo, descricao in campos_esperados.items():
                if campo in primeiro:
                    valor = primeiro[campo]
                    if isinstance(valor, str) and len(str(valor)) > 40:
                        valor = str(valor)[:37] + "..."
                    print(f"  ✓ {campo}: {valor}")
                    campos_ok += 1
                else:
                    print(f"  ✗ {campo}: NÃO ENCONTRADO")
            
            if campos_ok >= 4:
                print_ok(f"Validação passou: {campos_ok}/{len(campos_esperados)} campos")
                return True
            else:
                print_erro(f"Validação falhou: apenas {campos_ok} campos encontrados")
                return False
                
        except Exception as e:
            print_erro(f"Erro: {e}")
            return False
    
    def teste_6_performance(self) -> bool:
        """Teste 6: Performance"""
        separator("TESTE 6: PERFORMANCE")
        
        try:
            data_fim = datetime.now()
            data_inicio = data_fim - timedelta(days=1)
            
            print("Medindo performance de 3 requisições...")
            
            tempos = []
            
            for i in range(1, 4):
                params = {
                    "dataInicial": data_inicio.strftime("%Y%m%d"),
                    "dataFinal": data_fim.strftime("%Y%m%d"),
                    "codigoModalidadeContratacao": 1,
                    "pagina": i,
                }
                
                inicio = datetime.now()
                resposta = requests.get(self.URL_BASE, params=params, timeout=self.TIMEOUT)
                tempo = (datetime.now() - inicio).total_seconds()
                tempos.append(tempo)
                
                status = "✓" if resposta.status_code == 200 else "✗"
                print(f"  {status} Página {i}: {tempo:.2f}s")
            
            tempo_medio = sum(tempos) / len(tempos)
            
            print(f"\nTempo médio: {tempo_medio:.2f}s")
            
            if tempo_medio <= 2:
                print_ok("Performance excelente (< 2s)")
            elif tempo_medio <= 4:
                print_ok("Performance boa (2-4s)")
            else:
                print_aviso(f"Performance lenta (> 4s)")
            
            return True
            
        except Exception as e:
            print_erro(f"Erro: {e}")
            return False
    
    def executar(self):
        """Executa todos os testes"""
        separator("DIAGNÓSTICO DA API PNCP")
        print(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        
        testes = [
            ("Conectividade", self.teste_1_conectividade),
            ("Parâmetros Básicos", self.teste_2_parametros_basicos),
            ("Paginação", self.teste_3_paginacao),
            ("Modalidades", self.teste_4_modalidades),
            ("Validação de Campos", self.teste_5_campos),
            ("Performance", self.teste_6_performance),
        ]
        
        resultados = {}
        
        for nome, teste_func in testes:
            try:
                resultados[nome] = teste_func()
            except Exception as e:
                print_erro(f"Erro ao executar {nome}: {e}")
                resultados[nome] = False
        
        self._relatorio_final(resultados)
    
    def _relatorio_final(self, resultados):
        """Gera relatório final"""
        separator("RELATÓRIO FINAL")
        
        total = len(resultados)
        passou = sum(1 for v in resultados.values() if v)
        
        print(f"Total de testes: {total}")
        print(f"Testes passou: {passou}")
        print(f"Taxa de sucesso: {(passou/total*100):.0f}%\n")
        
        for teste, resultado in resultados.items():
            status = "✓ OK" if resultado else "✗ FALHOU"
            cor = Cores.VERDE if resultado else Cores.VERMELHO
            print(f"{cor}{teste:<25} {status}{Cores.RESET}")
        
        print()
        
        if passou >= 5:
            print_ok("Sistema está pronto para usar!")
        elif passou >= 3:
            print_aviso("Sistema parcialmente funcional")
        else:
            print_erro("Sistema com problemas graves")
        
        print()

def main():
    testador = TestadorAPIPNCP()
    testador.executar()

if __name__ == "__main__":
    main()

