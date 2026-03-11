"""
Notificações multi-canal: Slack e Discord (webhooks).
Complementa o sistema de alertas Telegram existente.
"""

import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

import requests

logger = logging.getLogger(__name__)

TIMEOUT = 10  # segundos


class SlackNotifier:
    """Envia notificações via Slack Incoming Webhook."""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.session = requests.Session()

    def enviar(self, texto: str, canal: Optional[str] = None) -> bool:
        """Envia mensagem de texto simples."""
        payload = {"text": texto}
        if canal:
            payload["channel"] = canal
        return self._post(payload)

    def enviar_licitacao(self, licitacao: Dict) -> bool:
        """Envia licitação formatada como block kit do Slack."""
        valor = licitacao.get("valor_estimado", 0)
        valor_fmt = f"R$ {valor:,.2f}" if valor else "Não informado"
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "📡 Nova Licitação de TI", "emoji": True},
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Órgão:*\n{licitacao.get('orgao', 'N/A')}"},
                    {"type": "mrkdwn", "text": f"*UF:*\n{licitacao.get('uf', 'N/A')}"},
                    {"type": "mrkdwn", "text": f"*Valor Estimado:*\n{valor_fmt}"},
                    {"type": "mrkdwn", "text": f"*Modalidade:*\n{licitacao.get('modalidade', 'N/A')}"},
                ],
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Objeto:*\n{licitacao.get('objeto', 'N/A')[:500]}",
                },
            },
        ]
        link = licitacao.get("link_edital")
        if link:
            blocks.append({
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "🔗 Ver Edital"},
                        "url": link,
                    }
                ],
            })
        return self._post({"blocks": blocks})

    def enviar_resumo(self, total: int, novas: int, ufs: Dict[str, int]) -> bool:
        """Envia resumo diário de coleta."""
        top_ufs = ", ".join(f"{k}: {v}" for k, v in sorted(ufs.items(), key=lambda x: -x[1])[:5])
        texto = (
            f"📊 *Resumo Diário — Radar Licitações TI*\n"
            f"• Total monitoradas: {total}\n"
            f"• Novas hoje: {novas}\n"
            f"• Top UFs: {top_ufs}\n"
            f"• Horário: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        )
        return self._post({"text": texto})

    def _post(self, payload: dict) -> bool:
        try:
            resp = self.session.post(self.webhook_url, json=payload, timeout=TIMEOUT)
            if resp.status_code == 200:
                logger.info("Slack: mensagem enviada com sucesso")
                return True
            logger.warning("Slack: erro %d — %s", resp.status_code, resp.text[:200])
            return False
        except requests.RequestException as e:
            logger.error("Slack: erro de conexão — %s", e)
            return False


class DiscordNotifier:
    """Envia notificações via Discord Webhook."""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.session = requests.Session()

    def enviar(self, texto: str) -> bool:
        """Envia mensagem de texto simples."""
        return self._post({"content": texto})

    def enviar_licitacao(self, licitacao: Dict) -> bool:
        """Envia licitação formatada como embed do Discord."""
        valor = licitacao.get("valor_estimado", 0)
        valor_fmt = f"R$ {valor:,.2f}" if valor else "Não informado"
        embed = {
            "title": "📡 Nova Licitação de TI",
            "color": 3447003,  # Azul
            "fields": [
                {"name": "Órgão", "value": licitacao.get("orgao", "N/A"), "inline": False},
                {"name": "UF", "value": licitacao.get("uf", "N/A"), "inline": True},
                {"name": "Valor Estimado", "value": valor_fmt, "inline": True},
                {"name": "Modalidade", "value": licitacao.get("modalidade", "N/A"), "inline": True},
                {"name": "Objeto", "value": licitacao.get("objeto", "N/A")[:1024], "inline": False},
            ],
            "timestamp": datetime.utcnow().isoformat(),
        }
        link = licitacao.get("link_edital")
        if link:
            embed["url"] = link
        return self._post({"embeds": [embed]})

    def enviar_resumo(self, total: int, novas: int, ufs: Dict[str, int]) -> bool:
        """Envia resumo diário de coleta."""
        top_ufs = "\n".join(f"• {k}: {v}" for k, v in sorted(ufs.items(), key=lambda x: -x[1])[:5])
        embed = {
            "title": "📊 Resumo Diário — Radar Licitações TI",
            "color": 15844367,  # Dourado
            "fields": [
                {"name": "Total monitoradas", "value": str(total), "inline": True},
                {"name": "Novas hoje", "value": str(novas), "inline": True},
                {"name": "Top UFs", "value": top_ufs or "N/A", "inline": False},
            ],
            "timestamp": datetime.utcnow().isoformat(),
        }
        return self._post({"embeds": [embed]})

    def _post(self, payload: dict) -> bool:
        try:
            resp = self.session.post(self.webhook_url, json=payload, timeout=TIMEOUT)
            if resp.status_code in (200, 204):
                logger.info("Discord: mensagem enviada com sucesso")
                return True
            logger.warning("Discord: erro %d — %s", resp.status_code, resp.text[:200])
            return False
        except requests.RequestException as e:
            logger.error("Discord: erro de conexão — %s", e)
            return False


class NotificadorMultiCanal:
    """Orquestra envio de notificações em múltiplos canais."""

    def __init__(self):
        self.canais: List[object] = []

    def adicionar_slack(self, webhook_url: str):
        if webhook_url:
            self.canais.append(SlackNotifier(webhook_url))

    def adicionar_discord(self, webhook_url: str):
        if webhook_url:
            self.canais.append(DiscordNotifier(webhook_url))

    def notificar_licitacao(self, licitacao: Dict) -> Dict[str, bool]:
        """Envia licitação para todos os canais configurados."""
        resultados = {}
        for canal in self.canais:
            nome = type(canal).__name__
            resultados[nome] = canal.enviar_licitacao(licitacao)
        return resultados

    def notificar_resumo(self, total: int, novas: int, ufs: Dict[str, int]) -> Dict[str, bool]:
        """Envia resumo para todos os canais configurados."""
        resultados = {}
        for canal in self.canais:
            nome = type(canal).__name__
            resultados[nome] = canal.enviar_resumo(total, novas, ufs)
        return resultados

    @property
    def total_canais(self) -> int:
        return len(self.canais)
