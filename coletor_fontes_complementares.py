"""
========================================
COLETORES DE FONTES COMPLEMENTARES
========================================
Coleta licitações de TI de múltiplas APIs públicas gratuitas:
1. Querido Diário (Open Knowledge Brasil) - Diários Oficiais Municipais
2. Portal da Transparência (CGU) - Contratos Federais
3. Compras.gov.br - Dados Abertos de Contratações

Uso:
    python coletor_fontes_complementares.py

Requisitos:
- requests, pandas
========================================
"""

import requests
import pandas as pd
import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== CONFIGURAÇÕES ====================

OUTPUT_DIR = "dados"
OUTPUT_COMPLEMENTAR = os.path.join(OUTPUT_DIR, "licitacoes_complementares.csv")
OUTPUT_QUERIDO_DIARIO = os.path.join(OUTPUT_DIR, "querido_diario.csv")
OUTPUT_TRANSPARENCIA = os.path.join(OUTPUT_DIR, "portal_transparencia.csv")
OUTPUT_COMPRAS_GOV = os.path.join(OUTPUT_DIR, "compras_gov.csv")
STATE_FILE_COMPLEMENTAR = "radar_state_complementar.json"

PALAVRAS_TI = [
    "software", "sistema", "tecnologia", "informática",
    "informacao", "desenvolvimento", "cloud", "nuvem",
    "api", "dados", "ti ", " ti,", "aplicativo", "licença",
    "licenciamento", "infraestrutura de rede", "segurança da informação",
    "banco de dados", "python", "java", "csharp", "nodejs",
    "docker", "kubernetes", "aws", "azure", "gcp",
    "erp", "lgpd", "computador", "notebook", "servidor",
    "firewall", "antivírus", "backup", "helpdesk", "suporte técnico",
    "rede lógica", "cabeamento estruturado", "data center",
    "inteligência artificial", "machine learning", "devops",
]

MAX_TENTATIVAS = 3
TIMEOUT = 60

# ==================== CLASSE BASE ====================


class ColetorBase:
    """Classe base com funcionalidades comuns de coleta."""

    def __init__(self, nome: str):
        self.nome = nome
        self.dados: List[Dict] = []
        self.erros: List[str] = []
        self.sessao = requests.Session()
        self.sessao.headers.update({
            "Accept": "application/json",
            "User-Agent": "RadarLicitacoesTI-Complementar/1.0",
        })

    def _eh_ti(self, texto: str) -> bool:
        if not texto:
            return False
        texto_lower = str(texto).lower()
        for palavra in PALAVRAS_TI:
            if palavra in texto_lower:
                return True
        return False

    def _fazer_requisicao(self, url: str, params: Optional[Dict] = None,
                          headers: Optional[Dict] = None) -> Optional[Dict]:
        for tentativa in range(MAX_TENTATIVAS):
            try:
                logger.info(f"[{self.nome}] Requisição (tentativa {tentativa + 1}): {url}")
                resp = self.sessao.get(
                    url, params=params, headers=headers or {}, timeout=TIMEOUT
                )

                # Verificar se resposta é JSON
                content_type = resp.headers.get('content-type', '')
                if resp.status_code == 200:
                    if 'json' not in content_type and 'text/html' in content_type:
                        logger.warning(f"[{self.nome}] Resposta HTML em vez de JSON")
                        return None
                    return resp.json()
                if resp.status_code == 204:
                    return None
                if resp.status_code == 429:
                    espera = 10 * (tentativa + 1)
                    logger.warning(f"[{self.nome}] Rate limit. Aguardando {espera}s...")
                    time.sleep(espera)
                    continue
                if resp.status_code >= 500:
                    espera = 5 * (tentativa + 1)
                    logger.warning(f"[{self.nome}] Erro {resp.status_code}. Retry em {espera}s...")
                    time.sleep(espera)
                    continue

                logger.warning(f"[{self.nome}] Status {resp.status_code}: {resp.text[:200]}")
                return None

            except requests.Timeout:
                logger.warning(f"[{self.nome}] Timeout (tentativa {tentativa + 1})")
                time.sleep(2)
            except requests.ConnectionError as e:
                logger.warning(f"[{self.nome}] Erro de conexão: {e}")
                time.sleep(3)
            except Exception as e:
                logger.error(f"[{self.nome}] Erro inesperado: {e}")
                self.erros.append(str(e))
                return None

        logger.error(f"[{self.nome}] Falha após {MAX_TENTATIVAS} tentativas")
        return None

    def exportar_csv(self, caminho: str) -> bool:
        if not self.dados:
            logger.warning(f"[{self.nome}] Nenhum dado para exportar")
            return False
        try:
            diretorio = os.path.dirname(caminho)
            if diretorio and not os.path.exists(diretorio):
                os.makedirs(diretorio)
            df = pd.DataFrame(self.dados)
            df.to_csv(caminho, index=False, encoding="utf-8")
            logger.info(f"[{self.nome}] CSV exportado: {len(df)} registros -> {caminho}")
            return True
        except Exception as e:
            logger.error(f"[{self.nome}] Erro ao exportar: {e}")
            self.erros.append(str(e))
            return False


