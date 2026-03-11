"""Testes para exportar_ical.py — geração de arquivos .ics."""

import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from exportar_ical import gerar_ics


@pytest.fixture
def licitacoes():
    return [
        {
            "numero_edital": "E-001",
            "orgao": "Ministério da Fazenda",
            "objeto": "Aquisição de licenças de software",
            "valor_estimado": 500000,
            "uf": "DF",
            "data_abertura": "2026-03-15T10:00:00",
            "data_encerramento": "2026-03-20T18:00:00",
            "link_edital": "https://pncp.gov.br/app/editais/E-001",
        },
        {
            "numero_edital": "E-002",
            "orgao": "INSS",
            "objeto": "Serviço de cloud computing",
            "valor_estimado": 1200000,
            "uf": "SP",
            "data_abertura": "2026-04-01T09:00:00",
            "data_encerramento": "2026-04-10T17:00:00",
            "link_edital": "https://pncp.gov.br/app/editais/E-002",
        },
    ]


class TestGerarIcs:
    def test_gera_vcalendar_valido(self, licitacoes):
        ics = gerar_ics(licitacoes, "abertura")
        assert "BEGIN:VCALENDAR" in ics
        assert "END:VCALENDAR" in ics
        assert "VERSION:2.0" in ics

    def test_contem_eventos_abertura(self, licitacoes):
        ics = gerar_ics(licitacoes, "abertura")
        assert ics.count("BEGIN:VEVENT") == 2
        assert "20260315T100000" in ics
        assert "20260401T090000" in ics

    def test_contem_eventos_encerramento(self, licitacoes):
        ics = gerar_ics(licitacoes, "encerramento")
        assert ics.count("BEGIN:VEVENT") == 2
        assert "20260320T180000" in ics

    def test_contem_alarme(self, licitacoes):
        ics = gerar_ics(licitacoes, "abertura")
        assert "BEGIN:VALARM" in ics
        assert "TRIGGER:-PT30M" in ics

    def test_uid_unico(self, licitacoes):
        ics = gerar_ics(licitacoes, "abertura")
        assert "E-001-abertura@radar-licitacoes-ti" in ics
        assert "E-002-abertura@radar-licitacoes-ti" in ics

    def test_lista_vazia(self):
        ics = gerar_ics([], "abertura")
        assert "BEGIN:VCALENDAR" in ics
        assert "BEGIN:VEVENT" not in ics

    def test_dados_invalidos_ignorados(self):
        dados = [{"numero_edital": "X", "data_abertura": "invalido"}]
        ics = gerar_ics(dados, "abertura")
        assert "BEGIN:VEVENT" not in ics

    def test_nome_calendario(self, licitacoes):
        ics = gerar_ics(licitacoes, "abertura")
        assert "Licitações TI - Abertura" in ics
        ics2 = gerar_ics(licitacoes, "encerramento")
        assert "Licitações TI - Encerramento" in ics2
