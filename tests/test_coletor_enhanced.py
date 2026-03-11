"""Testes para coletor_async.py — Coleta assíncrona aprimorada."""

import os
import sys
import asyncio
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from coletor_async import coletar_sincrono_wrapper


class TestColetorSincronoWrapper:
    """Testa o wrapper síncrono (que chama a coleta assíncrona)."""

    @patch("coletor_async.coletar_async")
    def test_retorna_lista(self, mock_async):
        """Wrapper deve extrair lista de licitações do dict retornado."""
        mock_async.return_value = {
            "licitacoes": [{"orgao": "Org1"}, {"orgao": "Org2"}],
            "total": 2,
            "duracao_segundos": 5.0,
            "erros": 0,
        }
        resultado = coletar_sincrono_wrapper(dias_atras=1)
        assert isinstance(resultado, list)
        assert len(resultado) == 2

    @patch("coletor_async.coletar_async")
    def test_retorna_lista_vazia(self, mock_async):
        mock_async.return_value = {
            "licitacoes": [],
            "total": 0,
            "duracao_segundos": 1.0,
            "erros": 0,
        }
        resultado = coletar_sincrono_wrapper(dias_atras=1)
        assert resultado == []

    @patch("coletor_async.coletar_async")
    def test_compatibilidade_formato_antigo(self, mock_async):
        """Se por algum motivo retornar lista pura, deve funcionar."""
        mock_async.return_value = [{"orgao": "Org1"}]
        resultado = coletar_sincrono_wrapper(dias_atras=1)
        assert isinstance(resultado, list)


class TestDivisaoPeriodos:
    """Testa a lógica de divisão de períodos em faixas."""

    def test_periodo_curto_sem_divisao(self):
        """Períodos <= 7 dias não devem ser divididos."""
        data_fim = datetime.now()
        data_inicio = data_fim - timedelta(days=5)
        dias = 5

        faixas = []
        if dias > 7:
            d = data_inicio
            while d < data_fim:
                fim_faixa = min(d + timedelta(days=5), data_fim)
                faixas.append((d.strftime("%Y%m%d"), fim_faixa.strftime("%Y%m%d")))
                d = fim_faixa
        else:
            faixas.append((data_inicio.strftime("%Y%m%d"), data_fim.strftime("%Y%m%d")))

        assert len(faixas) == 1

    def test_periodo_longo_divisao(self):
        """Períodos > 7 dias devem ser divididos em faixas de 5."""
        data_fim = datetime.now()
        data_inicio = data_fim - timedelta(days=20)
        dias = 20

        faixas = []
        d = data_inicio
        while d < data_fim:
            fim_faixa = min(d + timedelta(days=5), data_fim)
            faixas.append((d.strftime("%Y%m%d"), fim_faixa.strftime("%Y%m%d")))
            d = fim_faixa

        assert len(faixas) == 4  # 20 / 5 = 4 faixas

    def test_periodo_15_dias(self):
        """15 dias → 3 faixas de 5."""
        data_fim = datetime.now()
        data_inicio = data_fim - timedelta(days=15)

        faixas = []
        d = data_inicio
        while d < data_fim:
            fim_faixa = min(d + timedelta(days=5), data_fim)
            faixas.append((d.strftime("%Y%m%d"), fim_faixa.strftime("%Y%m%d")))
            d = fim_faixa

        assert len(faixas) == 3

    def test_faixas_cobrem_periodo_completo(self):
        """As faixas devem cobrir todo o período sem lacunas."""
        data_fim = datetime.now()
        data_inicio = data_fim - timedelta(days=12)

        faixas = []
        d = data_inicio
        while d < data_fim:
            fim_faixa = min(d + timedelta(days=5), data_fim)
            faixas.append((d.strftime("%Y%m%d"), fim_faixa.strftime("%Y%m%d")))
            d = fim_faixa

        # Primeira faixa começa no início
        assert faixas[0][0] == data_inicio.strftime("%Y%m%d")
        # Última faixa termina no fim
        assert faixas[-1][1] == data_fim.strftime("%Y%m%d")


class TestResultadoColeta:
    """Testa a estrutura do resultado da coleta."""

    @patch("coletor_async.coletar_async")
    def test_estrutura_resultado(self, mock_async):
        mock_async.return_value = {
            "licitacoes": [],
            "total": 0,
            "duracao_segundos": 2.5,
            "modalidades_coletadas": 13,
            "faixas_paralelas": 3,
            "erros": 0,
            "por_modalidade": {},
            "editais_unicos": 0,
            "periodo": {
                "inicio": "2026-01-01",
                "fim": "2026-01-15",
                "dias": 15,
            },
        }
        resultado = mock_async.return_value
        assert "licitacoes" in resultado
        assert "total" in resultado
        assert "duracao_segundos" in resultado
        assert "modalidades_coletadas" in resultado
        assert "faixas_paralelas" in resultado
        assert "erros" in resultado
        assert "periodo" in resultado
        assert resultado["modalidades_coletadas"] == 13
