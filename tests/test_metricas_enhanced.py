"""Testes para metricas.py — Sentry, health check, Prometheus aprimorado."""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import metricas
from metricas import health_check, inicializar_sentry, capturar_excecao, MetricasDB


class TestHealthCheck:
    def test_retorna_dict(self):
        resultado = health_check()
        assert isinstance(resultado, dict)
        assert "status" in resultado
        assert "timestamp" in resultado
        assert "componentes" in resultado

    def test_status_valido(self):
        resultado = health_check()
        assert resultado["status"] in ("healthy", "degraded", "unhealthy")

    def test_componentes_essenciais(self):
        resultado = health_check()
        componentes = resultado["componentes"]
        assert "dados_dir" in componentes
        assert "disco" in componentes

    def test_disco_info(self):
        resultado = health_check()
        disco = resultado["componentes"]["disco"]
        assert "uso_percentual" in disco or disco["status"] == "unknown"


class TestInicializarSentry:
    def test_sem_dsn(self):
        resultado = inicializar_sentry("")
        assert resultado is False

    def test_dsn_none(self):
        resultado = inicializar_sentry(None)
        assert resultado is False

    @patch.dict(os.environ, {"SENTRY_DSN": ""})
    def test_sem_dsn_env(self):
        resultado = inicializar_sentry()
        assert resultado is False

    @patch("metricas._sentry_inicializado", False)
    def test_com_dsn_falso(self):
        """Com DSN fake, deve retornar bool (True se sentry-sdk presente, False se não)."""
        resultado = inicializar_sentry("https://fake@sentry.io/123")
        assert isinstance(resultado, bool)


class TestCapturarExcecao:
    def test_captura_sem_sentry(self):
        """Deve funcionar sem erro mesmo sem Sentry inicializado."""
        exc = ValueError("teste")
        # Não deve levantar exceção
        capturar_excecao(exc)

    def test_captura_com_contexto(self):
        exc = RuntimeError("erro teste")
        capturar_excecao(exc, contexto={"modulo": "teste", "acao": "validar"})


class TestMetricasDB:
    @pytest.fixture
    def mdb(self, tmp_path):
        return MetricasDB(db_path=str(tmp_path / "metricas_test.db"))

    def test_registrar_evento(self, mdb):
        mdb.registrar_evento("coleta", "PNCP", "coletou 50 licitações", 50)

    def test_listar_eventos(self, mdb):
        mdb.registrar_evento("coleta", "PNCP", "Coleta 1")
        mdb.registrar_evento("erro", "API", "Erro 1")
        eventos = mdb.ultimos_eventos(limite=10)
        assert len(eventos) == 2

    def test_listar_eventos_por_tipo(self, mdb):
        mdb.registrar_evento("coleta", "PNCP", "Coleta OK")
        mdb.registrar_evento("erro", "API", "Erro X")
        mdb.registrar_evento("coleta", "PNCP", "Coleta OK 2")
        eventos = mdb.ultimos_eventos(tipo="coleta", limite=10)
        assert len(eventos) == 2

    def test_exportar_prometheus(self, mdb):
        mdb.registrar_evento("coleta", "Test")
        prom = mdb.exportar_prometheus()
        assert isinstance(prom, str)
        assert "radar_" in prom or "# HELP" in prom or len(prom) > 0

    def test_resumo(self, mdb):
        mdb.registrar_evento("coleta", "PNCP", "OK")
        resumo = mdb.metricas_resumo()
        assert isinstance(resumo, dict)
        assert "eventos_por_tipo" in resumo
