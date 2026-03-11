"""
Métricas e monitoramento do sistema.
Exporta métricas em formato Prometheus, registra eventos para observabilidade,
e integra com Sentry para rastreamento de erros em produção.
"""

import os
import time
import json
import sqlite3
import logging
import traceback
from contextlib import closing
from datetime import datetime
from typing import Dict, List, Optional
from threading import Lock

logger = logging.getLogger(__name__)

DB_PATH = os.path.join("dados", "metricas.db")
METRICAS_JSON = os.path.join("dados", "metricas.json")

# ========== INTEGRAÇÃO SENTRY ==========

_sentry_inicializado = False


def inicializar_sentry(dsn: Optional[str] = None):
    """
    Inicializa Sentry SDK para captura automática de exceções.
    DSN via parâmetro ou variável de ambiente SENTRY_DSN.
    """
    global _sentry_inicializado
    dsn = dsn or os.environ.get("SENTRY_DSN", "")
    if not dsn or _sentry_inicializado:
        return False
    try:
        import sentry_sdk
        from sentry_sdk.integrations.logging import LoggingIntegration

        sentry_logging = LoggingIntegration(
            level=logging.WARNING,
            event_level=logging.ERROR,
        )
        sentry_sdk.init(
            dsn=dsn,
            integrations=[sentry_logging],
            traces_sample_rate=float(os.environ.get("SENTRY_TRACES_RATE", "0.1")),
            environment=os.environ.get("ENV", "development"),
            release=os.environ.get("APP_VERSION", "2.0.0"),
        )
        _sentry_inicializado = True
        logger.info("Sentry inicializado com sucesso")
        return True
    except ImportError:
        logger.debug("sentry-sdk não instalado. Monitoramento Sentry desabilitado.")
        return False
    except Exception as e:
        logger.warning("Falha ao inicializar Sentry: %s", e)
        return False


def capturar_excecao(exc: Exception, contexto: Optional[Dict] = None):
    """Envia exceção para Sentry (se disponível) e registra localmente."""
    if _sentry_inicializado:
        try:
            import sentry_sdk
            with sentry_sdk.push_scope() as scope:
                if contexto:
                    for k, v in contexto.items():
                        scope.set_extra(k, v)
                sentry_sdk.capture_exception(exc)
        except Exception:
            pass
    logger.error("Exceção capturada: %s\n%s", exc, traceback.format_exc())


# ========== HEALTH CHECK ==========

def health_check() -> Dict:
    """Verifica saúde de todos os componentes do sistema."""
    status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "componentes": {},
    }

    # Check dados dir
    dados_ok = os.path.exists("dados")
    status["componentes"]["dados_dir"] = {"status": "ok" if dados_ok else "erro"}

    # Check CSV
    csv_path = os.path.join("dados", "licitacoes.csv")
    csv_ok = os.path.exists(csv_path)
    status["componentes"]["csv_dados"] = {
        "status": "ok" if csv_ok else "warning",
        "tamanho_bytes": os.path.getsize(csv_path) if csv_ok else 0,
    }

    # Check DBs
    for nome, caminho in [
        ("metricas_db", DB_PATH),
        ("usuarios_db", os.path.join("dados", "usuarios.db")),
        ("alertas_db", os.path.join("dados", "alertas.db")),
        ("precos_db", os.path.join("dados", "precos.db")),
    ]:
        existe = os.path.exists(caminho)
        status["componentes"][nome] = {
            "status": "ok" if existe else "warning",
            "tamanho_bytes": os.path.getsize(caminho) if existe else 0,
        }

    # Check disco
    try:
        import shutil
        uso = shutil.disk_usage("dados" if os.path.exists("dados") else ".")
        pct = (uso.used / uso.total) * 100
        status["componentes"]["disco"] = {
            "status": "ok" if pct < 90 else "warning" if pct < 95 else "critical",
            "uso_percentual": round(pct, 1),
            "livre_gb": round(uso.free / (1024 ** 3), 2),
        }
    except Exception:
        status["componentes"]["disco"] = {"status": "unknown"}

    # Determinar status global
    statuses = [c.get("status") for c in status["componentes"].values()]
    if "critical" in statuses:
        status["status"] = "unhealthy"
    elif "erro" in statuses:
        status["status"] = "degraded"

    return status


