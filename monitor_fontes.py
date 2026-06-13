"""
═══════════════════════════════════════════════════════════════════════════════
MONITORAMENTO DE FONTES E APIs COMPLEMENTARES
═══════════════════════════════════════════════════════════════════════════════
Módulo para monitorar a saúde, disponibilidade e mudanças de endpoints
das APIs de licitações (PNCP, estaduais, complementares).

Uso:
    from monitor_fontes import MonitorFontes
    monitor = MonitorFontes()
    status = monitor.verificar_todas()
    monitor.enviar_alertas_problemas(status)

Funcionalidades:
- Health check periódico de cada fonte
- Detecção de mudanças de endpoint/API
- Cache de respostas quando API falha
- Métricas de disponibilidade (uptime)
- Alertas quando fontes ficam indisponíveis
"""

import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

import requests

logger = logging.getLogger(__name__)

DB_PATH = os.path.join("dados", "monitor_fontes.db")
STATE_FILE = os.path.join("dados", "monitor_fontes_estado.json")


@dataclass
class StatusFonte:
    """Representa o status atual de uma fonte de dados."""
    nome: str
    url: str
    disponivel: bool
    tempo_resposta_ms: float
    http_status: Optional[int]
    ultimo_sucesso: Optional[str]
    ultima_falha: Optional[str]
    mensagem_erro: str
    uptime_24h: float  # percentual
    total_checks: int
    total_falhas: int
    mudanca_detectada: bool
    cache_disponivel: bool


