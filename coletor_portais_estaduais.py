"""
Coletor de portais estaduais de licitações.
Coleta de portais públicos estaduais complementando a cobertura do PNCP.

Portais implementados:
  - BEC-SP (Bolsa Eletrônica de Compras de São Paulo)
  - CELIC-RS (Central de Licitações do Rio Grande do Sul)
  - Licitações-e (Banco do Brasil / Licitações Eletrônicas)
"""

import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import requests
import pandas as pd

logger = logging.getLogger(__name__)

OUTPUT_ESTADUAIS = "dados/licitacoes_estaduais.csv"

# Reutilizar classificação TI
from constantes import PALAVRAS_TI, PALAVRAS_EXCLUSAO


def _eh_ti(texto: str) -> bool:
    if not texto:
        return False
    t = texto.lower()
    for exc in PALAVRAS_EXCLUSAO:
        if exc in t:
            return False
    for p in PALAVRAS_TI:
        if p in t:
            return True
    return False


class ColetorBEC_SP:
    """
    Coletor para a Bolsa Eletrônica de Compras de São Paulo.
    API pública: https://www.bec.sp.gov.br/BEC_API
    """

    URL_BASE = "https://www.bec.sp.gov.br/BEC_API/api/OC"

    def __init__(self):
        self.sessao = requests.Session()
        self.sessao.headers.update({
            "Accept": "application/json",
            "User-Agent": "RadarLicitacoesTI/1.0"
        })

    def coletar(self, dias_atras: int = 15) -> List[Dict]:
        data_inicio = (datetime.now() - timedelta(days=dias_atras)).strftime("%Y-%m-%d")
        data_fim = datetime.now().strftime("%Y-%m-%d")
        resultados = []

        try:
            resp = self.sessao.get(
                self.URL_BASE,
                params={"dataInicio": data_inicio, "dataFim": data_fim},
                timeout=60,
            )
            if resp.status_code != 200:
                logger.warning("BEC-SP retornou HTTP %d", resp.status_code)
                return []

            dados = resp.json()
            itens = dados if isinstance(dados, list) else dados.get("data", dados.get("value", []))

            for item in itens:
                objeto = item.get("descricao", item.get("objeto", ""))
                if not _eh_ti(objeto):
                    continue
                resultados.append({
                    "orgao": item.get("unidadeCompradora", item.get("orgao", "N/A")),
                    "cnpj_orgao": item.get("cnpj", "N/A"),
                    "objeto": objeto,
                    "valor_estimado": float(item.get("valorEstimado", item.get("valor", 0)) or 0),
                    "data_publicacao": item.get("dataPublicacao", item.get("dataInicio", "")),
                    "data_abertura": item.get("dataAbertura", ""),
                    "data_encerramento": item.get("dataEncerramento", ""),
                    "uf": "SP",
                    "municipio": item.get("municipio", "São Paulo"),
                    "numero_edital": item.get("numeroOC", item.get("numero", "N/A")),
                    "modalidade": item.get("modalidade", "Oferta de Compra"),
                    "status": item.get("situacao", item.get("status", "N/A")),
                    "criterio_julgamento": "Menor Preço",
                    "link_edital": item.get("url", f"https://www.bec.sp.gov.br/BEC_Dispensa_UI/ui/bec_oc_item.aspx?OC={item.get('numeroOC', '')}"),
                    "fonte": "BEC-SP",
                })

            logger.info("BEC-SP: %d licitações TI coletadas", len(resultados))
        except requests.ConnectionError:
            logger.warning("BEC-SP: API indisponível")
        except Exception as e:
            logger.error("BEC-SP erro: %s", e)

        return resultados


