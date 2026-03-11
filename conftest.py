"""
Fixtures compartilhadas para todos os testes.
"""

import os
import pytest


@pytest.fixture
def dados_dir(tmp_path):
    """Cria diretório de dados temporário."""
    d = tmp_path / "dados"
    d.mkdir()
    return d


@pytest.fixture
def licitacao_exemplo():
    """Retorna um dicionário de licitação de exemplo para testes."""
    return {
        "orgao": "Ministério da Ciência e Tecnologia",
        "cnpj_orgao": "00.000.000/0001-00",
        "objeto": "Aquisição de licenças de software para infraestrutura de TI",
        "valor_estimado": 150000.00,
        "data_publicacao": "2026-03-01",
        "data_abertura": "2026-03-15",
        "data_encerramento": "2026-03-20",
        "uf": "DF",
        "municipio": "Brasília",
        "numero_edital": "PE-2026-0001",
        "modalidade": "Pregão Eletrônico",
        "status": "Aberto",
        "criterio_julgamento": "Menor Preço",
        "link_edital": "https://pncp.gov.br/edital/PE-2026-0001",
        "fonte": "PNCP",
    }


@pytest.fixture(autouse=True)
def _garantir_dados_dir():
    """Garante que o diretório dados/ existe para testes que precisam dele."""
    os.makedirs("dados", exist_ok=True)