class MonitorFontes:
    """
    Monitora a saúde de todas as fontes de licitações.
    Detecta indisponibilidade, mudanças de API e mantém cache de fallback.
    """

    FONTES = {
        "PNCP": {
            "url": "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao",
            "timeout": 30,
            "headers": {"Accept": "application/json", "User-Agent": "RadarLicitacoesTI/Monitor"},
            "params": {"pagina": 1, "tamanhoPagina": 1},
        },
        "Compras.gov.br": {
            "url": "https://compras.dados.gov.br/contratos/v1/contratos.json",
            "timeout": 30,
            "headers": {"Accept": "application/json"},
            "params": {},
        },
        "BEC-SP": {
            "url": "https://www.bec.sp.gov.br/BEC_API/api/OC",
            "timeout": 30,
            "headers": {"Accept": "application/json", "User-Agent": "RadarLicitacoesTI/Monitor"},
            "params": {},
        },
        "CELIC-RS": {
            "url": "https://www.celic.rs.gov.br/api/licitacoes",
            "timeout": 30,
            "headers": {"Accept": "application/json", "User-Agent": "RadarLicitacoesTI/Monitor"},
            "params": {},
        },
        "Licitações-e": {
            "url": "https://www.licitacoes-e.com.br/aop/rest/busca/licitacoes",
            "timeout": 30,
            "headers": {"Accept": "application/json", "User-Agent": "RadarLicitacoesTI/Monitor"},
            "params": {"pagina": 1, "tamanhoPagina": 1},
        },
        "Querido Diário": {
            "url": "https://api.queridodiario.ok.org.br/api/gazettes",
            "timeout": 30,
            "headers": {"Accept": "application/json"},
            "params": {"size": 1},
        },
        "BEC-PE": {
            "url": "https://www.bec.pe.gov.br/BEC_API/api/OC",
            "timeout": 30,
            "headers": {"Accept": "application/json", "User-Agent": "RadarLicitacoesTI/Monitor"},
            "params": {},
        },
        "BEC-CE": {
            "url": "https://www.bec.ce.gov.br/BEC_API/api/OC",
            "timeout": 30,
            "headers": {"Accept": "application/json", "User-Agent": "RadarLicitacoesTI/Monitor"},
            "params": {},
        },
        "BEC-BA": {
            "url": "https://www.bec.ba.gov.br/BEC_API/api/OC",
            "timeout": 30,
            "headers": {"Accept": "application/json", "User-Agent": "RadarLicitacoesTI/Monitor"},
            "params": {},
        },
        "ComprasNet": {
            "url": "https://compras.dados.gov.br/contratos/v1/contratos.json",
            "timeout": 30,
            "headers": {"Accept": "application/json"},
            "params": {},
        },
        "BBM": {
            "url": "https://www.bb.com.br/pbb/pagina-inicial/canais-digitais/licitacoes",
            "timeout": 30,
            "headers": {"Accept": "text/html", "User-Agent": "Mozilla/5.0"},
            "params": {},
        },
        "e-OUV/e-SIC": {
            "url": "https://falabr.cgu.gov.br/publico/Manifestacao/RegistrarManifestacao.aspx",
            "timeout": 30,
            "headers": {"Accept": "text/html", "User-Agent": "Mozilla/5.0"},
            "params": {},
        },
        "SICAF/CAGEF": {
            "url": "https://www2.sicaf.tesouro.gov.br/sicafapp/index.jsf",
            "timeout": 30,
            "headers": {"Accept": "text/html", "User-Agent": "Mozilla/5.0"},
            "params": {},
        },
        "Portal da Transparência": {
            "url": "http://www.portaltransparencia.gov.br/api-de-dados/contratos",
            "timeout": 30,
            "headers": {"Accept": "application/json", "chave-api-dados": "demo"},
            "params": {"pagina": 1},
        },
    }

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.sessao = requests.Session()
        self._carregar_estado()
        self._inicializar_db()

    def _carregar_estado(self):
        """Carrega estado anterior do monitoramento."""
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    self.estado = json.load(f)
            except Exception:
                self.estado = {}
        else:
            self.estado = {}

    def _salvar_estado(self):
        """Persiste estado atual do monitoramento."""
        os.makedirs(os.path.dirname(STATE_FILE) or ".", exist_ok=True)
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(self.estado, f, indent=2, ensure_ascii=False, default=str)

    def _inicializar_db(self):
        """Cria tabela de histórico de checks se não existir."""
        try:
            import sqlite3
            os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
            conn = sqlite3.connect(self.db_path)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS checks_fontes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fonte TEXT NOT NULL,
                    disponivel INTEGER NOT NULL,
                    tempo_resposta_ms REAL,
                    http_status INTEGER,
                    mensagem_erro TEXT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_checks_fonte_ts
                ON checks_fontes(fonte, timestamp)
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning("Erro ao inicializar DB de monitoramento: %s", e)

    def _registrar_check(self, fonte: str, status: StatusFonte):
        """Registra um check no banco de dados."""
        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            conn.execute("""
                INSERT INTO checks_fontes (fonte, disponivel, tempo_resposta_ms, http_status, mensagem_erro)
                VALUES (?, ?, ?, ?, ?)
            """, (fonte, 1 if status.disponivel else 0, status.tempo_resposta_ms,
                  status.http_status, status.mensagem_erro))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.debug("Erro ao registrar check: %s", e)

    def _calcular_uptime(self, fonte: str, horas: int = 24) -> float:
        """Calcula uptime percentual nas últimas N horas."""
        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            desde = (datetime.now() - timedelta(hours=horas)).isoformat()
            cursor = conn.execute("""
                SELECT COUNT(*) as total, SUM(disponivel) as sucessos
                FROM checks_fontes
                WHERE fonte = ? AND timestamp > ?
            """, (fonte, desde))
            row = cursor.fetchone()
            conn.close()
            if row and row[0] > 0:
                return round((row[1] / row[0]) * 100, 1)
        except Exception:
            pass
        return 100.0 if self.estado.get(fonte, {}).get("disponivel", True) else 0.0

    def _contar_checks(self, fonte: str) -> tuple:
        """Retorna (total_checks, total_falhas) para uma fonte."""
        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute("""
                SELECT COUNT(*) as total, SUM(CASE WHEN disponivel = 0 THEN 1 ELSE 0 END) as falhas
                FROM checks_fontes WHERE fonte = ?
            """, (fonte,))
            row = cursor.fetchone()
            conn.close()
            if row:
                return row[0], row[1] or 0
        except Exception:
            pass
        return 0, 0

    def verificar_fonte(self, nome: str, config: Dict) -> StatusFonte:
        """
        Verifica a saúde de uma fonte específica.

        Args:
            nome: Nome da fonte
            config: Configuração com url, timeout, headers, params

        Returns:
            StatusFonte com métricas da verificação
        """
        url = config["url"]
        timeout = config.get("timeout", 30)
        headers = config.get("headers", {})
        params = config.get("params", {})

        inicio = time.time()
        disponivel = False
        http_status = None
        mensagem_erro = ""
        mudanca_detectada = False

        try:
            resp = self.sessao.get(
                url,
                headers=headers,
                params=params,
                timeout=timeout,
                allow_redirects=True,
            )
            http_status = resp.status_code
            tempo_ms = round((time.time() - inicio) * 1000, 1)

            if http_status == 200:
                disponivel = True
                # Verificar se resposta mudou de formato (possível mudança de API)
                try:
                    dados = resp.json()
                    estrutura_atual = self._extrair_estrutura(dados)
                    estrutura_anterior = self.estado.get(nome, {}).get("estrutura_resposta")
                    if estrutura_anterior and estrutura_atual != estrutura_anterior:
                        mudanca_detectada = True
                        logger.warning("Mudança de estrutura detectada em %s", nome)
                    self.estado.setdefault(nome, {})["estrutura_resposta"] = estrutura_atual
                except Exception:
                    pass
            elif http_status in (301, 302, 307, 308):
                mudanca_detectada = True
                mensagem_erro = f"Redirecionamento detectado ({http_status}): {resp.headers.get('Location', 'desconhecido')}"
                logger.warning("[%s] %s", nome, mensagem_erro)
            elif http_status == 404:
                mudanca_detectada = True
                mensagem_erro = f"Endpoint não encontrado (404) - possível mudança de URL"
            elif http_status == 401:
                mensagem_erro = f"Autenticação necessária (401)"
            elif http_status == 403:
                mensagem_erro = f"Acesso negado (403) - possível bloqueio"
            elif http_status == 429:
                mensagem_erro = f"Rate limit atingido (429)"
            elif http_status >= 500:
                mensagem_erro = f"Erro do servidor ({http_status})"
            else:
                mensagem_erro = f"Status HTTP inesperado: {http_status}"

        except requests.Timeout:
            tempo_ms = round((time.time() - inicio) * 1000, 1)
            mensagem_erro = f"Timeout após {timeout}s"
        except requests.ConnectionError:
            tempo_ms = round((time.time() - inicio) * 1000, 1)
            mensagem_erro = "Erro de conexão - API possivelmente indisponível"
        except Exception as e:
            tempo_ms = round((time.time() - inicio) * 1000, 1)
            mensagem_erro = f"Erro inesperado: {str(e)}"

        # Atualizar estado
        estado_fonte = self.estado.setdefault(nome, {})
        if disponivel:
            estado_fonte["ultimo_sucesso"] = datetime.now().isoformat()
            estado_fonte["falhas_consecutivas"] = 0
        else:
            estado_fonte["ultima_falha"] = datetime.now().isoformat()
            estado_fonte["falhas_consecutivas"] = estado_fonte.get("falhas_consecutivas", 0) + 1
        estado_fonte["disponivel"] = disponivel
        estado_fonte["http_status"] = http_status

        total_checks, total_falhas = self._contar_checks(nome)
        uptime = self._calcular_uptime(nome)

        status = StatusFonte(
            nome=nome,
            url=url,
            disponivel=disponivel,
            tempo_resposta_ms=tempo_ms,
            http_status=http_status,
            ultimo_sucesso=estado_fonte.get("ultimo_sucesso"),
            ultima_falha=estado_fonte.get("ultima_falha"),
            mensagem_erro=mensagem_erro,
            uptime_24h=uptime,
            total_checks=total_checks + 1,
            total_falhas=total_falhas + (0 if disponivel else 1),
            mudanca_detectada=mudanca_detectada,
            cache_disponivel=self._cache_disponivel(nome),
        )

        self._registrar_check(nome, status)
        return status

    def _extrair_estrutura(self, dados: Any) -> str:
        """Extrai uma assinatura da estrutura da resposta para detectar mudanças."""
        if isinstance(dados, dict):
            return ",".join(sorted(dados.keys()))
        elif isinstance(dados, list) and dados:
            return f"list[{self._extrair_estrutura(dados[0])}]"
        return type(dados).__name__

    def _cache_disponivel(self, nome: str) -> bool:
        """Verifica se existe cache local para a fonte."""
        cache_paths = {
            "BEC-SP": os.path.join("dados", "licitacoes_estaduais.csv"),
            "CELIC-RS": os.path.join("dados", "licitacoes_estaduais.csv"),
            "Licitações-e": os.path.join("dados", "licitacoes_estaduais.csv"),
            "Querido Diário": os.path.join("dados", "querido_diario.csv"),
            "Portal da Transparência": os.path.join("dados", "portal_transparencia.csv"),
            "Compras.gov.br": os.path.join("dados", "compras_gov.csv"),
        }
        caminho = cache_paths.get(nome)
        if caminho and os.path.exists(caminho):
            # Verificar se cache tem menos de 7 dias
            idade = datetime.now() - datetime.fromtimestamp(os.path.getmtime(caminho))
            return idade.days < 7
        return False

    def verificar_todas(self) -> Dict[str, StatusFonte]:
        """
        Executa health check em todas as fontes configuradas.

        Returns:
            Dicionário {nome_fonte: StatusFonte}
        """
        logger.info("Iniciando verificação de %d fontes...", len(self.FONTES))
        resultados = {}

        for nome, config in self.FONTES.items():
            logger.info("Verificando %s...", nome)
            status = self.verificar_fonte(nome, config)
            resultados[nome] = status

            nivel = "info" if status.disponivel else "warning"
            if status.mudanca_detectada:
                nivel = "warning"

            getattr(logger, nivel)(
                "[%s] %s | %dms | HTTP %s | Uptime 24h: %.1f%% | Cache: %s",
                nome,
                "OK" if status.disponivel else "FALHA",
                status.tempo_resposta_ms,
                status.http_status or "N/A",
                status.uptime_24h,
                "sim" if status.cache_disponivel else "não",
            )

            if status.mensagem_erro and not status.disponivel:
                logger.warning("[%s] Erro: %s", nome, status.mensagem_erro)

        self._salvar_estado()
        return resultados

    def fontes_com_problemas(self, resultados: Dict[str, StatusFonte]) -> List[StatusFonte]:
        """Retorna apenas fontes com problemas (indisponíveis ou mudança detectada)."""
        problemas = []
        for status in resultados.values():
            if not status.disponivel or status.mudanca_detectada:
                problemas.append(status)
        return problemas

    def enviar_alertas_problemas(self, resultados: Dict[str, StatusFonte]) -> bool:
        """
        Envia alertas para canais configurados quando há problemas.
        Integra com o sistema de notificações existente (Slack/Discord).
        """
        problemas = self.fontes_com_problemas(resultados)
        if not problemas:
            logger.info("Todas as fontes estão operacionais. Nenhum alerta necessário.")
            return True

        # Tentar enviar via notificador multi-canal
        try:
            from notificacoes import NotificadorMultiCanal
            notificador = NotificadorMultiCanal()

            mensagem = "🚨 *Alerta de Fontes de Licitações*\n\n"
            for p in problemas:
                emoji = "🔴" if not p.disponivel else "🟡"
                mensagem += f"{emoji} *{p.nome}*\n"
                mensagem += f"   URL: `{p.url}`\n"
                if not p.disponivel:
                    mensagem += f"   Status: Indisponível (HTTP {p.http_status or 'N/A'})\n"
                    mensagem += f"   Erro: {p.mensagem_erro}\n"
                    if p.cache_disponivel:
                        mensagem += f"   💾 Cache local disponível\n"
                if p.mudanca_detectada:
                    mensagem += f"   ⚠️ Mudança de API detectada\n"
                mensagem += f"   Uptime 24h: {p.uptime_24h}%\n\n"

            notificador.enviar_todos(mensagem)
            logger.info("Alertas de problemas enviados para %d canais", len(notificador.canais))
            return True

        except Exception as e:
            logger.error("Erro ao enviar alertas de problemas: %s", e)
            return False

    def gerar_relatorio(self, resultados: Dict[str, StatusFonte]) -> str:
        """Gera relatório em formato Markdown da saúde das fontes."""
        linhas = [
            "# 📊 Relatório de Saúde das Fontes",
            f"\n**Gerado em:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
            f"**Total de fontes:** {len(resultados)}\n",
            "| Fonte | Status | HTTP | Tempo | Uptime 24h | Cache |",
            "|-------|--------|------|-------|------------|-------|",
        ]

        for nome, status in sorted(resultados.items()):
            icone = "✅" if status.disponivel else "❌"
            if status.mudanca_detectada:
                icone = "⚠️"
            http = status.http_status or "N/A"
            tempo = f"{status.tempo_resposta_ms:.0f}ms"
            cache = "Sim" if status.cache_disponivel else "Não"
            linhas.append(f"| {nome} | {icone} | {http} | {tempo} | {status.uptime_24h}% | {cache} |")

        problemas = self.fontes_com_problemas(resultados)
        if problemas:
            linhas.append("\n## ⚠️ Problemas Detectados\n")
            for p in problemas:
                linhas.append(f"### {p.nome}")
                linhas.append(f"- **Status:** {'Indisponível' if not p.disponivel else 'Mudança detectada'}")
                linhas.append(f"- **URL:** {p.url}")
                linhas.append(f"- **Erro:** {p.mensagem_erro or 'N/A'}")
                linhas.append(f"- **Último sucesso:** {p.ultimo_sucesso or 'N/A'}")
                linhas.append(f"- **Cache disponível:** {'Sim' if p.cache_disponivel else 'Não'}")
                linhas.append("")

        return "\n".join(linhas)

    def exportar_relatorio(self, resultados: Dict[str, StatusFonte], caminho: str = "dados/relatorio_fontes.md"):
        """Exporta relatório para arquivo Markdown."""
        os.makedirs(os.path.dirname(caminho) or ".", exist_ok=True)
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(self.gerar_relatorio(resultados))
        logger.info("Relatório exportado: %s", caminho)


def executar_monitoramento():
    """Função standalone para execução via cron/agendador."""
    monitor = MonitorFontes()
    resultados = monitor.verificar_todas()
    monitor.enviar_alertas_problemas(resultados)
    monitor.exportar_relatorio(resultados)

    # Resumo
    total = len(resultados)
    ok = sum(1 for s in resultados.values() if s.disponivel and not s.mudanca_detectada)
    problemas = total - ok

    logger.info("=" * 50)
    logger.info("MONITORAMENTO CONCLUÍDO")
    logger.info("Total: %d | OK: %d | Problemas: %d", total, ok, problemas)
    logger.info("=" * 50)

    return resultados


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    executar_monitoramento()
