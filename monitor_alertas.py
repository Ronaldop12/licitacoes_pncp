"""
â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
MONITOR DE ALERTAS - Sistema de LicitaÃ§Ãµes PNCP
â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

Script de monitoramento que detecta novas licitaÃ§Ãµes e envia alertas via Telegram.

Uso:
    python monitor_alertas.py
    
    Ou agendar com Task Scheduler (Windows):
    schtasks /create /tn "PNCP_Alertas" /tr "python monitor_alertas.py" /sc minute /mo 5
"""

import pandas as pd
import hashlib
import json
import logging
import time
import os
import sys
from datetime import datetime
from typing import Tuple, List, Dict, Any
from pathlib import Path

# Imports locais
from utils_telegram import TelegramAlerter, validar_token, validar_chat_id
from alerts_db import AlertasDB
from utils_email import EmailAlerter

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# CONFIGURAÃ‡Ã•ES
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

CSV_PATH = "dados/licitacoes.csv"
CSV_PATH_ALT = "licitacoes_TI.csv"
HASH_FILE = "config/hash_anterior.txt"
BACKUP_CSV = "config/backup_licitacoes.csv"
LOG_FILE = "logs/monitor_alertas.log"
CONFIG_FILE = "config/alertas_config.json"

# Criar diretÃ³rios se nÃ£o existirem
Path("config").mkdir(exist_ok=True)
Path("logs").mkdir(exist_ok=True)
Path("dados").mkdir(exist_ok=True)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# FUNÃ‡Ã•ES PRINCIPAIS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def normalizar_colunas_csv(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza nomes de colunas para o esquema esperado pelo monitor."""
    # Garantir que o ID de contratação PNCP está disponível
    if 'numero_controle_pncp' not in df.columns:
        if 'numeroControlePNCP' in df.columns:
            df['numero_controle_pncp'] = df['numeroControlePNCP']
        elif 'numero_controle' in df.columns:
            df['numero_controle_pncp'] = df['numero_controle']
    
    # Manter compatibilidade: numero_edital é sinônimo de controle PNCP
    if 'numero_edital' not in df.columns:
        if 'numero_controle_pncp' in df.columns:
            df['numero_edital'] = df['numero_controle_pncp']
        elif 'numeroControlePNCP' in df.columns:
            df['numero_edital'] = df['numeroControlePNCP']
    
    return df


def carregar_csv() -> pd.DataFrame:
    """
    Carrega CSV de licitacoes

    Returns:
        DataFrame com dados ou DataFrame vazio se falhar
    """
    try:
        if os.path.exists(CSV_PATH):
            df = pd.read_csv(CSV_PATH)
        elif os.path.exists(CSV_PATH_ALT):
            df = pd.read_csv(CSV_PATH_ALT)
        else:
            logger.error(f"CSV nao encontrado em {CSV_PATH} ou {CSV_PATH_ALT}")
            return pd.DataFrame()

        df = normalizar_colunas_csv(df)

        if 'numero_edital' not in df.columns:
            logger.error(
                "CSV sem coluna de identificador (esperado: numero_edital ou numero_controle_pncp)"
            )
            return pd.DataFrame()

        if 'data_publicacao' in df.columns:
            df['data_publicacao'] = pd.to_datetime(df['data_publicacao'], errors='coerce')
        if 'valor_estimado' in df.columns:
            df['valor_estimado'] = pd.to_numeric(df['valor_estimado'], errors='coerce').fillna(0)

        logger.info(f"CSV carregado: {len(df)} registros")
        return df

    except Exception as e:
        logger.error(f"Erro ao carregar CSV: {e}")
        return pd.DataFrame()
def gerar_hash_csv(df: pd.DataFrame) -> str:
    """
    Gera hash MD5 do CSV para detectar mudanÃ§as
    
    Args:
        df: DataFrame
        
    Returns:
        String do hash
    """
    try:
        # Usar apenas valores importantes para hash (nÃ£o incluir timestamps que mudam)
        hash_data = df[['numero_edital', 'orgao', 'valor_estimado']].to_string().encode()
        return hashlib.md5(hash_data).hexdigest()
    except Exception as e:
        logger.error(f"Erro ao gerar hash: {e}")
        return ""


