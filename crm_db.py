"""
CRM e Pipeline de Propostas para Licitações de TI.
Gerencia o fluxo comercial: prospecção → análise → proposta → resultado.
"""

import os
import sqlite3
import json
import logging
from contextlib import closing
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

DB_PATH = os.path.join("dados", "crm.db")

# Estágios do pipeline comercial
ESTAGIOS = [
    "prospeccao",      # Licitação identificada
    "analise",         # Em análise técnica/financeira
    "decisao",         # Decidindo se vai participar
    "elaborando",      # Elaborando proposta
    "enviada",         # Proposta enviada
    "aguardando",      # Aguardando resultado
    "vencida",         # Ganhou a licitação
    "perdida",         # Perdeu a licitação
    "desistencia",     # Decidiu não participar
]

ESTAGIOS_ATIVOS = {"prospeccao", "analise", "decisao", "elaborando", "enviada", "aguardando"}
ESTAGIOS_FINAIS = {"vencida", "perdida", "desistencia"}


class CrmDB:
    """Gerencia o pipeline de propostas comerciais."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
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
                CREATE TABLE IF NOT EXISTS propostas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero_edital TEXT NOT NULL,
                    orgao TEXT DEFAULT '',
                    objeto TEXT DEFAULT '',
                    valor_estimado REAL DEFAULT 0,
                    uf TEXT DEFAULT '',
                    estagio TEXT NOT NULL DEFAULT 'prospeccao',
                    responsavel TEXT DEFAULT '',
                    valor_proposta REAL DEFAULT 0,
                    margem_percentual REAL DEFAULT 0,
                    data_limite TEXT DEFAULT '',
                    notas TEXT DEFAULT '',
                    tags TEXT DEFAULT '[]',
                    criado_em TIMESTAMP NOT NULL,
                    atualizado_em TIMESTAMP NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS historico_proposta (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    proposta_id INTEGER NOT NULL,
                    estagio_anterior TEXT DEFAULT '',
                    estagio_novo TEXT NOT NULL,
                    usuario TEXT DEFAULT '',
                    observacao TEXT DEFAULT '',
                    criado_em TIMESTAMP NOT NULL,
                    FOREIGN KEY (proposta_id) REFERENCES propostas(id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tarefas_proposta (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    proposta_id INTEGER NOT NULL,
                    descricao TEXT NOT NULL,
                    responsavel TEXT DEFAULT '',
                    prazo TEXT DEFAULT '',
                    concluida INTEGER DEFAULT 0,
                    criado_em TIMESTAMP NOT NULL,
                    FOREIGN KEY (proposta_id) REFERENCES propostas(id)
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_prop_edital ON propostas(numero_edital)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_prop_estagio ON propostas(estagio)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_hist_proposta ON historico_proposta(proposta_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tarefas_proposta ON tarefas_proposta(proposta_id)")
            conn.commit()

    # ========== CRUD PROPOSTAS ==========

    def criar_proposta(
        self,
        numero_edital: str,
        orgao: str = "",
        objeto: str = "",
        valor_estimado: float = 0,
        uf: str = "",
        responsavel: str = "",
        notas: str = "",
        tags: Optional[List[str]] = None,
    ) -> int:
        """Cria uma nova proposta no pipeline."""
        agora = datetime.now().isoformat()
        with closing(self._conn()) as conn:
            cur = conn.execute("""
                INSERT INTO propostas
                (numero_edital, orgao, objeto, valor_estimado, uf, estagio,
                 responsavel, notas, tags, criado_em, atualizado_em)
                VALUES (?, ?, ?, ?, ?, 'prospeccao', ?, ?, ?, ?, ?)
            """, (
                numero_edital, orgao, objeto[:500], valor_estimado, uf,
                responsavel, notas[:1000], json.dumps(tags or []),
                agora, agora,
            ))
            proposta_id = cur.lastrowid

            # Registrar no histórico
            conn.execute("""
                INSERT INTO historico_proposta
                (proposta_id, estagio_anterior, estagio_novo, usuario, criado_em)
                VALUES (?, '', 'prospeccao', ?, ?)
            """, (proposta_id, responsavel, agora))

            conn.commit()
        logger.info("Proposta #%d criada: %s", proposta_id, numero_edital)
        return proposta_id

    def obter_proposta(self, proposta_id: int) -> Optional[Dict]:
        """Retorna detalhes de uma proposta."""
        with closing(self._conn()) as conn:
            row = conn.execute("SELECT * FROM propostas WHERE id = ?", (proposta_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        d["tags"] = json.loads(d.get("tags", "[]"))
        return d

    def obter_por_edital(self, numero_edital: str) -> Optional[Dict]:
        """Busca proposta pelo número do edital."""
        with closing(self._conn()) as conn:
            row = conn.execute(
                "SELECT * FROM propostas WHERE numero_edital = ?", (numero_edital,)
            ).fetchone()
        if not row:
            return None
        d = dict(row)
        d["tags"] = json.loads(d.get("tags", "[]"))
        return d

    def atualizar_proposta(self, proposta_id: int, **campos) -> bool:
        """Atualiza campos de uma proposta."""
        permitidos = {
            "responsavel", "valor_proposta", "margem_percentual",
            "data_limite", "notas", "tags",
        }
        atualizacoes = {k: v for k, v in campos.items() if k in permitidos}
        if not atualizacoes:
            return False

        if "tags" in atualizacoes and isinstance(atualizacoes["tags"], list):
            atualizacoes["tags"] = json.dumps(atualizacoes["tags"])

        atualizacoes["atualizado_em"] = datetime.now().isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in atualizacoes)
        valores = list(atualizacoes.values()) + [proposta_id]

        with closing(self._conn()) as conn:
            conn.execute(f"UPDATE propostas SET {set_clause} WHERE id = ?", valores)
            conn.commit()
        return True

    # ========== TRANSIÇÃO DE ESTÁGIOS ==========

    def mover_estagio(
        self, proposta_id: int, novo_estagio: str,
        usuario: str = "", observacao: str = "",
    ) -> bool:
        """Move proposta para novo estágio no pipeline."""
        if novo_estagio not in ESTAGIOS:
            logger.warning("Estágio inválido: %s", novo_estagio)
            return False

        with closing(self._conn()) as conn:
            row = conn.execute(
                "SELECT estagio FROM propostas WHERE id = ?", (proposta_id,)
            ).fetchone()
            if not row:
                return False

            estagio_atual = row["estagio"]
            if estagio_atual in ESTAGIOS_FINAIS:
                logger.warning("Proposta #%d já está em estágio final: %s", proposta_id, estagio_atual)
                return False

            agora = datetime.now().isoformat()
            conn.execute(
                "UPDATE propostas SET estagio = ?, atualizado_em = ? WHERE id = ?",
                (novo_estagio, agora, proposta_id),
            )
            conn.execute("""
                INSERT INTO historico_proposta
                (proposta_id, estagio_anterior, estagio_novo, usuario, observacao, criado_em)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (proposta_id, estagio_atual, novo_estagio, usuario, observacao[:500], agora))
            conn.commit()

        logger.info("Proposta #%d: %s → %s", proposta_id, estagio_atual, novo_estagio)
        return True

    # ========== TAREFAS ==========

    def adicionar_tarefa(
        self, proposta_id: int, descricao: str,
        responsavel: str = "", prazo: str = "",
    ) -> int:
        """Adiciona tarefa a uma proposta."""
        agora = datetime.now().isoformat()
        with closing(self._conn()) as conn:
            cur = conn.execute("""
                INSERT INTO tarefas_proposta
                (proposta_id, descricao, responsavel, prazo, criado_em)
                VALUES (?, ?, ?, ?, ?)
            """, (proposta_id, descricao[:500], responsavel, prazo, agora))
            conn.commit()
            return cur.lastrowid

    def concluir_tarefa(self, tarefa_id: int) -> bool:
        """Marca tarefa como concluída."""
        with closing(self._conn()) as conn:
            conn.execute(
                "UPDATE tarefas_proposta SET concluida = 1 WHERE id = ?", (tarefa_id,)
            )
            conn.commit()
        return True

    def listar_tarefas(self, proposta_id: int) -> List[Dict]:
        """Lista tarefas de uma proposta."""
        with closing(self._conn()) as conn:
            rows = conn.execute(
                "SELECT * FROM tarefas_proposta WHERE proposta_id = ? ORDER BY concluida, prazo",
                (proposta_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    # ========== CONSULTAS E RELATÓRIOS ==========

    def listar_pipeline(self, estagio: Optional[str] = None, limite: int = 100) -> List[Dict]:
        """Lista propostas do pipeline, opcionalmente filtradas por estágio."""
        with closing(self._conn()) as conn:
            if estagio and estagio in ESTAGIOS:
                rows = conn.execute(
                    "SELECT * FROM propostas WHERE estagio = ? ORDER BY atualizado_em DESC LIMIT ?",
                    (estagio, limite),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM propostas ORDER BY atualizado_em DESC LIMIT ?",
                    (limite,),
                ).fetchall()
        resultado = []
        for r in rows:
            d = dict(r)
            d["tags"] = json.loads(d.get("tags", "[]"))
            resultado.append(d)
        return resultado

    def pipeline_resumo(self) -> Dict:
        """Retorna contagem de propostas por estágio."""
        with closing(self._conn()) as conn:
            rows = conn.execute(
                "SELECT estagio, COUNT(*) as qtd FROM propostas GROUP BY estagio"
            ).fetchall()
            total_valor = conn.execute(
                "SELECT COALESCE(SUM(valor_proposta), 0) FROM propostas WHERE estagio IN ('elaborando', 'enviada', 'aguardando')"
            ).fetchone()[0]
            total_ganho = conn.execute(
                "SELECT COALESCE(SUM(valor_proposta), 0) FROM propostas WHERE estagio = 'vencida'"
            ).fetchone()[0]
        por_estagio = {r["estagio"]: r["qtd"] for r in rows}
        total_ativas = sum(por_estagio.get(e, 0) for e in ESTAGIOS_ATIVOS)
        return {
            "por_estagio": por_estagio,
            "total_ativas": total_ativas,
            "total_propostas": sum(por_estagio.values()),
            "valor_em_andamento": round(total_valor, 2),
            "valor_ganho": round(total_ganho, 2),
        }

    def historico_proposta(self, proposta_id: int) -> List[Dict]:
        """Retorna histórico de movimentações de uma proposta."""
        with closing(self._conn()) as conn:
            rows = conn.execute(
                "SELECT * FROM historico_proposta WHERE proposta_id = ? ORDER BY criado_em",
                (proposta_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    def taxa_conversao(self) -> Dict:
        """Calcula taxa de conversão do pipeline."""
        resumo = self.pipeline_resumo()
        por_estagio = resumo["por_estagio"]
        total = resumo["total_propostas"]
        vencidas = por_estagio.get("vencida", 0)
        finalizadas = vencidas + por_estagio.get("perdida", 0)
        return {
            "total_propostas": total,
            "finalizadas": finalizadas,
            "vencidas": vencidas,
            "taxa_conversao": round((vencidas / finalizadas * 100) if finalizadas > 0 else 0, 1),
            "valor_medio_vencida": round(
                resumo["valor_ganho"] / vencidas if vencidas > 0 else 0, 2
            ),
        }
