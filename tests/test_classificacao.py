"""
Testes de classificação TI e falsos positivos.
Testa a lógica real do pncp_radar_ti_plus.py.
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pncp_radar_ti_plus import RadarLicitacoesTI


@pytest.fixture
def radar():
    return RadarLicitacoesTI()


class TestDeteccaoTI:
    """Testa classificação de licitações como TI ou não-TI."""

    @pytest.mark.parametrize("texto", [
        "Aquisição de licença de software ERP",
        "Serviço de cloud computing AWS",
        "Contratação de sistema de informação",
        "Infraestrutura de TI - Data Center",
        "Serviço de segurança da informação e firewall",
        "Desenvolvimento de sistema web em Python",
        "Locação de computador e notebook",
        "Contratação de storage e backup",
        "Business intelligence e analytics",
        "Certificação digital ICP-Brasil",
        "Governança de TI ITIL COBIT",
        "Helpdesk e suporte técnico de TI",
        "Cabeamento estruturado e rede lógica",
        "Videoconferência e VoIP",
        "Solução SaaS de gestão",
    ])
    def test_detecta_ti(self, radar, texto):
        assert radar._eh_licitacao_ti(texto), f"Deveria detectar TI: {texto}"

    @pytest.mark.parametrize("texto", [
        "Construção de prédio escolar",
        "Pavimentação asfáltica de rodovia",
        "Material de escritório e papel A4",
        "Serviço de limpeza e conservação",
        "Rede de esgoto sanitário",
        "Rede de água pluvial",
        "Sistema de esgoto municipal",
        "Infraestrutura viária e drenagem",
        "Dados epidemiológicos de saúde",
        "Rede elétrica de baixa tensão",
        "Rede de proteção para quadra",
        "Sistema viário urbano",
    ])
    def test_nao_detecta_nao_ti(self, radar, texto):
        assert not radar._eh_licitacao_ti(texto), f"Não deveria detectar TI: {texto}"

    def test_texto_vazio(self, radar):
        assert not radar._eh_licitacao_ti("")
        assert not radar._eh_licitacao_ti(None)

    def test_case_insensitive(self, radar):
        assert radar._eh_licitacao_ti("SOFTWARE DE GESTÃO")
        assert radar._eh_licitacao_ti("Cloud Computing")


class TestProcessarLicitacao:
    def test_processar_item_ti(self, radar):
        item = {
            "objetoCompra": "Aquisição de licença de software ERP",
            "orgaoEntidade": {"razaoSocial": "Teste Org", "cnpj": "12345678000100"},
            "unidadeOrgao": {"ufSigla": "SP", "municipioNome": "São Paulo"},
            "valorTotalEstimado": 500000,
            "dataPublicacaoPncp": "2026-03-01",
            "dataAberturaProposta": "2026-03-15T10:00:00",
            "dataEncerramentoProposta": "2026-03-20T18:00:00",
            "numeroControlePNCP": "12345678000100-1-000001/2026",
            "modalidadeNome": "Pregão Eletrônico",
            "situacaoCompraNome": "Divulgada no PNCP",
            "tipoCriterioJulgamentoNome": "Menor Preço",
        }
        resultado = radar._processar_licitacao(item)
        assert resultado is not None
        assert resultado["orgao"] == "Teste Org"
        assert resultado["uf"] == "SP"
        assert resultado["fonte"] == "PNCP"
        assert "pncp.gov.br" in resultado["link_edital"]

    def test_rejeitar_nao_ti(self, radar):
        item = {
            "objetoCompra": "Pavimentação de estrada municipal",
            "orgaoEntidade": {"razaoSocial": "Prefeitura"},
            "unidadeOrgao": {"ufSigla": "MG", "municipioNome": "BH"},
        }
        resultado = radar._processar_licitacao(item)
        assert resultado is None