# ==================== 1. QUERIDO DIÁRIO ====================


class ColetorQueridoDiario(ColetorBase):
    """
    Coleta publicações de diários oficiais municipais via API Querido Diário.
    Fonte: Open Knowledge Brasil - queridodiario.ok.org.br
    Documentação: https://queridodiario.ok.org.br/api/docs
    """

    API_URL = "https://api.queridodiario.ok.org.br/api/gazettes"

    def __init__(self):
        super().__init__("QueridoDiário")

    def coletar(self, dias_atras: int = 7, max_resultados: int = 500) -> List[Dict]:
        logger.info(f"[{self.nome}] Iniciando coleta - últimos {dias_atras} dias")

        data_fim = datetime.now()
        data_inicio = data_fim - timedelta(days=dias_atras)

        # Buscar por cada palavra-chave principal de TI
        keywords_busca = [
            "software", "tecnologia da informação", "sistema de informação",
            "infraestrutura de TI", "cloud computing", "licenciamento software",
            "desenvolvimento sistema", "segurança informação", "ERP",
            "data center", "firewall", "helpdesk",
        ]

        editais_vistos = set()

        for keyword in keywords_busca:
            if len(self.dados) >= max_resultados:
                break

            offset = 0
            tamanho_pagina = 50

            while len(self.dados) < max_resultados:
                params = {
                    "querystring": keyword,
                    "published_since": data_inicio.strftime("%Y-%m-%d"),
                    "published_until": data_fim.strftime("%Y-%m-%d"),
                    "offset": offset,
                    "size": tamanho_pagina,
                }

                resposta = self._fazer_requisicao(self.API_URL, params=params)
                if not resposta:
                    break

                gazettes = resposta.get("gazettes", [])
                if not gazettes:
                    break

                for item in gazettes:
                    excerto = item.get("excerpts", [""])[0] if item.get("excerpts") else ""
                    territorio = item.get("territory_name", "N/A")
                    uf = item.get("state_code", "N/A")

                    # Usar combinação de data + território como ID único
                    chave = f"{item.get('date', '')}_{territorio}_{keyword}"
                    if chave in editais_vistos:
                        continue
                    editais_vistos.add(chave)

                    # Verificar se o texto é relevante para TI
                    texto_completo = f"{excerto} {keyword}"
                    if not self._eh_ti(texto_completo):
                        continue

                    registro = {
                        "orgao": territorio,
                        "objeto": excerto[:500] if excerto else f"Publicação sobre {keyword}",
                        "valor_estimado": 0,
                        "data_publicacao": item.get("date", "N/A"),
                        "uf": uf.upper() if uf else "N/A",
                        "municipio": territorio,
                        "numero_edital": f"QD-{item.get('territory_id', 'NA')}-{item.get('date', 'NA')}",
                        "modalidade": "Diário Oficial",
                        "status": "Publicado",
                        "fonte": "Querido Diário",
                        "url_fonte": item.get("url", ""),
                    }
                    self.dados.append(registro)

                if len(gazettes) < tamanho_pagina:
                    break

                offset += tamanho_pagina
                time.sleep(0.5)

            time.sleep(1)

        logger.info(f"[{self.nome}] Coleta finalizada: {len(self.dados)} publicações de TI")
        return self.dados


