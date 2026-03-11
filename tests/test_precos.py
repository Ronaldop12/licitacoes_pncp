"""
Testes do módulo precos_db — histórico de preços por categoria.
Inclui testes para novas funcionalidades: tendência, comparação, outliers, ranking.
"""

import os
import sys
import pytest
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from precos_db import PrecosDB


@pytest.fixture
def db(tmp_path):
    return PrecosDB(db_path=str(tmp_path / "test_precos.db"))


@pytest.fixture
def db_populado(db):
    """DB com dados de teste realistas."""
    dados = pd.DataFrame([
        {"numero_edital": "PE-001", "codigo_catmat_catser": "CAT001", "categoria_item": "Software",
         "objeto": "Licença antivírus", "valor_estimado": 50000.0, "orgao": "MEC", "uf": "DF", "data_publicacao": "2025-01-15"},
        {"numero_edital": "PE-002", "codigo_catmat_catser": "CAT001", "categoria_item": "Software",
         "objeto": "Licença antivírus", "valor_estimado": 55000.0, "orgao": "INSS", "uf": "RJ", "data_publicacao": "2025-03-20"},
        {"numero_edital": "PE-003", "codigo_catmat_catser": "CAT001", "categoria_item": "Software",
         "objeto": "Licença antivírus", "valor_estimado": 60000.0, "orgao": "MEC", "uf": "DF", "data_publicacao": "2025-06-10"},
        {"numero_edital": "PE-004", "codigo_catmat_catser": "CAT001", "categoria_item": "Software",
         "objeto": "Licença antivírus", "valor_estimado": 200000.0, "orgao": "MS", "uf": "SP", "data_publicacao": "2025-09-01"},
        {"numero_edital": "PE-005", "codigo_catmat_catser": "CAT002", "categoria_item": "Hardware",
         "objeto": "Notebooks", "valor_estimado": 120000.0, "orgao": "MEC", "uf": "DF", "data_publicacao": "2025-02-01"},
        {"numero_edital": "PE-006", "codigo_catmat_catser": "CAT002", "categoria_item": "Hardware",
         "objeto": "Notebooks", "valor_estimado": 115000.0, "orgao": "INSS", "uf": "SP", "data_publicacao": "2025-05-15"},
        {"numero_edital": "PE-007", "codigo_catmat_catser": "CAT003", "categoria_item": "Serviços",
         "objeto": "Suporte TI", "valor_estimado": 300000.0, "orgao": "STF", "uf": "DF", "data_publicacao": "2025-04-01"},
    ])
    db.registrar_precos(dados)
    return db


class TestRegistrarPrecos:

    def test_registrar_precos_basico(self, db):
        df = pd.DataFrame([{
            "numero_edital": "PE-001",
            "codigo_catmat_catser": "CAT001",
            "categoria_item": "Software",
            "objeto": "Licença",
            "valor_estimado": 50000.0,
            "orgao": "MEC",
            "uf": "DF",
            "data_publicacao": "2025-01-01",
        }])
        inseridos = db.registrar_precos(df)
        assert inseridos == 1

    def test_nao_duplica(self, db):
        df = pd.DataFrame([{
            "numero_edital": "PE-001",
            "valor_estimado": 50000.0,
        }])
        db.registrar_precos(df)
        inseridos = db.registrar_precos(df)
        assert inseridos == 0

    def test_ignora_valor_zero(self, db):
        df = pd.DataFrame([{
            "numero_edital": "PE-001",
            "valor_estimado": 0,
        }])
        inseridos = db.registrar_precos(df)
        assert inseridos == 0

    def test_df_vazio(self, db):
        inseridos = db.registrar_precos(pd.DataFrame())
        assert inseridos == 0


class TestEvolucao:

    def test_evolucao_por_categoria(self, db_populado):
        df = db_populado.evolucao_por_categoria("CAT001")
        assert len(df) == 4
        assert "valor_estimado" in df.columns

    def test_evolucao_categoria_inexistente(self, db_populado):
        df = db_populado.evolucao_por_categoria("NAOEXISTE")
        assert df.empty


class TestResumo:

    def test_resumo_categorias(self, db_populado):
        df = db_populado.resumo_categorias(limite=10)
        assert len(df) >= 2
        assert df.iloc[0]["quantidade"] >= df.iloc[1]["quantidade"]

    def test_estatisticas_gerais(self, db_populado):
        stats = db_populado.estatisticas_gerais()
        assert stats["total_registros"] == 7
        assert stats["categorias_distintas"] == 3
        assert stats["preco_medio_geral"] > 0


class TestComparacao:

    def test_comparar_orgaos(self, db_populado):
        df = db_populado.comparar_orgaos_categoria("CAT001")
        assert len(df) >= 2
        assert "preco_medio" in df.columns
        orgaos = df["orgao"].tolist()
        assert "MEC" in orgaos

    def test_comparar_categoria_inexistente(self, db_populado):
        df = db_populado.comparar_orgaos_categoria("NADA")
        assert df.empty


class TestOutliers:

    def test_detectar_outlier(self, db_populado):
        # CAT001 tem valor 200k que é outlier (50k, 55k, 60k, 200k)
        outliers = db_populado.detectar_outliers("CAT001", fator=1.0)
        assert len(outliers) >= 1
        assert any(outliers["valor_estimado"] > 100000)

    def test_sem_outliers(self, db_populado):
        # CAT002 tem valores próximos (120k, 115k)
        outliers = db_populado.detectar_outliers("CAT002", fator=2.0)
        assert len(outliers) == 0

    def test_poucos_dados(self, db):
        df = pd.DataFrame([{
            "numero_edital": "PE-001", "valor_estimado": 100.0,
        }])
        db.registrar_precos(df)
        outliers = db.detectar_outliers("N/A")
        assert outliers.empty


class TestTendencia:

    def test_tendencia_alta(self, db_populado):
        t = db_populado.tendencia_categoria("CAT001")
        assert t is not None
        assert t["registros"] == 4
        assert t["variacao_percentual"] > 0
        assert t["direcao"] == "alta"

    def test_tendencia_baixa(self, db_populado):
        t = db_populado.tendencia_categoria("CAT002")
        assert t is not None
        # 120k -> 115k = ~-4.2%, dentro da faixa estável (±5%)
        assert t["variacao_percentual"] < 0
        assert t["direcao"] == "estável"

    def test_tendencia_insuficiente(self, db_populado):
        t = db_populado.tendencia_categoria("CAT003")
        # Apenas 1 registro
        assert t is None

    def test_tendencia_inexistente(self, db_populado):
        t = db_populado.tendencia_categoria("NAOEXISTE")
        assert t is None


class TestRanking:

    def test_ranking_variacao(self, db_populado):
        ranking = db_populado.ranking_categorias_variacao(limite=10)
        assert len(ranking) >= 2
        # Deve estar ordenado por valor absoluto de variação
        assert abs(ranking[0]["variacao_percentual"]) >= abs(ranking[1]["variacao_percentual"])


class TestEvolucaoPorUF:

    def test_precos_por_uf(self, db_populado):
        df = db_populado.evolucao_por_uf("CAT001")
        assert len(df) >= 2
        ufs = df["uf"].tolist()
        assert "DF" in ufs
        assert "preco_medio" in df.columns

    def test_uf_categoria_inexistente(self, db_populado):
        df = db_populado.evolucao_por_uf("NADA")
        assert df.empty
