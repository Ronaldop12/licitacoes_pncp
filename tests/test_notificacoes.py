"""Testes para notificacoes.py — Slack e Discord notifications."""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from notificacoes import SlackNotifier, DiscordNotifier, NotificadorMultiCanal


@pytest.fixture
def licitacao_exemplo():
    return {
        "orgao": "Ministério da Ciência e Tecnologia",
        "objeto": "Aquisição de licenças de software para TI",
        "valor_estimado": 150000.00,
        "uf": "DF",
        "modalidade": "Pregão Eletrônico",
        "link_edital": "https://pncp.gov.br/edital/PE-2026-0001",
    }


class TestSlackNotifier:
    @pytest.fixture
    def slack(self):
        return SlackNotifier("https://hooks.slack.com/services/TEST")

    @patch("notificacoes.requests.Session.post")
    def test_enviar_sucesso(self, mock_post, slack):
        mock_post.return_value = MagicMock(status_code=200)
        assert slack.enviar("Teste") is True
        mock_post.assert_called_once()

    @patch("notificacoes.requests.Session.post")
    def test_enviar_falha(self, mock_post, slack):
        mock_post.return_value = MagicMock(status_code=500, text="error")
        assert slack.enviar("Teste") is False

    @patch("notificacoes.requests.Session.post")
    def test_enviar_licitacao(self, mock_post, slack, licitacao_exemplo):
        mock_post.return_value = MagicMock(status_code=200)
        assert slack.enviar_licitacao(licitacao_exemplo) is True
        payload = mock_post.call_args[1]["json"]
        assert "blocks" in payload

    @patch("notificacoes.requests.Session.post")
    def test_enviar_resumo(self, mock_post, slack):
        mock_post.return_value = MagicMock(status_code=200)
        assert slack.enviar_resumo(100, 15, {"SP": 30, "DF": 20, "RJ": 10}) is True

    @patch("notificacoes.requests.Session.post")
    def test_erro_conexao(self, mock_post, slack):
        import requests
        mock_post.side_effect = requests.RequestException("timeout")
        assert slack.enviar("Teste") is False


class TestDiscordNotifier:
    @pytest.fixture
    def discord(self):
        return DiscordNotifier("https://discord.com/api/webhooks/TEST")

    @patch("notificacoes.requests.Session.post")
    def test_enviar_sucesso(self, mock_post, discord):
        mock_post.return_value = MagicMock(status_code=204)
        assert discord.enviar("Teste") is True

    @patch("notificacoes.requests.Session.post")
    def test_enviar_licitacao(self, mock_post, discord, licitacao_exemplo):
        mock_post.return_value = MagicMock(status_code=200)
        assert discord.enviar_licitacao(licitacao_exemplo) is True
        payload = mock_post.call_args[1]["json"]
        assert "embeds" in payload
        assert payload["embeds"][0]["title"] == "📡 Nova Licitação de TI"

    @patch("notificacoes.requests.Session.post")
    def test_enviar_licitacao_sem_link(self, mock_post, discord):
        mock_post.return_value = MagicMock(status_code=200)
        lic = {"orgao": "Org", "objeto": "Obj", "valor_estimado": 0}
        assert discord.enviar_licitacao(lic) is True

    @patch("notificacoes.requests.Session.post")
    def test_enviar_resumo(self, mock_post, discord):
        mock_post.return_value = MagicMock(status_code=200)
        assert discord.enviar_resumo(200, 30, {"MG": 40, "GO": 15}) is True


class TestNotificadorMultiCanal:
    def test_nenhum_canal(self):
        n = NotificadorMultiCanal()
        assert n.total_canais == 0

    def test_adicionar_canais(self):
        n = NotificadorMultiCanal()
        n.adicionar_slack("https://hooks.slack.com/x")
        n.adicionar_discord("https://discord.com/api/webhooks/y")
        assert n.total_canais == 2

    def test_adicionar_url_vazia(self):
        n = NotificadorMultiCanal()
        n.adicionar_slack("")
        n.adicionar_discord("")
        assert n.total_canais == 0

    @patch("notificacoes.requests.Session.post")
    def test_notificar_licitacao_multi(self, mock_post, licitacao_exemplo):
        mock_post.return_value = MagicMock(status_code=200)
        n = NotificadorMultiCanal()
        n.adicionar_slack("https://hooks.slack.com/x")
        n.adicionar_discord("https://discord.com/api/webhooks/y")
        resultados = n.notificar_licitacao(licitacao_exemplo)
        assert "SlackNotifier" in resultados
        assert "DiscordNotifier" in resultados
        assert all(v is True for v in resultados.values())

    @patch("notificacoes.requests.Session.post")
    def test_notificar_resumo_multi(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200)
        n = NotificadorMultiCanal()
        n.adicionar_slack("https://hooks.slack.com/x")
        resultados = n.notificar_resumo(100, 10, {"SP": 20})
        assert resultados["SlackNotifier"] is True