# ==================== 2. PORTAL DA TRANSPARÊNCIA ====================


class ColetorPortalTransparencia(ColetorBase):
    """
    Coleta contratos federais do Portal da Transparência (CGU).
    Fonte: api.portaldatransparencia.gov.br
    Documentação: https://api.portaldatransparencia.gov.br/swagger-ui.html
    
    NOTA: Requer chave de API gratuita (cadastro em dados.gov.br)
    """

    API_URL = "https://api.portaldatransparencia.gov.br/api-de-dados/contratos"

    def __init__(self, chave_api: str = ""):
        super().__init__("PortalTransparência")
        self.chave_api = chave_api

    def coletar(self, dias_atras: int = 30, max_resultados: int = 500) -> List[Dict]:
        if not self.chave_api:
            logger.warning(
                f"[{self.nome}] Chave de API não configurada. "
                "Cadastre-se em https://portaldatransparencia.gov.br/api-de-dados/cadastrar-email "
                "para obter uma chave gratuita."
            )
            return self.dados

        logger.info(f"[{self.nome}] Iniciando coleta - últimos {dias_atras} dias")

        data_fim = datetime.now()
        data_inicio = data_fim - timedelta(days=dias_atras)

        pagina = 1
        contratos_vistos = set()

        while len(self.dados) < max_resultados:
            params = {
                "dataInicial": data_inicio.strftime("%d/%m/%Y"),
                "dataFinal": data_fim.strftime("%d/%m/%Y"),
                "pagina": pagina,
            }

            headers = {
                "chave-api-dados": self.chave_api,
            }

            resposta = self._fazer_requisicao(self.API_URL, params=params, headers=headers)
            if not resposta:
                break

            contratos = resposta if isinstance(resposta, list) else resposta.get("data", [])
            if not contratos:
                break

            for item in contratos:
                objeto = item.get("objeto", "")
                if not self._eh_ti(objeto):
                    continue

                numero = item.get("numero", "")
                if numero in contratos_vistos:
                    continue
                contratos_vistos.add(numero)

                orgao_info = item.get("unidadeGestora", {})
                nome_orgao = orgao_info.get("nome", "N/A") if isinstance(orgao_info, dict) else "N/A"

                registro = {
                    "orgao": nome_orgao,
                    "objeto": objeto[:500],
                    "valor_estimado": item.get("valorInicial", 0) or 0,
                    "data_publicacao": item.get("dataInicioVigencia", "N/A"),
                    "uf": item.get("ufContratante", "N/A"),
                    "municipio": "N/A",
                    "numero_edital": f"PT-{numero}",
                    "modalidade": item.get("modalidadeCompra", "Contrato Federal"),
                    "status": item.get("situacao", "N/A"),
                    "fonte": "Portal da Transparência",
                    "url_fonte": f"https://portaldatransparencia.gov.br/contratos/{numero}",
                }
                self.dados.append(registro)

            if len(contratos) < 15:
                break

            pagina += 1
            time.sleep(1)

        logger.info(f"[{self.nome}] Coleta finalizada: {len(self.dados)} contratos de TI")
        return self.dados


# ==================== 3. COMPRAS.GOV.BR ====================


