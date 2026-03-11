"""Testes para utils_email.py"""

import pytest
from unittest.mock import patch, MagicMock


class TestEmailAlerter:

    def test_init(self):
        from utils_email import EmailAlerter
        e = EmailAlerter(
            smtp_server="smtp.test.com",
            smtp_port=587,
            email_from="test@test.com",
            senha="secret"
        )
        assert e.smtp_server == "smtp.test.com"
        assert e.smtp_port == 587
        assert e.email_from == "test@test.com"

    def test_validar_configuracao_vazia(self):
        from utils_email import EmailAlerter
        e = EmailAlerter()
        assert e.validar_configuracao() is False

    @patch("utils_email.smtplib.SMTP")
    def test_validar_configuracao_sucesso(self, mock_smtp):
        from utils_email import EmailAlerter
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server

        e = EmailAlerter(
            smtp_server="smtp.test.com",
            smtp_port=587,
            email_from="test@test.com",
            senha="secret"
        )
        assert e.validar_configuracao() is True
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("test@test.com", "secret")
        mock_server.quit.assert_called_once()

    @patch("utils_email.smtplib.SMTP")
    def test_validar_configuracao_auth_error(self, mock_smtp):
        import smtplib
        from utils_email import EmailAlerter
        mock_server = MagicMock()
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, b"Auth failed")
        mock_smtp.return_value = mock_server

        e = EmailAlerter(email_from="t@t.com", senha="wrong")
        assert e.validar_configuracao() is False

    @patch("utils_email.smtplib.SMTP")
    def test_enviar_alerta_licitacao(self, mock_smtp):
        from utils_email import EmailAlerter
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp.return_value.__exit__ = MagicMock(return_value=False)

        e = EmailAlerter(email_from="from@test.com", senha="secret")
        licita = {
            "numero_edital": "PE-001",
            "objeto": "Software ERP",
            "valor_estimado": 50000.0,
            "orgao": "Ministério X",
            "uf": "DF",
            "data_publicacao": "2026-01-01",
        }
        result = e.enviar_alerta_licitacao("dest@test.com", licita, "Alerta Teste")
        assert result is True
        mock_server.send_message.assert_called_once()

    def test_init_defaults(self):
        from utils_email import EmailAlerter
        e = EmailAlerter()
        assert e.smtp_server == "smtp.gmail.com"
        assert e.smtp_port == 587
        assert e.email_from == ""
        assert e.senha == ""
