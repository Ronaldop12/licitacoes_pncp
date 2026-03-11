"""Testes para fases_db.py — rastreamento de mudanças de status."""

import os
import sys
import pytest
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fases_db import FasesDB


@pytest.fixture
def db(tmp_path):
    return FasesDB(db_path=str(tmp_path / "test_fases.db"))


def _df(dados):
    return pd.DataFrame(dados)


class TestProcessarColeta:
    def test_primeira_coleta_sem_mudancas(self, db):
        df = _df([
            {"numero_edital": "E1", "status": "Divulgada", "orgao": "Org1", "objeto": "Obj", "uf": "SP"},
            {"numero_edital": "E2", "status": "Divulgada", "orgao": "Org2", "objeto": "Obj", "uf": "RJ"},
        ])
        mudancas = db.processar_coleta(df)
        assert len(mudancas) == 0  # Primeira vez, sem mudanças

    def test_detecta_mudanca_status(self, db):
        # Primeira coleta
        df1 = _df([{"numero_edital": "E1", "status": "Divulgada", "orgao": "Org1", "objeto": "X", "uf": "SP"}])
        db.processar_coleta(df1)

        # Segunda coleta com mudança
        df2 = _df([{"numero_edital": "E1", "status": "Em andamento", "orgao": "Org1", "objeto": "X", "uf": "SP"}])
        mudancas = db.processar_coleta(df2)
        assert len(mudancas) == 1
        assert mudancas[0]["status_anterior"] == "Divulgada"
        assert mudancas[0]["status_novo"] == "Em andamento"

    def test_sem_mudanca_sem_registro(self, db):
        df = _df([{"numero_edital": "E1", "status": "Divulgada", "orgao": "O", "objeto": "X", "uf": "SP"}])
        db.processar_coleta(df)
        mudancas = db.processar_coleta(df)  # Mesma coleta
        assert len(mudancas) == 0

    def test_multiplas_mudancas(self, db):
        df1 = _df([
            {"numero_edital": "E1", "status": "A", "orgao": "O1", "objeto": "X", "uf": "SP"},
            {"numero_edital": "E2", "status": "A", "orgao": "O2", "objeto": "Y", "uf": "RJ"},
        ])
        db.processar_coleta(df1)

        df2 = _df([
            {"numero_edital": "E1", "status": "B", "orgao": "O1", "objeto": "X", "uf": "SP"},
            {"numero_edital": "E2", "status": "C", "orgao": "O2", "objeto": "Y", "uf": "RJ"},
        ])
        mudancas = db.processar_coleta(df2)
        assert len(mudancas) == 2

    def test_df_vazio(self, db):
        assert db.processar_coleta(pd.DataFrame()) == []


class TestListarMudancas:
    def test_listar(self, db):
        df1 = _df([{"numero_edital": "E1", "status": "A", "orgao": "O", "objeto": "X", "uf": "SP"}])
        db.processar_coleta(df1)
        df2 = _df([{"numero_edital": "E1", "status": "B", "orgao": "O", "objeto": "X", "uf": "SP"}])
        db.processar_coleta(df2)

        mudancas = db.listar_mudancas()
        assert len(mudancas) == 1

    def test_filtrar_por_uf(self, db):
        df1 = _df([
            {"numero_edital": "E1", "status": "A", "orgao": "O", "objeto": "X", "uf": "SP"},
            {"numero_edital": "E2", "status": "A", "orgao": "O", "objeto": "Y", "uf": "RJ"},
        ])
        db.processar_coleta(df1)
        df2 = _df([
            {"numero_edital": "E1", "status": "B", "orgao": "O", "objeto": "X", "uf": "SP"},
            {"numero_edital": "E2", "status": "B", "orgao": "O", "objeto": "Y", "uf": "RJ"},
        ])
        db.processar_coleta(df2)

        sp = db.listar_mudancas(uf="SP")
        assert len(sp) == 1

    def test_historico_edital(self, db):
        df = _df([{"numero_edital": "E1", "status": "A", "orgao": "O", "objeto": "X", "uf": "SP"}])
        db.processar_coleta(df)
        df["status"] = "B"
        db.processar_coleta(df)
        df["status"] = "C"
        db.processar_coleta(df)

        hist = db.obter_historico_edital("E1")
        assert len(hist) == 2  # A→B, B→C


class TestEstatisticas:
    def test_contar(self, db):
        df1 = _df([{"numero_edital": "E1", "status": "A", "orgao": "O", "objeto": "X", "uf": "SP"}])
        db.processar_coleta(df1)
        df2 = _df([{"numero_edital": "E1", "status": "B", "orgao": "O", "objeto": "X", "uf": "SP"}])
        db.processar_coleta(df2)

        stats = db.contar_mudancas()
        assert stats["total_mudancas"] == 1
        assert stats["editais_com_mudanca"] == 1
        assert stats["total_rastreados"] == 1
