"""Testes para historico_db.py — registro e consulta de coletas."""

import os
import sys
import pytest
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from historico_db import HistoricoDB


@pytest.fixture
def db(tmp_path):
    return HistoricoDB(db_path=str(tmp_path / "test_historico.db"))


@pytest.fixture
def df_exemplo():
    return pd.DataFrame({
        "orgao": ["Org A", "Org B", "Org A", "Org C"],
        "uf": ["SP", "RJ", "SP", "MG"],
        "valor_estimado": [100000, 200000, 50000, 300000],
        "modalidade": ["Pregão", "Pregão", "Concorrência", "Pregão"],
    })


class TestRegistrarColeta:
    def test_registrar(self, db, df_exemplo):
        coleta_id = db.registrar_coleta(df_exemplo, fonte="PNCP", total_verificadas=100)
        assert coleta_id >= 1

    def test_listar_coletas(self, db, df_exemplo):
        db.registrar_coleta(df_exemplo)
        coletas = db.listar_coletas()
        assert len(coletas) == 1
        assert coletas[0]["total_ti"] == 4
        assert coletas[0]["total_orgaos"] == 3
        assert coletas[0]["total_ufs"] == 3

    def test_multiplas_coletas(self, db, df_exemplo):
        db.registrar_coleta(df_exemplo, fonte="PNCP")
        db.registrar_coleta(df_exemplo, fonte="QD")
        coletas = db.listar_coletas()
        assert len(coletas) == 2

    def test_valor_total(self, db, df_exemplo):
        db.registrar_coleta(df_exemplo)
        coletas = db.listar_coletas()
        assert coletas[0]["valor_total"] == 650000


class TestEvolucao:
    def test_evolucao_ti(self, db, df_exemplo):
        db.registrar_coleta(df_exemplo)
        df = db.obter_evolucao_ti()
        assert len(df) == 1
        assert df.iloc[0]["total_ti"] == 4

    def test_evolucao_uf(self, db, df_exemplo):
        db.registrar_coleta(df_exemplo)
        df = db.obter_evolucao_uf("SP")
        assert len(df) == 1
        assert df.iloc[0]["quantidade"] == 2

    def test_evolucao_uf_inexistente(self, db, df_exemplo):
        db.registrar_coleta(df_exemplo)
        df = db.obter_evolucao_uf("AC")
        assert df.empty


class TestUltimaColeta:
    def test_ultima_coleta(self, db, df_exemplo):
        db.registrar_coleta(df_exemplo)
        ultima = db.obter_ultima_coleta()
        assert ultima is not None
        assert ultima["total_ti"] == 4

    def test_sem_coleta(self, db):
        assert db.obter_ultima_coleta() is None