def detectar_novas_licitacoes(df_atual: pd.DataFrame) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Detecta novas licitacoes comparando com backup anterior

    Args:
        df_atual: DataFrame atual

    Returns:
        Tupla (ha_mudancas, lista_de_novas_licitacoes)
    """
    try:
        df_atual = normalizar_colunas_csv(df_atual)

        if 'numero_edital' not in df_atual.columns:
            logger.error("DataFrame atual sem coluna numero_edital")
            return False, []

        if os.path.exists(BACKUP_CSV):
            df_anterior = pd.read_csv(BACKUP_CSV)
            df_anterior = normalizar_colunas_csv(df_anterior)
            logger.info(f"  Registros anteriores: {len(df_anterior)}")
        else:
            logger.warning("  Nenhum backup anterior encontrado (primeira execucao?)")
            df_anterior = pd.DataFrame()

        if len(df_anterior) > 0:
            if 'numero_edital' not in df_anterior.columns:
                logger.warning(
                    "  Backup anterior sem numero_edital; sera tratado como primeira execucao"
                )
                return False, []

            editais_anteriores = set(df_anterior['numero_edital'].astype(str).unique())
            editais_atuais = set(df_atual['numero_edital'].astype(str).unique())

            novos_editais = editais_atuais - editais_anteriores
            logger.info(f"  Novos editais detectados: {len(novos_editais)}")

            if novos_editais:
                novas = df_atual[df_atual['numero_edital'].astype(str).isin(novos_editais)]
                logger.info(f"  Convertendo para lista: {len(novas)} licitacoes")
                return True, novas.to_dict('records')
        else:
            logger.info("  Primeira execucao - fazendo backup inicial")
            return False, []

        return False, []

    except Exception as e:
        logger.error(f"Erro ao detectar novas licitacoes: {e}")
        return False, []
def filtrar_licitacoes_por_alerta(
    licitacoes: List[Dict[str, Any]],
    alerta: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Filtra licitaÃ§Ãµes pela configuraÃ§Ã£o do alerta
    
    Args:
        licitacoes: Lista de licitaÃ§Ãµes
        alerta: ConfiguraÃ§Ã£o do alerta
        
    Returns:
        Lista de licitaÃ§Ãµes que atendem ao critÃ©rio
    """
    try:
        filtradas = []
        ufs_alerta = [str(uf).strip().upper() for uf in alerta.get('ufs', []) if str(uf).strip()]
        monitorar_todas_ufs = not ufs_alerta or "*" in ufs_alerta

        for lic in licitacoes:
            # Verificar UF
            uf_licitacao = str(lic.get('uf', '')).strip().upper()
            if not monitorar_todas_ufs and uf_licitacao not in ufs_alerta:
                continue

            # Verificar valor
            valor = float(lic.get('valor_estimado', 0))
            if valor < alerta['valor_min'] or valor > alerta['valor_max']:
                continue

            # Verificar Ã³rgÃ£o (se nÃ£o for coringa)
            if alerta['orgaos'] != ['*']:
                org = str(lic.get('orgao', '')).upper()
                if not any(o.upper() in org for o in alerta['orgaos']):
                    continue

            # Verificar palavras-chave (se houver)
            if alerta['palavras_chave']:
                objeto = str(lic.get('objeto', '')).lower()
                if not any(palavra.lower() in objeto for palavra in alerta['palavras_chave']):
                    continue

            filtradas.append(lic)

        logger.info(f"  Alerta '{alerta['nome']}': {len(filtradas)} licitaÃ§Ãµes relevantes")
        return filtradas

    except Exception as e:
        logger.error(f"âœ— Erro ao filtrar licitaÃ§Ãµes: {e}")
        return []


def enviar_alertas(
    licitacoes: List[Dict[str, Any]],
    alerta: Dict[str, Any],
    bot: TelegramAlerter,
    db: AlertasDB
) -> int:
    """
    Envia alertas via Telegram para as licitaÃ§Ãµes
    
    Args:
        licitacoes: Lista de licitaÃ§Ãµes
        alerta: ConfiguraÃ§Ã£o do alerta
        bot: InstÃ¢ncia do TelegramAlerter
        db: InstÃ¢ncia do AlertasDB
        
    Returns:
        NÃºmero de alertas enviados com sucesso
    """
    enviados = 0

    try:
        for lic in licitacoes:
            try:
                # Formatar mensagem
                msg = bot.formatar_alerta_licitacao(lic)

                # Enviar
                resultado = bot.enviar_mensagem(
                    alerta['chat_id'],
                    msg,
                    parse_mode="HTML"
                )

                if resultado and resultado.get('ok'):
                    # Registrar no banco
                    db.registrar_alerta_enviado(
                        alerta['id'],
                        lic.get('numero_edital', 'N/A'),
                        float(lic.get('valor_estimado', 0)),
                        lic.get('orgao', 'N/A')
                    )
                    enviados += 1
                    logger.info(f"  âœ“ Alerta enviado: {lic.get('numero_edital')} â†’ {alerta['nome']}")
                else:
                    logger.warning(f"  âš  Falha ao enviar alerta para {alerta['chat_id']}")

                # Pequeno delay para nÃ£o sobrecarregar API
                time.sleep(0.5)

            except Exception as e:
                logger.error(f"  âœ— Erro ao enviar alerta individual: {e}")
                continue

    except Exception as e:
        logger.error(f"âœ— Erro ao enviar alertas: {e}")

    return enviados


