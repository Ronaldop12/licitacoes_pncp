"""
Histórico versionado de coletas.
Armazena snapshots de cada execução para análise de tendências.
"""

import sqlite3
import json
import os
import logging
from contextlib import closing
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd

logger = logging.getLogger(__name__)

DB_PATH = os.path.join("dados", "historico.db")


class HistoricoDB:
    """Gerencia o histórico versionado de coletas."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        diretorio = os.path.dirname(db_path)
        if diretorio and not os.path.exists(diretorio):
            os.makedirs(diretorio)
        self._criar_tabelas()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _criar_tabelas(self):
        with closing(self._get_connection()) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS coletas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data_execucao TIMESTAMP NOT NULL,
                    fonte TEXT NOT NULL DEFAULT 'PNCP',
                    total_verificadas INTEGER DEFAULT 0,
                    total_ti INTEGER DEFAULT 0,
                    total_duplicadas INTEGER DEFAULT 0,
                    valor_total REAL DEFAULT 0,
                    valor_medio REAL DEFAULT 0,
                    total_orgaos INTEGER DEFAULT 0,
                    total_ufs INTEGER DEFAULT 0,
                    modalidades TEXT DEFAULT '[]',
                    resumo TEXT DEFAULT '{}'
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS snapshots_uf (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    coleta_id INTEGER NOT NULL,
                    uf TEXT NOT NULL,
                    quantidade INTEGER DEFAULT 0,
                    valor_total REAL DEFAULT 0,
                    FOREIGN KEY (coleta_id) REFERENCES coletas(id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS snapshots_orgao (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    coleta_id INTEGER NOT NULL,
                    orgao TEXT NOT NULL,
                    quantidade INTEGER DEFAULT 0,
                    valor_total REAL DEFAULT 0,
                    FOREIGN KEY (coleta_id) REFERENCES coletas(id)
                )
            """)

            cursor.execute("CREATE INDEX IF NOT EXISTS idx_coletas_data ON coletas(data_execucao)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_snap_uf_coleta ON snapshots_uf(coleta_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_snap_orgao_coleta ON snapshots_orgao(coleta_id)")

            conn.commit()

    def registrar_coleta(self, df: pd.DataFrame, fonte: str = "PNCP",
                         total_verificadas: int = 0, total_duplicadas: int = 0) -> int:
        """Registra uma coleta e seus snapshots por UF e órgão."""
        with closing(self._get_connection()) as conn:
            cursor = conn.cursor()

            total_ti = len(df)
            valor_total = float(df['valor_estimado'].sum()) if 'valor_estimado' in df.columns else 0
            valor_medio = float(df['valor_estimado'].mean()) if 'valor_estimado' in df.columns and total_ti > 0 else 0
            total_orgaos = int(df['orgao'].nunique()) if 'orgao' in df.columns else 0
            total_ufs = int(df['uf'].nunique()) if 'uf' in df.columns else 0
            modalidades = df['modalidade'].unique().tolist() if 'modalidade' in df.columns else []

            cursor.execute("""
                INSERT INTO coletas 
                (data_execucao, fonte, total_verificadas, total_ti, total_duplicadas,
                 valor_total, valor_medio, total_orgaos, total_ufs, modalidades)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(), fonte, total_verificadas, total_ti,
                total_duplicadas, valor_total, valor_medio, total_orgaos, total_ufs,
                json.dumps([str(m) for m in modalidades], ensure_ascii=False),
            ))
            coleta_id = cursor.lastrowid

            # Snapshots por UF
            if 'uf' in df.columns:
                uf_agg = df.groupby('uf').agg(
                    quantidade=('uf', 'size'),
                    valor_total=('valor_estimado', 'sum')
                ).reset_index()
                for _, row in uf_agg.iterrows():
                    cursor.execute(
                        "INSERT INTO snapshots_uf (coleta_id, uf, quantidade, valor_total) VALUES (?, ?, ?, ?)",
                        (coleta_id, row['uf'], int(row['quantidade']), float(row['valor_total']))
                    )

            # Snapshots por órgão (top 30)
            if 'orgao' in df.columns:
                org_agg = df.groupby('orgao').agg(
                    quantidade=('orgao', 'size'),
                    valor_total=('valor_estimado', 'sum')
                ).reset_index().nlargest(30, 'quantidade')
                for _, row in org_agg.iterrows():
                    cursor.execute(
                        "INSERT INTO snapshots_orgao (coleta_id, orgao, quantidade, valor_total) VALUES (?, ?, ?, ?)",
                        (coleta_id, row['orgao'], int(row['quantidade']), float(row['valor_total']))
                    )

            conn.commit()
            logger.info("Coleta #%d registrada: %d licitações TI", coleta_id, total_ti)
            return coleta_id

    def listar_coletas(self, limite: int = 50) -> List[Dict]:
        with closing(self._get_connection()) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM coletas ORDER BY data_execucao DESC LIMIT ?", (limite,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def obter_evolucao_ti(self) -> pd.DataFrame:
        """Retorna série temporal do total de licitações TI por coleta."""
        with closing(self._get_connection()) as conn:
            df = pd.read_sql_query(
                "SELECT data_execucao, total_ti, valor_total, total_orgaos, total_ufs FROM coletas ORDER BY data_execucao",
                conn
            )
        if not df.empty:
            df['data_execucao'] = pd.to_datetime(df['data_execucao'])
        return df

    def obter_evolucao_uf(self, uf: str) -> pd.DataFrame:
        """Retorna evolução temporal de uma UF específica."""
        with closing(self._get_connection()) as conn:
            df = pd.read_sql_query("""
                SELECT c.data_execucao, s.quantidade, s.valor_total
                FROM snapshots_uf s
                JOIN coletas c ON c.id = s.coleta_id
                WHERE s.uf = ?
                ORDER BY c.data_execucao
            """, conn, params=(uf,))
        if not df.empty:
            df['data_execucao'] = pd.to_datetime(df['data_execucao'])
        return df

    def obter_ultima_coleta(self) -> Optional[Dict]:
        coletas = self.listar_coletas(limite=1)
        return coletas[0] if coletas else None