class MetricasDB:
    """Coleta e persiste métricas operacionais do sistema."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._lock = Lock()
        d = os.path.dirname(db_path)
        if d and not os.path.exists(d):
            os.makedirs(d)
        self._criar_tabelas()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _criar_tabelas(self):
        with closing(self._conn()) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS eventos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo TEXT NOT NULL,
                    componente TEXT NOT NULL,
                    mensagem TEXT DEFAULT '',
                    valor REAL DEFAULT 0,
                    criado_em TIMESTAMP NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS metricas_snapshot (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chave TEXT NOT NULL,
                    valor REAL NOT NULL,
                    criado_em TIMESTAMP NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_eventos_tipo ON eventos(tipo)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_eventos_data ON eventos(criado_em)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_snap_chave ON metricas_snapshot(chave)")
            conn.commit()

    def registrar_evento(self, tipo: str, componente: str, mensagem: str = "", valor: float = 0):
        """Registra um evento operacional."""
        with self._lock:
            with closing(self._conn()) as conn:
                conn.execute(
                    "INSERT INTO eventos (tipo, componente, mensagem, valor, criado_em) VALUES (?, ?, ?, ?, ?)",
                    (tipo, componente, mensagem, valor, datetime.now().isoformat()),
                )
                conn.commit()

    def registrar_coleta(self, total_ti: int, total_verificadas: int, duracao_s: float, erros: int = 0):
        """Registra métricas de uma coleta."""
        agora = datetime.now().isoformat()
        with self._lock:
            with closing(self._conn()) as conn:
                for chave, valor in [
                    ("coleta_total_ti", total_ti),
                    ("coleta_total_verificadas", total_verificadas),
                    ("coleta_duracao_segundos", duracao_s),
                    ("coleta_erros", erros),
                ]:
                    conn.execute(
                        "INSERT INTO metricas_snapshot (chave, valor, criado_em) VALUES (?, ?, ?)",
                        (chave, valor, agora),
                    )
                conn.commit()

    def registrar_requisicao_api(self, endpoint: str, status_code: int, duracao_ms: float):
        """Registra uma requisição à API REST."""
        self.registrar_evento("api_request", endpoint, f"HTTP {status_code}", duracao_ms)

    def ultimos_eventos(self, limite: int = 50, tipo: Optional[str] = None):
        with closing(self._conn()) as conn:
            if tipo:
                rows = conn.execute(
                    "SELECT * FROM eventos WHERE tipo = ? ORDER BY criado_em DESC LIMIT ?",
                    (tipo, limite),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM eventos ORDER BY criado_em DESC LIMIT ?", (limite,)
                ).fetchall()
            return [dict(r) for r in rows]

    def metricas_resumo(self) -> Dict:
        """Retorna resumo de métricas para exibição."""
        with closing(self._conn()) as conn:
            cur = conn.cursor()

            cur.execute("""
                SELECT valor, criado_em FROM metricas_snapshot
                WHERE chave = 'coleta_total_ti'
                ORDER BY criado_em DESC LIMIT 1
            """)
            row = cur.fetchone()
            ultima_coleta_ti = dict(row) if row else {}

            cur.execute("""
                SELECT COUNT(*) FROM eventos
                WHERE tipo = 'erro'
                AND criado_em > datetime('now', '-1 day')
            """)
            erros_24h = cur.fetchone()[0]

            cur.execute("SELECT tipo, COUNT(*) as qtd FROM eventos GROUP BY tipo ORDER BY qtd DESC")
            por_tipo = {r["tipo"]: r["qtd"] for r in cur.fetchall()}

            metricas_coleta = {}
            for chave in ["coleta_total_ti", "coleta_duracao_segundos", "coleta_erros"]:
                cur.execute(
                    "SELECT valor FROM metricas_snapshot WHERE chave = ? ORDER BY criado_em DESC LIMIT 1",
                    (chave,),
                )
                r = cur.fetchone()
                metricas_coleta[chave] = r[0] if r else 0

        return {
            "ultima_coleta": ultima_coleta_ti,
            "erros_24h": erros_24h,
            "eventos_por_tipo": por_tipo,
            "metricas_coleta": metricas_coleta,
        }

    def exportar_prometheus(self) -> str:
        """Exporta métricas no formato de texto Prometheus."""
        resumo = self.metricas_resumo()
        stats = self.estatisticas()
        hc = health_check()

        linhas = [
            "# HELP radar_coleta_total_ti Total de licitações TI na última coleta",
            "# TYPE radar_coleta_total_ti gauge",
            f"radar_coleta_total_ti {resumo['metricas_coleta'].get('coleta_total_ti', 0)}",
            "",
            "# HELP radar_coleta_duracao_segundos Duração da última coleta em segundos",
            "# TYPE radar_coleta_duracao_segundos gauge",
            f"radar_coleta_duracao_segundos {resumo['metricas_coleta'].get('coleta_duracao_segundos', 0)}",
            "",
            "# HELP radar_coleta_erros Erros na última coleta",
            "# TYPE radar_coleta_erros gauge",
            f"radar_coleta_erros {resumo['metricas_coleta'].get('coleta_erros', 0)}",
            "",
            "# HELP radar_erros_24h Erros nas últimas 24 horas",
            "# TYPE radar_erros_24h gauge",
            f"radar_erros_24h {resumo['erros_24h']}",
            "",
            "# HELP radar_eventos_total Total de eventos registrados",
            "# TYPE radar_eventos_total counter",
            f"radar_eventos_total {stats.get('total_eventos', 0)}",
            "",
            "# HELP radar_coletas_total Total de coletas realizadas",
            "# TYPE radar_coletas_total counter",
            f"radar_coletas_total {stats.get('total_coletas', 0)}",
            "",
            "# HELP radar_erros_total Total de erros acumulados",
            "# TYPE radar_erros_total counter",
            f"radar_erros_total {stats.get('total_erros', 0)}",
            "",
            "# HELP radar_health_status Status do sistema (1=healthy, 0=unhealthy)",
            "# TYPE radar_health_status gauge",
            f"radar_health_status {1 if hc['status'] == 'healthy' else 0}",
            "",
        ]

        # Métricas por tipo de evento
        for tipo, qtd in resumo.get("eventos_por_tipo", {}).items():
            tipo_safe = tipo.replace("-", "_").replace(" ", "_")
            linhas.append(f'radar_eventos_por_tipo{{tipo="{tipo_safe}"}} {qtd}')

        # Métricas dos componentes
        for comp, info in hc.get("componentes", {}).items():
            comp_safe = comp.replace("-", "_")
            val = 1 if info.get("status") == "ok" else 0
            linhas.append(f'radar_componente_status{{componente="{comp_safe}"}} {val}')

        linhas.append("")
        return "\n".join(linhas)

    def salvar_json(self, caminho: str = METRICAS_JSON):
        """Salva resumo de métricas em JSON para dashboards externos."""
        resumo = self.metricas_resumo()
        resumo["exportado_em"] = datetime.now().isoformat()
        os.makedirs(os.path.dirname(caminho) or ".", exist_ok=True)
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(resumo, f, indent=2, ensure_ascii=False)

    def estatisticas(self) -> Dict:
        """Retorna estatísticas gerais para exibição no dashboard."""
        with closing(self._conn()) as conn:
            cur = conn.cursor()

            cur.execute("SELECT COUNT(*) FROM eventos")
            total_eventos = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM metricas_snapshot WHERE chave = 'coleta_total_ti'")
            total_coletas = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM eventos WHERE tipo = 'erro'")
            total_erros = cur.fetchone()[0]

            cur.execute("SELECT criado_em FROM eventos ORDER BY criado_em DESC LIMIT 1")
            row = cur.fetchone()
            ultimo = row[0] if row else "N/A"

        return {
            "total_eventos": total_eventos,
            "total_coletas": total_coletas,
            "total_erros": total_erros,
            "ultimo_evento": ultimo,
        }