def fazer_backup_csv(df: pd.DataFrame):
    """
    Faz backup do CSV para comparaÃ§Ã£o posterior
    
    Args:
        df: DataFrame a fazer backup
    """
    try:
        df.to_csv(BACKUP_CSV, index=False)
        logger.info(f"âœ“ Backup realizado: {BACKUP_CSV}")
    except Exception as e:
        logger.error(f"âœ— Erro ao fazer backup: {e}")


def enviar_resumo_email(
    licitacoes: List[Dict[str, Any]],
    config: Dict[str, Any],
    total_alertas: int
):
    """
    Envia resumo dos alertas por email

    Args:
        licitacoes: Lista de licitacoes detectadas
        config: Configuracao de email
        total_alertas: Total de alertas enviados
    """
    try:
        email_cfg = config.get('email_config', {})

        if not email_cfg.get('ativo'):
            logger.info("Email nao ativo na configuracao")
            return

        if not email_cfg.get('enviar_resumo', True):
            logger.info("Envio de resumo por email desativado na configuracao")
            return

        if not email_cfg.get('email_from') or not email_cfg.get('senha_app'):
            logger.warning("Email ou senha nao configurados")
            return

        destinatario = email_cfg.get('email_destinatario', email_cfg['email_from'])
        if destinatario == "mesma conta":
            destinatario = email_cfg['email_from']

        alerter = EmailAlerter(
            smtp_server=email_cfg.get('smtp_server', 'smtp.gmail.com'),
            smtp_port=email_cfg.get('smtp_port', 587),
            email_from=email_cfg['email_from'],
            senha=email_cfg['senha_app']
        )

        if not alerter.validar_configuracao():
            logger.error("Credenciais de email invalidas")
            return

        html = """
        <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: Arial, sans-serif; background: #f5f5f5; }}
                    .container {{ max-width: 600px; margin: 20px auto; background: white; padding: 20px; border-radius: 5px; }}
                    .header {{ background: #2c3e50; color: white; padding: 15px; border-radius: 5px; text-align: center; }}
                    .content {{ margin: 20px 0; }}
                    .licitacao {{ background: #ecf0f1; padding: 10px; margin: 10px 0; border-left: 4px solid #3498db; }}
                    .footer {{ text-align: center; color: #7f8c8d; font-size: 12px; margin-top: 20px; }}
                    .stats {{ background: #e8f4f8; padding: 15px; border-radius: 5px; text-align: center; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>Resumo de Alertas PNCP</h2>
                        <p>{data_hora}</p>
                    </div>

                    <div class="stats">
                        <p><strong>Novas Licitacoes Detectadas:</strong> {total_licitacoes}</p>
                        <p><strong>Alertas Enviados:</strong> {total_alertas}</p>
                    </div>

                    <div class="content">
                        <h3>Detalhes:</h3>
        """.format(
            data_hora=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            total_licitacoes=len(licitacoes),
            total_alertas=total_alertas
        )

        for lic in licitacoes[:10]:
            html += f"""
            <div class="licitacao">
                <p><strong>Edital:</strong> {lic.get('numero_edital', 'N/A')}</p>
                <p><strong>Orgao:</strong> {lic.get('orgao', 'N/A')}</p>
                <p><strong>Valor:</strong> R$ {lic.get('valor_estimado', 0):,.2f}</p>
                <p><strong>Objeto:</strong> {str(lic.get('objeto', 'N/A'))[:100]}...</p>
            </div>
            """

        if len(licitacoes) > 10:
            html += f"<p>... e mais {len(licitacoes) - 10} licitacoes</p>"

        html += """
                    </div>

                    <div class="footer">
                        <p>Sistema de Monitoramento de Licitacoes PNCP</p>
                        <p>Este e um email automatico. Nao responda.</p>
                    </div>
                </div>
            </body>
        </html>
        """

        enviado = alerter.enviar_email_html(destinatario, "Resumo de Alertas PNCP", html)
        if enviado:
            logger.info(f"Resumo enviado por email para: {destinatario}")
        else:
            logger.error(f"Falha ao enviar resumo por email para: {destinatario}")

    except Exception as e:
        logger.error(f"Erro ao enviar resumo por email: {e}")