class ColetorComprasGov(ColetorBase):
    """
    Coleta contratações federais via API de Dados Abertos do Compras.gov.br.
    Fonte: dadosabertos.compras.gov.br
    Documentação: https://compras.dados.gov.br/docs/home.html
    """

    API_URL = "https://compras.dados.gov.br/contratos/v1/contratos.json"
    API_URL_LICITACOES = "https://compras.dados.gov.br/licitacoes/v1/licitacoes.json"

    def __init__(self):
        super().__init__("Compras.gov.br")

    def coletar(self, dias_atras: int = 30, max_resultados: int = 500) -> List[Dict]:
        logger.info(f"[{self.nome}] Iniciando coleta - últimos {dias_atras} dias")

        # Tentar ambas as APIs
        for api_url in [self.API_URL, self.API_URL_LICITACOES]:
            dados = self._tentar_api(api_url, dias_atras, max_resultados)
            if dados:
                return dados
        
        logger.warning(f"[{self.nome}] Ambas APIs indisponíveis (serviço fora do ar)")
        return self.dados

    def _tentar_api(self, api_url: str, dias_atras: int, max_resultados: int) -> Optional[List[Dict]]:

        data_fim = datetime.now()
        data_inicio = data_fim - timedelta(days=dias_atras)

        offset = 0
        tamanho_pagina = 50
        contratos_vistos = set()

        while len(self.dados) < max_resultados:
            params = {
                "data_inicio_vigencia_min": data_inicio.strftime("%Y-%m-%d"),
                "data_inicio_vigencia_max": data_fim.strftime("%Y-%m-%d"),
                "offset": offset,
                "limit": tamanho_pagina,
            }

            resposta = self._fazer_requisicao(api_url, params=params)
            if not resposta:
                break

            recursos = resposta.get("_embedded", {}).get("contratos", [])
            if not recursos:
                break

            for item in recursos:
                objeto = item.get("objeto", "")
                if not self._eh_ti(objeto):
                    continue

                numero = item.get("numero", "")
                if numero in contratos_vistos:
                    continue
                contratos_vistos.add(numero)

                registro = {
                    "orgao": item.get("unidade_gestora", {}).get("nome", "N/A"),
                    "objeto": objeto[:500],
                    "valor_estimado": item.get("valor_inicial", 0) or 0,
                    "data_publicacao": item.get("data_inicio_vigencia", "N/A"),
                    "uf": item.get("uf", "N/A"),
                    "municipio": "N/A",
                    "numero_edital": f"CG-{numero}",
                    "modalidade": item.get("modalidade_licitacao", "Contrato Federal"),
                    "status": "Vigente",
                    "fonte": "Compras.gov.br",
                    "url_fonte": f"https://compras.dados.gov.br/contratos/v1/contratos/{numero}.html",
                }
                self.dados.append(registro)

            if len(recursos) < tamanho_pagina:
                break

            offset += tamanho_pagina
            time.sleep(1)

        logger.info(f"[{self.nome}] Coleta finalizada: {len(self.dados)} contratos de TI")
        return self.dados


# ==================== ORQUESTRADOR ====================


