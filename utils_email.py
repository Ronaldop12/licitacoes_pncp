#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════════════════
UTILITÁRIOS DE EMAIL - Sistema de Alertas PNCP
═══════════════════════════════════════════════════════════════════════════════

Módulo para envio de alertas via email.

Uso:
    from utils_email import EmailAlerter
    alerter = EmailAlerter(
        smtp_server="smtp.gmail.com",
        smtp_port=587,
        email_from="seu_email@gmail.com",
        senha="sua_senha_app"
    )
    alerter.enviar_alerta_licitacao(
        email_para="destinatario@example.com",
        licita={"numero_edital": "123", ...}
    )
"""

import smtplib
import logging
from typing import Optional, Dict, Any, List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailAlerter:
    """Classe para enviar alertas via Email"""

    def __init__(
        self,
        smtp_server: str = "smtp.gmail.com",
        smtp_port: int = 587,
        email_from: str = "",
        senha: str = ""
    ):
        """
        Inicializa o alertador de Email

        Args:
            smtp_server: Servidor SMTP (default: Gmail)
            smtp_port: Porta SMTP (default: 587 para TLS)
            email_from: Email do remetente
            senha: Senha ou App Password
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email_from = email_from
        self.senha = senha
        logger.info(f"EmailAlerter inicializado: {email_from}")

    def validar_configuracao(self) -> bool:
        """
        Valida se as credenciais estão corretas

        Returns:
            True se validado com sucesso
        """
        if not self.email_from or not self.senha:
            logger.error("Email ou senha não configurados!")
            return False

        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_from, self.senha)
            server.quit()
            logger.info("✓ Credenciais de email válidas!")
            return True
        except smtplib.SMTPAuthenticationError:
            logger.error("✗ Email ou senha incorretos!")
            return False
        except Exception as e:
            logger.error(f"✗ Erro ao validar email: {e}")
            return False

    def enviar_alerta_licitacao(
        self,
        email_para: str,
        licita: Dict[str, Any],
        nome_alerta: str = "Novo Alerta"
    ) -> bool:
        """
        Envia alerta de licitação por email

        Args:
            email_para: Email destinatário
            licita: Dicionário com dados da licitação
            nome_alerta: Nome do alerta

        Returns:
            True se enviado com sucesso
        """
        try:
            # Formatar a mensagem HTML
            numero_edital = licita.get("numero_edital", "N/A")
            objeto = licita.get("objeto", "N/A")
            valor = float(licita.get("valor_estimado", 0))
            orgao = licita.get("orgao", "N/A")
            uf = licita.get("uf", "N/A")
            data_pub = licita.get("data_publicacao", "N/A")

            # Formatar valor
            valor_fmt = f"R$ {valor:,.2f}".replace(",", ".")

            html_body = f"""
            <html>
                <head>
                    <meta charset="utf-8">
                    <style>
                        body {{ font-family: Arial, sans-serif; color: #333; }}
                        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                        .header {{ background-color: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
                        .content {{ background-color: #f8f9fa; padding: 20px; margin-top: 20px; border-left: 4px solid #3498db; }}
                        .field {{ margin: 12px 0; }}
                        .label {{ font-weight: bold; color: #2c3e50; }}
                        .value {{ color: #333; }}
                        .footer {{ margin-top: 20px; font-size: 12px; color: #7f8c8d; border-top: 1px solid #bdc3c7; padding-top: 10px; }}
                        .badge {{ display: inline-block; background-color: #27ae60; color: white; padding: 5px 10px; border-radius: 3px; font-weight: bold; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h2>🎯 {nome_alerta}</h2>
                            <p>Nova licitação detectada pelo Sistema Radar TI!</p>
                        </div>

                        <div class="content">
                            <div class="field">
                                <span class="label">📋 Número do Edital:</span>
                                <span class="value">{numero_edital}</span>
                            </div>

                            <div class="field">
                                <span class="label">🏢 Órgão:</span>
                                <span class="value">{orgao}</span>
                            </div>

                            <div class="field">
                                <span class="label">📍 UF:</span>
                                <span class="value">{uf}</span>
                            </div>

                            <div class="field">
                                <span class="label">💰 Valor Estimado:</span>
                                <span class="value badge">{valor_fmt}</span>
                            </div>

                            <div class="field">
                                <span class="label">📝 Objeto da Licitação:</span>
                                <span class="value">{objeto}</span>
                            </div>

                            <div class="field">
                                <span class="label">📅 Data de Publicação:</span>
                                <span class="value">{data_pub}</span>
                            </div>
                        </div>

                        <div class="footer">
                            <p>✓ Enviado em: {datetime.now().strftime("%d/%m/%Y às %H:%M:%S")}</p>
                            <p>Sistema Radar de Licitações TI - Alertas Automáticos</p>
                        </div>
                    </div>
                </body>
            </html>
            """

            # Criar mensagem
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"🎯 {nome_alerta}: {numero_edital}"
            msg["From"] = self.email_from
            msg["To"] = email_para

            # Versão texto simples
            text_body = f"""
            {nome_alerta}
            {'=' * 60}

            Número do Edital: {numero_edital}
            Órgão: {orgao}
            UF: {uf}
            Valor: {valor_fmt}
            Objeto: {objeto}
            Data: {data_pub}

            Enviado em: {datetime.now().strftime("%d/%m/%Y às %H:%M:%S")}
            Sistema Radar de Licitações TI
            """

            # Adicionar ambas as versões
            part1 = MIMEText(text_body, "plain")
            part2 = MIMEText(html_body, "html")
            msg.attach(part1)
            msg.attach(part2)

            # Enviar
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_from, self.senha)
                server.send_message(msg)

            logger.info(f"✓ Email enviado para {email_para}: {numero_edital}")
            return True

        except Exception as e:
            logger.error(f"✗ Erro ao enviar email: {e}")
            return False

    def enviar_resumo_alertas(
        self,
        email_para: str,
        licitacoes: List[Dict[str, Any]],
        nome_alerta: str = "Resumo de Alertas"
    ) -> bool:
        """
        Envia resumo de múltiplas licitações em um único email

        Args:
            email_para: Email destinatário
            licitacoes: Lista de licitações
            nome_alerta: Nome do alerta

        Returns:
            True se enviado com sucesso
        """
        if not licitacoes:
            logger.warning("Nenhuma licitação para enviar resumo")
            return False

        try:
            # Montar linhas da tabela
            linhas_tabela = ""
            valor_total = 0

            for lic in licitacoes:
                valor = float(lic.get("valor_estimado", 0))
                valor_total += valor
                valor_fmt = f"R$ {valor:,.2f}".replace(",", ".")

                linhas_tabela += f"""
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #ecf0f1;">{lic.get('numero_edital', 'N/A')}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #ecf0f1;">{lic.get('orgao', 'N/A')}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #ecf0f1;">{lic.get('uf', 'N/A')}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #ecf0f1; text-align: right;">{valor_fmt}</td>
                </tr>
                """

            valor_total_fmt = f"R$ {valor_total:,.2f}".replace(",", ".")

            html_body = f"""
            <html>
                <head>
                    <meta charset="utf-8">
                    <style>
                        body {{ font-family: Arial, sans-serif; color: #333; }}
                        .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
                        .header {{ background-color: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
                        .content {{ background-color: #f8f9fa; padding: 20px; margin-top: 20px; }}
                        .stats {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                        .stat {{ background: white; padding: 15px; border-radius: 5px; text-align: center; }}
                        .stat-number {{ font-size: 24px; font-weight: bold; color: #3498db; }}
                        .stat-label {{ color: #7f8c8d; font-size: 12px; }}
                        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                        th {{ background-color: #3498db; color: white; padding: 12px; text-align: left; }}
                        .footer {{ margin-top: 20px; font-size: 12px; color: #7f8c8d; border-top: 1px solid #bdc3c7; padding-top: 10px; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h2>📊 {nome_alerta}</h2>
                            <p>Resumo das novas licitações detectadas</p>
                        </div>

                        <div class="stats">
                            <div class="stat">
                                <div class="stat-number">{len(licitacoes)}</div>
                                <div class="stat-label">Licitações</div>
                            </div>
                            <div class="stat">
                                <div class="stat-number">{valor_total_fmt}</div>
                                <div class="stat-label">Valor Total</div>
                            </div>
                        </div>

                        <div class="content">
                            <table>
                                <thead>
                                    <tr>
                                        <th>Edital</th>
                                        <th>Órgão</th>
                                        <th>UF</th>
                                        <th>Valor</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {linhas_tabela}
                                </tbody>
                            </table>
                        </div>

                        <div class="footer">
                            <p>✓ Enviado em: {datetime.now().strftime("%d/%m/%Y às %H:%M:%S")}</p>
                            <p>Sistema Radar de Licitações TI - Alertas Automáticos</p>
                        </div>
                    </div>
                </body>
            </html>
            """

            # Criar mensagem
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"📊 {nome_alerta} - {len(licitacoes)} licitações"
            msg["From"] = self.email_from
            msg["To"] = email_para

            part1 = MIMEText(f"Resumo: {len(licitacoes)} licitações - Valor Total: {valor_total_fmt}", "plain")
            part2 = MIMEText(html_body, "html")
            msg.attach(part1)
            msg.attach(part2)

            # Enviar
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_from, self.senha)
                server.send_message(msg)

            logger.info(f"✓ Resumo enviado para {email_para}: {len(licitacoes)} licitações")
            return True

        except Exception as e:
            logger.error(f"✗ Erro ao enviar resumo por email: {e}")
            return False

    def enviar_email_html(
        self,
        email_para: str,
        assunto: str,
        html_body: str
    ) -> bool:
        """
        Envia email com conteúdo HTML puro

        Args:
            email_para: Email destinatário
            assunto: Assunto do email
            html_body: Conteúdo HTML do email

        Returns:
            True se enviado com sucesso
        """
        try:
            # Criar mensagem
            msg = MIMEMultipart("alternative")
            msg["Subject"] = assunto
            msg["From"] = self.email_from
            msg["To"] = email_para

            # Versão texto simples
            text_body = "Visualize este email em um cliente com suporte a HTML"

            # Adicionar ambas as versões
            part1 = MIMEText(text_body, "plain")
            part2 = MIMEText(html_body, "html")
            msg.attach(part1)
            msg.attach(part2)

            # Enviar
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_from, self.senha)
                server.send_message(msg)

            logger.info(f"✓ Email HTML enviado para {email_para}: {assunto}")
            return True

        except Exception as e:
            logger.error(f"✗ Erro ao enviar email HTML: {e}")
            return False

