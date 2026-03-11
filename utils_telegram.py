"""
═══════════════════════════════════════════════════════════════════════════════
UTILITÁRIOS DE TELEGRAM - Sistema de Alertas PNCP
═══════════════════════════════════════════════════════════════════════════════

Módulo para envio de mensagens e alertas via Telegram Bot API.

Uso:
    from utils_telegram import TelegramAlerter
    bot = TelegramAlerter(token="SEU_TOKEN")
    bot.enviar_mensagem("-123456789", "Olá!")
"""

import requests
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from urllib.parse import quote

# Configurar logging
logger = logging.getLogger(__name__)


class TelegramAlerter:
    """Classe para enviar mensagens e alertas via Telegram Bot API"""

    def __init__(self, token: str):
        """
        Inicializa o alertador do Telegram
        
        Args:
            token: Token do bot Telegram (obtido em @BotFather)
        """
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.session = requests.Session()
        logger.info(f"TelegramAlerter inicializado com token: {token[:10]}...")

    def enviar_mensagem(
        self, 
        chat_id: str, 
        mensagem: str,
        parse_mode: str = "HTML"
    ) -> Optional[Dict[str, Any]]:
        """
        Envia mensagem para chat/canal do Telegram
        
        Args:
            chat_id: ID do chat ou canal (negativo para grupos/canais)
            mensagem: Texto da mensagem (HTML permitido)
            parse_mode: Modo de parse ("HTML", "Markdown", "MarkdownV2")
            
        Returns:
            Resposta JSON da API ou None em caso de erro
        """
        try:
            response = self.session.post(
                f"{self.base_url}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": mensagem,
                    "parse_mode": parse_mode,
                    "disable_web_page_preview": False
                },
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"✓ Mensagem enviada para {chat_id}")
                return response.json()
            else:
                logger.error(f"✗ Erro ao enviar: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"✗ Erro de conexão ao enviar para {chat_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"✗ Erro inesperado ao enviar para {chat_id}: {e}")
            return None

    def enviar_mensagem_com_botoes(
        self,
        chat_id: str,
        mensagem: str,
        botoes: list
    ) -> Optional[Dict[str, Any]]:
        """
        Envia mensagem com botões inline (substituídos por links no texto)
        
        Args:
            chat_id: ID do chat
            mensagem: Texto da mensagem
            botoes: Lista de dicts com {'text': 'Texto', 'url': 'https://...'}
            
        Returns:
            Resposta da API
        """
        try:
            # Adicionar botões como links no final da mensagem
            if botoes:
                mensagem += "\n\n"
                for btn in botoes:
                    mensagem += f'<a href="{btn["url"]}">{btn["text"]}</a> | '
                mensagem = mensagem.rstrip(" | ")
            
            return self.enviar_mensagem(chat_id, mensagem)
            
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem com botões: {e}")
            return None

    def formatar_alerta_licitacao(self, licitacao: Dict[str, Any]) -> str:
        """
        Formata uma licitação como mensagem formatada para Telegram
        
        Args:
            licitacao: Dicionário com dados da licitação
            
        Returns:
            String formatada em HTML para Telegram
        """
        try:
            # Extrair dados com fallback
            orgao = licitacao.get('orgao', 'N/A')
            objeto = licitacao.get('objeto', 'N/A')
            valor = licitacao.get('valor_estimado', 0)
            uf = licitacao.get('uf', 'N/A')
            municipio = licitacao.get('municipio', 'N/A')
            data = licitacao.get('data_publicacao', 'N/A')
            numero_edital = licitacao.get('numero_edital', 'N/A')
            
            # Obter ID de contratação PNCP (campo prioritário para gerar link)
            numero_controle = (
                licitacao.get('numero_controle_pncp') or 
                licitacao.get('numero_controle') or 
                numero_edital
            )
            
            # Formatar valor como moeda
            try:
                valor_fmt = f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            except:
                valor_fmt = f"R$ {valor}"
            
            # Criar link para PNCP - usando ID de contratação (não o edital)
            if numero_controle != "N/A" and numero_controle:
                # Usar quote para codificar URL corretamente
                numero_encoded = quote(str(numero_controle).strip())
                # Usar número de controle para busca precisa no PNCP
                link_pncp = f"https://pncp.gov.br/app/editais?numero={numero_encoded}"
            else:
                link_pncp = "https://pncp.gov.br/app/editais"
            
            # Formatar objeto (truncar se muito longo)
            objeto_fmt = objeto[:120] + "..." if len(str(objeto)) > 120 else objeto
            
            msg = f"""<b>🎯 NOVA LICITAÇÃO DETECTADA!</b>

<b>Órgão:</b> {orgao}
<b>Objeto:</b> {objeto_fmt}
<b>Valor:</b> {valor_fmt}
<b>UF:</b> {uf}
<b>Município:</b> {municipio}
<b>Data:</b> {data}
<b>Edital:</b> {numero_edital}

<a href="{link_pncp}">🔗 Ver no PNCP</a>"""
            
            return msg
            
        except Exception as e:
            logger.error(f"Erro ao formatar alerta: {e}")
            return f"<b>⚠️ Erro ao formatar licitação</b>\n{str(e)}"

    def formatar_resumo_alertas(self, alertas: list) -> str:
        """
        Formata múltiplos alertas como resumo diário
        
        Args:
            alertas: Lista de dicionários de licitações
            
        Returns:
            String formatada em HTML
        """
        try:
            if not alertas:
                return "<b>📋 Nenhuma licitação encontrada neste período</b>"
            
            msg = f"<b>📊 RESUMO DE LICITAÇÕES - {datetime.now().strftime('%d/%m/%Y')}</b>\n"
            msg += f"<b>Total:</b> {len(alertas)} licitações\n\n"
            
            valor_total = sum(float(a.get('valor_estimado', 0)) for a in alertas)
            msg += f"<b>Valor Total:</b> R$ {valor_total:,.2f}\n\n"
            
            # Top 5 por valor
            top_5 = sorted(alertas, key=lambda x: float(x.get('valor_estimado', 0)), reverse=True)[:5]
            msg += "<b>🏆 Top 5 Maiores Valores:</b>\n"
            
            for i, lic in enumerate(top_5, 1):
                valor = float(lic.get('valor_estimado', 0))
                valor_fmt = f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                msg += f"{i}. {lic.get('orgao', 'N/A')} - {valor_fmt}\n"
            
            return msg
            
        except Exception as e:
            logger.error(f"Erro ao formatar resumo: {e}")
            return f"<b>⚠️ Erro ao formatar resumo</b>\n{str(e)}"

    def formatar_confirmacao_config(self, config: Dict[str, Any]) -> str:
        """
        Formata mensagem de confirmação de configuração de alerta
        
        Args:
            config: Dicionário com configuração do alerta
            
        Returns:
            String formatada em HTML
        """
        try:
            msg = f"""<b>✅ Alerta Configurado com Sucesso!</b>

<b>Nome:</b> {config.get('nome', 'N/A')}
<b>Status:</b> {'🟢 Ativo' if config.get('ativo') else '🔴 Inativo'}
<b>Estados (UFs):</b> {', '.join(config.get('ufs', []))}
<b>Valor Mín:</b> R$ {float(config.get('valor_min', 0)):,.2f}
<b>Valor Máx:</b> R$ {float(config.get('valor_max', 999999999)):,.2f}
<b>Órgãos:</b> {', '.join(config.get('orgaos', ['Todos']))}
<b>Palavras-chave:</b> {', '.join(config.get('palavras_chave', ['Nenhuma']))}

<i>Você receberá notificações quando novas licitações forem detectadas!</i>"""
            
            return msg
            
        except Exception as e:
            logger.error(f"Erro ao formatar confirmação: {e}")
            return f"<b>⚠️ Erro ao formatar confirmação</b>\n{str(e)}"

    def testar_conexao(self) -> bool:
        """
        Testa se o token é válido e a conexão com Telegram funciona
        
        Returns:
            True se conexão OK, False caso contrário
        """
        try:
            response = self.session.get(
                f"{self.base_url}/getMe",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    bot_info = data.get('result', {})
                    logger.info(f"✓ Conexão OK - Bot: @{bot_info.get('username')}")
                    return True
                else:
                    logger.error(f"✗ Token inválido: {data.get('description')}")
                    return False
            else:
                logger.error(f"✗ Erro na conexão: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"✗ Erro ao testar conexão: {e}")
            return False

    def obter_info_bot(self) -> Optional[Dict[str, Any]]:
        """
        Obtém informações do bot
        
        Returns:
            Dicionário com informações do bot ou None
        """
        try:
            response = self.session.get(f"{self.base_url}/getMe", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    return data.get('result')
            return None
        except Exception as e:
            logger.error(f"Erro ao obter info do bot: {e}")
            return None


def criar_link_pncp(numero_edital: str) -> str:
    """
    Cria link para edital no PNCP
    
    Args:
        numero_edital: Número do edital
        
    Returns:
        URL para o edital no PNCP
    """
    return f"https://www.pncp.gov.br/app/editais?numero={quote(str(numero_edital))}"


def validar_token(token: str) -> bool:
    """
    Valida se um token é um token Telegram válido (formato)
    
    Args:
        token: Token a validar
        
    Returns:
        True se parece ser válido, False caso contrário
    """
    if not token or not isinstance(token, str):
        return False
    
    # Token Telegram tem formato: 123456:ABC-DEF1234ghIKL-zyx57W2v1u123ew11
    parts = token.split(':')
    if len(parts) != 2:
        return False
    
    if not parts[0].isdigit():
        return False
    
    if len(parts[1]) < 20:
        return False
    
    return True


def validar_chat_id(chat_id: str) -> bool:
    """
    Valida se um chat_id tem formato válido
    
    Args:
        chat_id: ID do chat a validar
        
    Returns:
        True se formato válido, False caso contrário
    """
    if not chat_id or not isinstance(chat_id, str):
        return False
    
    cleaned = chat_id.strip()
    
    # Pode ser número, número negativo, ou @username
    if cleaned.startswith('@'):
        return len(cleaned) > 1
    
    # Tentar converter para int
    try:
        int(cleaned)
        return True
    except ValueError:
        return False