class ColetorMultiFontes:
    """Orquestra coleta de todas as fontes complementares."""

    def __init__(self, chave_transparencia: str = ""):
        self.chave_transparencia = chave_transparencia
        self.resultados: Dict[str, List[Dict]] = {}
        self.erros: Dict[str, List[str]] = {}
        self.resumo: Dict = {}

    def coletar_todas(self, dias_atras: int = 7) -> pd.DataFrame:
        logger.info("=" * 60)
        logger.info("COLETA MULTI-FONTES COMPLEMENTARES")
        logger.info("=" * 60)

        todos_dados: List[Dict] = []

        # 1. Querido Diário
        logger.info("\n--- FONTE 1: Querido Diário ---")
        try:
            qd = ColetorQueridoDiario()
            dados_qd = qd.coletar(dias_atras=dias_atras)
            self.resultados["querido_diario"] = dados_qd
            self.erros["querido_diario"] = qd.erros
            todos_dados.extend(dados_qd)
            if dados_qd:
                qd.exportar_csv(OUTPUT_QUERIDO_DIARIO)
            logger.info(f"Querido Diário: {len(dados_qd)} registros")
        except Exception as e:
            logger.error(f"Erro no Querido Diário: {e}")
            self.erros["querido_diario"] = [str(e)]

        # 2. Portal da Transparência
        logger.info("\n--- FONTE 2: Portal da Transparência ---")
        try:
            pt = ColetorPortalTransparencia(chave_api=self.chave_transparencia)
            dados_pt = pt.coletar(dias_atras=min(dias_atras, 30))
            self.resultados["portal_transparencia"] = dados_pt
            self.erros["portal_transparencia"] = pt.erros
            todos_dados.extend(dados_pt)
            if dados_pt:
                pt.exportar_csv(OUTPUT_TRANSPARENCIA)
            logger.info(f"Portal da Transparência: {len(dados_pt)} registros")
        except Exception as e:
            logger.error(f"Erro no Portal da Transparência: {e}")
            self.erros["portal_transparencia"] = [str(e)]

        # 3. Compras.gov.br
        logger.info("\n--- FONTE 3: Compras.gov.br ---")
        try:
            cg = ColetorComprasGov()
            dados_cg = cg.coletar(dias_atras=min(dias_atras, 30))
            self.resultados["compras_gov"] = dados_cg
            self.erros["compras_gov"] = cg.erros
            todos_dados.extend(dados_cg)
            if dados_cg:
                cg.exportar_csv(OUTPUT_COMPRAS_GOV)
            logger.info(f"Compras.gov.br: {len(dados_cg)} registros")
        except Exception as e:
            logger.error(f"Erro no Compras.gov.br: {e}")
            self.erros["compras_gov"] = [str(e)]

        # Consolidar
        logger.info("\n" + "=" * 60)
        logger.info("CONSOLIDANDO RESULTADOS")
        logger.info("=" * 60)

        if not todos_dados:
            logger.warning("Nenhum dado coletado de fontes complementares")
            return pd.DataFrame()

        df = pd.DataFrame(todos_dados)

        # Remover duplicatas por numero_edital
        antes = len(df)
        df = df.drop_duplicates(subset=["numero_edital"], keep="first")
        depois = len(df)
        logger.info(f"Duplicatas removidas: {antes - depois}")

        # Exportar consolidado
        diretorio = os.path.dirname(OUTPUT_COMPLEMENTAR)
        if diretorio and not os.path.exists(diretorio):
            os.makedirs(diretorio)
        df.to_csv(OUTPUT_COMPLEMENTAR, index=False, encoding="utf-8")
        logger.info(f"CSV consolidado exportado: {len(df)} registros -> {OUTPUT_COMPLEMENTAR}")

        # Salvar estado
        self.resumo = {
            "data_execucao": datetime.now().isoformat(),
            "fontes": {
                "querido_diario": len(self.resultados.get("querido_diario", [])),
                "portal_transparencia": len(self.resultados.get("portal_transparencia", [])),
                "compras_gov": len(self.resultados.get("compras_gov", [])),
            },
            "total_coletado": len(df),
            "erros": {k: v for k, v in self.erros.items() if v},
        }

        with open(STATE_FILE_COMPLEMENTAR, "w", encoding="utf-8") as f:
            json.dump(self.resumo, f, indent=4, ensure_ascii=False)

        logger.info(f"\nTotal consolidado: {len(df)} licitações/contratos de TI")
        logger.info(f"Estado salvo em {STATE_FILE_COMPLEMENTAR}")

        return df


# ==================== FUNÇÃO PARA CARREGAR CONFIGURAÇÃO ====================


def carregar_chave_transparencia() -> str:
    """Carrega chave da API do Portal da Transparência de arquivo de config."""
    config_path = os.path.join("config", "api_keys.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            return config.get("portal_transparencia_api_key", "")
        except Exception:
            pass
    return ""


def salvar_chave_transparencia(chave: str) -> None:
    """Salva chave da API em arquivo de config."""
    config_path = os.path.join("config", "api_keys.json")
    config_dir = os.path.dirname(config_path)
    if config_dir and not os.path.exists(config_dir):
        os.makedirs(config_dir)

    config = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception:
            pass

    config["portal_transparencia_api_key"] = chave
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


# ==================== MAIN ====================


def main():
    """Execução principal da coleta complementar."""
    chave = carregar_chave_transparencia()

    coletor = ColetorMultiFontes(chave_transparencia=chave)
    df = coletor.coletar_todas(dias_atras=7)

    logger.info("\n" + "=" * 60)
    logger.info("RESUMO FINAL")
    logger.info("=" * 60)

    for fonte, qtd in coletor.resumo.get("fontes", {}).items():
        status = "✓" if qtd > 0 else "✗"
        logger.info(f"  {status} {fonte}: {qtd} registros")

    logger.info(f"\n  TOTAL: {coletor.resumo.get('total_coletado', 0)} registros consolidados")

    if coletor.resumo.get("erros"):
        logger.warning("\n  ERROS:")
        for fonte, errs in coletor.resumo["erros"].items():
            for err in errs:
                logger.warning(f"    [{fonte}] {err}")

    logger.info("\nEXECUÇÃO CONCLUÍDA")


if __name__ == "__main__":
    main()