class ColetorLicitacoesE:
    """
    Coletor para Licitações-e (Banco do Brasil).
    Portal: https://www.licitacoes-e.com.br
    """

    URL_API = "https://www.licitacoes-e.com.br/aop/rest/busca/licitacoes"

    def __init__(self):
        self.sessao = requests.Session()
        self.sessao.headers.update({
            "Accept": "application/json",
            "User-Agent": "RadarLicitacoesTI/1.0"
        })

    def coletar(self, dias_atras: int = 15) -> List[Dict]:
        data_inicio = (datetime.now() - timedelta(days=dias_atras)).strftime("%d/%m/%Y")
        data_fim = datetime.now().strftime("%d/%m/%Y")
        resultados = []

        try:
            resp = self.sessao.get(
                self.URL_API,
                params={
                    "dtInicio": data_inicio,
                    "dtFim": data_fim,
                    "pagina": 1,
                    "tamanhoPagina": 100,
                },
                timeout=60,
            )
            if resp.status_code != 200:
                logger.warning("Licitações-e retornou HTTP %d", resp.status_code)
                return []

            dados = resp.json()
            itens = dados if isinstance(dados, list) else dados.get("licitacoes", dados.get("data", []))

            for item in itens:
                objeto = item.get("objeto", item.get("descricao", ""))
                if not _eh_ti(objeto):
                    continue
                resultados.append({
                    "orgao": item.get("orgao", item.get("entidade", "N/A")),
                    "cnpj_orgao": item.get("cnpj", "N/A"),
                    "objeto": objeto,
                    "valor_estimado": float(item.get("valor", item.get("valorEstimado", 0)) or 0),
                    "data_publicacao": item.get("dataPublicacao", ""),
                    "data_abertura": item.get("dataAbertura", ""),
                    "data_encerramento": item.get("dataEncerramento", ""),
                    "uf": item.get("uf", "N/A"),
                    "municipio": item.get("municipio", "N/A"),
                    "numero_edital": item.get("numero", item.get("edital", "N/A")),
                    "modalidade": item.get("modalidade", "Licitação Eletrônica"),
                    "status": item.get("situacao", "N/A"),
                    "criterio_julgamento": item.get("criterioJulgamento", "N/A"),
                    "link_edital": item.get("url", ""),
                    "fonte": "Licitações-e",
                })

            logger.info("Licitações-e: %d licitações TI", len(resultados))
        except requests.ConnectionError:
            logger.warning("Licitações-e: API indisponível")
        except Exception as e:
            logger.error("Licitações-e erro: %s", e)

        return resultados


class ColetorCELIC_RS:
    """
    Coletor para CELIC-RS (Central de Licitações do RS).
    Portal: https://www.celic.rs.gov.br
    """

    URL_API = "https://www.celic.rs.gov.br/api/licitacoes"

    def __init__(self):
        self.sessao = requests.Session()
        self.sessao.headers.update({
            "Accept": "application/json",
            "User-Agent": "RadarLicitacoesTI/1.0"
        })

    def coletar(self, dias_atras: int = 15) -> List[Dict]:
        resultados = []
        try:
            resp = self.sessao.get(self.URL_API, params={"dias": dias_atras}, timeout=60)
            if resp.status_code != 200:
                logger.warning("CELIC-RS retornou HTTP %d", resp.status_code)
                return []

            dados = resp.json()
            itens = dados if isinstance(dados, list) else dados.get("data", [])

            for item in itens:
                objeto = item.get("objeto", "")
                if not _eh_ti(objeto):
                    continue
                resultados.append({
                    "orgao": item.get("orgao", "N/A"),
                    "cnpj_orgao": item.get("cnpj", "N/A"),
                    "objeto": objeto,
                    "valor_estimado": float(item.get("valor", 0) or 0),
                    "data_publicacao": item.get("dataPublicacao", ""),
                    "data_abertura": item.get("dataAbertura", ""),
                    "data_encerramento": item.get("dataEncerramento", ""),
                    "uf": "RS",
                    "municipio": item.get("municipio", "Porto Alegre"),
                    "numero_edital": item.get("numero", "N/A"),
                    "modalidade": item.get("modalidade", "Pregão Eletrônico"),
                    "status": item.get("situacao", "N/A"),
                    "criterio_julgamento": item.get("criterio", "N/A"),
                    "link_edital": item.get("url", ""),
                    "fonte": "CELIC-RS",
                })

            logger.info("CELIC-RS: %d licitações TI", len(resultados))
        except requests.ConnectionError:
            logger.warning("CELIC-RS: API indisponível")
        except Exception as e:
            logger.error("CELIC-RS erro: %s", e)

        return resultados


class ColetorPortaisEstaduais:
    """Orquestra coleta de todos os portais estaduais."""

    def __init__(self):
        self.coletores = [
            ColetorBEC_SP(),
            ColetorLicitacoesE(),
            ColetorCELIC_RS(),
        ]
        self.resumo: Dict = {}

    def coletar_todos(self, dias_atras: int = 15) -> pd.DataFrame:
        todos = []
        for coletor in self.coletores:
            nome = coletor.__class__.__name__
            try:
                dados = coletor.coletar(dias_atras=dias_atras)
                self.resumo[nome] = {"total": len(dados), "status": "ok"}
                todos.extend(dados)
            except Exception as e:
                self.resumo[nome] = {"total": 0, "status": f"erro: {e}"}
                logger.error("%s falhou: %s", nome, e)

        if todos:
            df = pd.DataFrame(todos)
            df.to_csv(OUTPUT_ESTADUAIS, index=False, encoding="utf-8")
            logger.info("Total portais estaduais: %d licitações TI salvas", len(df))
            return df

        logger.info("Nenhuma licitação TI encontrada nos portais estaduais")
        return pd.DataFrame()
