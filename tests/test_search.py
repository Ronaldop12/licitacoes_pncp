"""Testes para search_db.py — Busca Full-Text FTS5."""

import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from search_db import SearchDB


@pytest.fixture
def search(tmp_path):
    return SearchDB(db_path=str(tmp_path / "search_test.db"))


@pytest.fixture
def csv_licitacoes(tmp_path):
    """Cria CSV de teste para indexação."""
    import pandas as pd

    dados = [
        {
            "numero_edital": "PE-2026-0001",
            "orgao": "Ministério da Ciência e Tecnologia",
            "objeto": "Aquisição de licenças de software Microsoft para infraestrutura de TI",
            "uf": "DF",
            "modalidade": "Pregão Eletrônico",
            "valor_estimado": 150000.00,
            "data_publicacao": "2026-03-01",
            "link_edital": "https://pncp.gov.br/edital/PE-2026-0001",
        },
        {
            "numero_edital": "PE-2026-0002",
            "orgao": "Tribunal Regional Federal",
            "objeto": "Contratação de serviços de computação em nuvem AWS",
            "uf": "SP",
            "modalidade": "Pregão Eletrônico",
            "valor_estimado": 800000.00,
            "data_publicacao": "2026-03-02",
            "link_edital": "",
        },
        {
            "numero_edital": "CC-2026-0001",
            "orgao": "Universidade Federal do Paraná",
            "objeto": "Implantação de sistema ERP para gestão acadêmica",
            "uf": "PR",
            "modalidade": "Concorrência",
            "valor_estimado": 2500000.00,
            "data_publicacao": "2026-03-03",
            "link_edital": "",
        },
        {
            "numero_edital": "PE-2026-0003",
            "orgao": "Prefeitura de São Paulo",
            "objeto": "Fornecimento de equipamentos de rede switches e roteadores",
            "uf": "SP",
            "modalidade": "Pregão Eletrônico",
            "valor_estimado": 350000.00,
            "data_publicacao": "2026-03-04",
            "link_edital": "",
        },
    ]
    csv_path = str(tmp_path / "licitacoes.csv")
    pd.DataFrame(dados).to_csv(csv_path, index=False)
    return csv_path


class TestIndexacao:
    def test_indexar_csv(self, search, csv_licitacoes):
        resultado = search.indexar_csv(csv_licitacoes)
        assert resultado["ok"] is True
        assert resultado["total_indexados"] == 4
        assert resultado["reindexado"] is True

    def test_reindexacao_evitada(self, search, csv_licitacoes):
        search.indexar_csv(csv_licitacoes)
        resultado = search.indexar_csv(csv_licitacoes)
        assert resultado["ok"] is True
        assert resultado["reindexado"] is False

    def test_reindexacao_forcada(self, search, csv_licitacoes):
        search.indexar_csv(csv_licitacoes)
        resultado = search.indexar_csv(csv_licitacoes, forcar=True)
        assert resultado["ok"] is True
        assert resultado["reindexado"] is True

    def test_csv_inexistente(self, search):
        resultado = search.indexar_csv("/caminho/inexistente.csv")
        assert resultado["ok"] is False

    def test_info_apos_indexacao(self, search, csv_licitacoes):
        search.indexar_csv(csv_licitacoes)
        info = search.info()
        assert info["total_indexados"] == 4
        assert info["ultima_indexacao"] is not None


class TestBusca:
    @pytest.fixture(autouse=True)
    def _indexar(self, search, csv_licitacoes):
        search.indexar_csv(csv_licitacoes)
        self.search = search

    def test_busca_simples(self):
        resultados = self.search.buscar("software")
        assert len(resultados) >= 1
        assert any("software" in r["objeto"].lower() for r in resultados)

    def test_busca_multiplos_termos(self):
        resultados = self.search.buscar("computação nuvem")
        assert len(resultados) >= 1

    def test_busca_por_orgao(self):
        resultados = self.search.buscar("Ministério")
        assert len(resultados) >= 1

    def test_busca_com_filtro_uf(self):
        resultados = self.search.buscar("software OR rede OR nuvem", uf="SP")
        for r in resultados:
            assert r["uf"] == "SP"

    def test_busca_sem_resultados(self):
        resultados = self.search.buscar("xyztermoquenoexiste")
        assert resultados == []

    def test_busca_vazia(self):
        resultados = self.search.buscar("")
        assert resultados == []

    def test_busca_com_limite(self):
        resultados = self.search.buscar("software OR nuvem OR rede OR sistema", limite=2)
        assert len(resultados) <= 2

    def test_busca_caracteres_especiais(self):
        """Caracteres especiais devem ser sanitizados sem erro."""
        resultados = self.search.buscar("test@#$%")
        assert isinstance(resultados, list)


class TestSugerir:
    @pytest.fixture(autouse=True)
    def _indexar(self, search, csv_licitacoes):
        search.indexar_csv(csv_licitacoes)
        self.search = search

    def test_sugerir_prefixo(self):
        sugestoes = self.search.sugerir("soft")
        assert isinstance(sugestoes, list)

    def test_sugerir_muito_curto(self):
        sugestoes = self.search.sugerir("a")
        assert sugestoes == []

    def test_sugerir_vazio(self):
        sugestoes = self.search.sugerir("")
        assert sugestoes == []


class TestInfoVazio:
    def test_info_sem_indexacao(self, search):
        info = search.info()
        assert info["total_indexados"] == 0
