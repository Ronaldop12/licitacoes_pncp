"""
Agendamento de tarefas do Radar Licitações TI.
Usa APScheduler para substituir scripts .bat / .ps1.

Tarefas agendadas:
  - Coleta PNCP (padrão: a cada 6h)
  - Coleta portais estaduais (padrão: a cada 12h)
  - Exportação de métricas (padrão: a cada 1h)
  - Limpeza de cache (padrão: diário 03:00)
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

ARQUIVO_CONFIG = "dados/agendamento_config.json"

CONFIG_PADRAO = {
    "coleta_pncp": {
        "habilitado": True,
        "tipo": "interval",
        "horas": 6,
        "descricao": "Coleta PNCP a cada 6 horas",
    },
    "coleta_estaduais": {
        "habilitado": True,
        "tipo": "interval",
        "horas": 12,
        "descricao": "Coleta portais estaduais a cada 12 horas",
    },
    "exportar_metricas": {
        "habilitado": True,
        "tipo": "interval",
        "minutos": 60,
        "descricao": "Exportar métricas a cada hora",
    },
    "limpeza_cache": {
        "habilitado": True,
        "tipo": "cron",
        "hora": 3,
        "minuto": 0,
        "descricao": "Limpeza de cache diária às 03:00",
    },
}


def carregar_config() -> dict:
    if os.path.exists(ARQUIVO_CONFIG):
        try:
            with open(ARQUIVO_CONFIG, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return CONFIG_PADRAO.copy()


def salvar_config(config: dict):
    os.makedirs(os.path.dirname(ARQUIVO_CONFIG), exist_ok=True)
    with open(ARQUIVO_CONFIG, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


# --------------- Persistência de resultados ---------------

def _persistir_resultados(resultados: list):
    """Salva resultados da coleta async em CSV e alimenta DBs auxiliares."""
    import pandas as pd

    df = pd.DataFrame(resultados)
    if df.empty:
        return

    # Salvar CSV
    try:
        csv_path = os.path.join("dados", "licitacoes.csv")
        os.makedirs("dados", exist_ok=True)
        df.to_csv(csv_path, index=False, encoding="utf-8")
        logger.info("[Scheduler] CSV salvo: %d registros", len(df))
    except Exception as e:
        logger.warning("[Scheduler] Falha ao salvar CSV: %s", e)

    # Histórico versionado
    try:
        from historico_db import HistoricoDB
        HistoricoDB().registrar_coleta(df, fonte="PNCP-async", total_verificadas=len(df))
    except Exception as e:
        logger.warning("[Scheduler] Falha ao registrar histórico: %s", e)

    # Rastrear mudanças de fases
    try:
        from fases_db import FasesDB
        FasesDB().processar_coleta(df)
    except Exception as e:
        logger.warning("[Scheduler] Falha ao rastrear fases: %s", e)

    # Registrar preços
    try:
        from precos_db import PrecosDB
        PrecosDB().registrar_precos(df)
    except Exception as e:
        logger.warning("[Scheduler] Falha ao registrar preços: %s", e)

    # Registrar métricas
    try:
        from metricas import MetricasDB
        MetricasDB().registrar_coleta(total_ti=len(df), total_verificadas=len(df), duracao_s=0, erros=0)
    except Exception as e:
        logger.warning("[Scheduler] Falha ao registrar métricas: %s", e)


# --------------- Jobs ---------------

def job_coleta_pncp():
    """Executa a coleta PNCP (tenta assíncrona, fallback síncrona)."""
    logger.info("[Scheduler] Iniciando coleta PNCP...")
    try:
        from coletor_async import coletar_sincrono_wrapper
        resultado = coletar_sincrono_wrapper(dias_atras=15)
        # resultado pode ser lista (legado) ou extraído do dict
        if isinstance(resultado, list):
            licitacoes = resultado
        else:
            licitacoes = resultado
        logger.info("[Scheduler] Coleta assíncrona PNCP concluída: %d resultados", len(licitacoes))
        if licitacoes:
            _persistir_resultados(licitacoes)
    except Exception as e:
        logger.warning("[Scheduler] Coleta assíncrona falhou (%s), usando síncrona...", e)
        try:
            from pncp_radar_ti_plus import main as pncp_main
            pncp_main()
            logger.info("[Scheduler] Coleta síncrona PNCP concluída")
        except Exception as e2:
            logger.error("[Scheduler] Coleta PNCP falhou: %s", e2)


def job_coleta_estaduais():
    """Executa a coleta de portais estaduais."""
    logger.info("[Scheduler] Iniciando coleta portais estaduais...")
    try:
        from coletor_portais_estaduais import ColetorPortaisEstaduais
        coletor = ColetorPortaisEstaduais()
        df = coletor.coletar_todos(dias_atras=15)
        logger.info("[Scheduler] Portais estaduais: %d registros", len(df))
    except Exception as e:
        logger.error("[Scheduler] Coleta estaduais falhou: %s", e)


def job_exportar_metricas():
    """Exporta métricas para arquivo JSON."""
    try:
        from metricas import MetricasDB
        m = MetricasDB()
        m.salvar_json()
        logger.info("[Scheduler] Métricas exportadas")
    except Exception as e:
        logger.error("[Scheduler] Exportar métricas falhou: %s", e)


def job_limpeza_cache():
    """Remove arquivos antigos de cache."""
    import glob
    removidos = 0
    for padrao in ["dados/editais_pdf/*.pdf", "dados/*.tmp"]:
        for arq in glob.glob(padrao):
            try:
                info = os.stat(arq)
                idade_dias = (datetime.now().timestamp() - info.st_mtime) / 86400
                if idade_dias > 30:
                    os.remove(arq)
                    removidos += 1
            except OSError:
                pass
    logger.info("[Scheduler] Limpeza: %d arquivos removidos", removidos)


class AgendadorTarefas:
    """Gerencia o scheduler APScheduler."""

    def __init__(self):
        self.scheduler = None
        self.config = carregar_config()
        self._iniciado = False

    def iniciar(self):
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from apscheduler.triggers.interval import IntervalTrigger
            from apscheduler.triggers.cron import CronTrigger
        except ImportError:
            logger.warning(
                "APScheduler não instalado. Execute: pip install apscheduler"
            )
            return False

        self.scheduler = BackgroundScheduler(timezone="America/Sao_Paulo")

        # Coleta PNCP
        cfg = self.config.get("coleta_pncp", CONFIG_PADRAO["coleta_pncp"])
        if cfg.get("habilitado"):
            self.scheduler.add_job(
                job_coleta_pncp,
                trigger=IntervalTrigger(hours=cfg.get("horas", 6)),
                id="coleta_pncp",
                name="Coleta PNCP",
                replace_existing=True,
            )

        # Coleta estaduais
        cfg = self.config.get("coleta_estaduais", CONFIG_PADRAO["coleta_estaduais"])
        if cfg.get("habilitado"):
            self.scheduler.add_job(
                job_coleta_estaduais,
                trigger=IntervalTrigger(hours=cfg.get("horas", 12)),
                id="coleta_estaduais",
                name="Coleta Portais Estaduais",
                replace_existing=True,
            )

        # Métricas
        cfg = self.config.get("exportar_metricas", CONFIG_PADRAO["exportar_metricas"])
        if cfg.get("habilitado"):
            self.scheduler.add_job(
                job_exportar_metricas,
                trigger=IntervalTrigger(minutes=cfg.get("minutos", 60)),
                id="exportar_metricas",
                name="Exportar Métricas",
                replace_existing=True,
            )

        # Limpeza
        cfg = self.config.get("limpeza_cache", CONFIG_PADRAO["limpeza_cache"])
        if cfg.get("habilitado"):
            self.scheduler.add_job(
                job_limpeza_cache,
                trigger=CronTrigger(
                    hour=cfg.get("hora", 3),
                    minute=cfg.get("minuto", 0),
                ),
                id="limpeza_cache",
                name="Limpeza de Cache",
                replace_existing=True,
            )

        self.scheduler.start()
        self._iniciado = True
        logger.info("[Scheduler] Iniciado com %d tarefas", len(self.scheduler.get_jobs()))
        return True

    def parar(self):
        if self.scheduler and self._iniciado:
            self.scheduler.shutdown(wait=False)
            self._iniciado = False
            logger.info("[Scheduler] Parado")

    def listar_jobs(self) -> list:
        if not self.scheduler or not self._iniciado:
            return []
        jobs = []
        for job in self.scheduler.get_jobs():
            prox = job.next_run_time
            jobs.append({
                "id": job.id,
                "nome": job.name,
                "proxima_execucao": prox.strftime("%Y-%m-%d %H:%M:%S") if prox else "N/A",
                "ativo": prox is not None,
            })
        return jobs

    def executar_agora(self, job_id: str) -> bool:
        """Executa uma tarefa agora, fora do agendamento."""
        mapa = {
            "coleta_pncp": job_coleta_pncp,
            "coleta_estaduais": job_coleta_estaduais,
            "exportar_metricas": job_exportar_metricas,
            "limpeza_cache": job_limpeza_cache,
        }
        func = mapa.get(job_id)
        if func:
            func()
            return True
        return False

    def atualizar_config(self, nova_config: dict):
        self.config.update(nova_config)
        salvar_config(self.config)
        if self._iniciado:
            self.parar()
            self.iniciar()

    @property
    def ativo(self) -> bool:
        return self._iniciado