def processar_alertas(token: str, db: AlertasDB):
    """
    FunÃ§Ã£o principal que processa todos os alertas
    
    Args:
        token: Token do bot Telegram
        db: InstÃ¢ncia do AlertasDB
    """
    logger.info("=" * 80)
    logger.info(f"INICIANDO PROCESSAMENTO DE ALERTAS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Arquivo CSV: {CSV_PATH if os.path.exists(CSV_PATH) else CSV_PATH_ALT}")

    try:
        # 1. Carregar CSV
        df_atual = carregar_csv()
        if df_atual.empty:
            logger.error("âœ— Falha ao carregar CSV. Abortando.")
            return

        # 2. Detectar mudanÃ§as
        logger.info("Detectando novas licitaÃ§Ãµes...")
        ha_mudancas, novas_licitacoes = detectar_novas_licitacoes(df_atual)

        if not ha_mudancas:
            logger.info("â„¹ Nenhuma mudanÃ§a detectada")
            # Mesmo sem mudanÃ§as, atualizar backup
            fazer_backup_csv(df_atual)
            db.atualizar_monitoramento(ultimo_check=datetime.now().isoformat())
            logger.info("=" * 80)
            return

        logger.info(f"âœ“ {len(novas_licitacoes)} novas licitaÃ§Ãµes detectadas!")

        # 3. Fazer backup
        fazer_backup_csv(df_atual)

        # 4. Inicializar bot
        if not validar_token(token):
            logger.error("âœ— Token Telegram invÃ¡lido!")
            return

        bot = TelegramAlerter(token)

        # 5. Processar cada alerta
        alertas_ativos = db.listar_alertas(apenas_ativos=True)
        logger.info(f"Processando {len(alertas_ativos)} alertas ativos...")

        total_enviados = 0

        for alerta in alertas_ativos:
            try:
                logger.info(f"\nâ”œâ”€ Processando alerta: '{alerta['nome']}'")

                # Filtrar licitaÃ§Ãµes para este alerta
                licitacoes_alerta = filtrar_licitacoes_por_alerta(novas_licitacoes, alerta)

                if not licitacoes_alerta:
                    logger.info(f"â””â”€ Nenhuma licitaÃ§Ã£o relevante para este alerta")
                    continue

                # Enviar alertas
                enviados = enviar_alertas(licitacoes_alerta, alerta, bot, db)
                total_enviados += enviados

                logger.info(f"â””â”€ {enviados} alerta(s) enviado(s)")

            except Exception as e:
                logger.error(f"âœ— Erro ao processar alerta '{alerta['nome']}': {e}")
                continue

        # 6. Atualizar status
        logger.info(f"\n{'=' * 80}")
        logger.info(f"RESUMO: {total_enviados} alerta(s) enviado(s) com sucesso")
        logger.info(f"PrÃ³xima verificaÃ§Ã£o: em ~5 minutos")

        # 7. Enviar resumo por email
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    if total_enviados > 0:
                        enviar_resumo_email(novas_licitacoes, config, total_enviados)
                    else:
                        logger.info("â„¹ Nenhum alerta enviado, resumo de email nÃ£o serÃ¡ enviado")
        except Exception as e:
            logger.error(f"âœ— Erro ao enviar resumo por email: {e}")

        db.atualizar_monitoramento(
            ultimo_check=datetime.now().isoformat(),
            total_alertas_enviados=db.obter_status_monitoramento().get('total_alertas_enviados', 0) + total_enviados
        )

    except Exception as e:
        logger.error(f"âœ— Erro crÃ­tico no processamento: {e}")
        db.atualizar_monitoramento(ultimo_erro=str(e))

    finally:
        logger.info("=" * 80)


def carregar_config_token() -> str:
    """
    Carrega token do Telegram de config/alertas_config.json
    
    Returns:
        Token ou string vazia se nÃ£o encontrado
    """
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                token = config.get('telegram_token', '').strip()
                if token and token != "SEU_TOKEN_AQUI":
                    return token
    except Exception as e:
        logger.warning(f"Erro ao carregar config: {e}")

    return ""


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# MAIN
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

if __name__ == "__main__":
    logger.info("ðŸš€ Monitor de Alertas PNCP iniciado")

    # Carregar token
    token = carregar_config_token()
    if not token:
        logger.error("âœ— Token do Telegram nÃ£o configurado!")
        logger.error("  Configure em: config/alertas_config.json (campo 'telegram_token')")
        sys.exit(1)

    # Inicializar banco
    db = AlertasDB()

    # Processar alertas
    processar_alertas(token, db)

    logger.info("âœ“ Processamento concluÃ­do!")
