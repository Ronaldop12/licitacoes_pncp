"""
Acompanhamento de fases / mudanças de status de licitações.
Detecta quando o status muda entre coletas e registra o histórico.
"""

import sqlite3
import os
import logging
from contextlib import closing
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd

logger = logging.getLogger(__name__)

DB_PATH = os.path.join("dados", "fases.db")


class FasesDB:
    """Rastreia mudanças de status/fase das licitações ao longo do tempo."""

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

            # Último status conhecido por edital
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS status_atual (
                    numero_edital TEXT PRIMARY KEY,
                    orgao TEXT DEFAULT '',
                    objeto TEXT DEFAULT '',
                    uf TEXT DEFAULT '',
                    status TEXT NOT NULL,
                    atualizado_em TIMESTAMP NOT NULL
                )
            """)

            # Histórico de mudanças de status
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mudancas_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero_edital TEXT NOT NULL,
                    orgao TEXT DEFAULT '',
                    status_anterior TEXT NOT NULL,
                    status_novo TEXT NOT NULL,
                    detectado_em TIMESTAMP NOT NULL
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_mudancas_edital 
                ON mudancas_status(numero_edital)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_mudancas_data 
                ON mudancas_status(detectado_em)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_status_atual_uf 
                ON status_atual(uf)
            """)

            conn.commit()

    def processar_coleta(self, df: pd.DataFrame) -> List[Dict]:
        """
        Compara status atual com coleta nova e registra mudanças.

        Args:
            df: DataFrame com dados da coleta (requer numero_edital e status).

        Returns:
            Lista de mudanças detectadas.
        """
        if df.empty or 'numero_edital' not in df.columns or 'status' not in df.columns:
            return []

        conn = self._get_connection()
        cursor = conn.cursor()
        agora = datetime.now().isoformat()
        mudancas = []

        for _, row in df.iterrows():
            edital = str(row['numero_edital'])
            novo_status = str(row.get('status', 'N/A'))
            orgao = str(row.get('orgao', ''))
            objeto = str(row.get('objeto', ''))[:500]
            uf = str(row.get('uf', ''))

            if not edital or edital == 'N/A' or not novo_status or novo_status == 'N/A':
                continue

            cursor.execute(
                "SELECT status FROM status_atual WHERE numero_edital = ?",
                (edital,)
            )
            existente = cursor.fetchone()

            if existente:
                status_anterior = existente['status']
                if status_anterior != novo_status:
                    cursor.execute("""
                        INSERT INTO mudancas_status 
                        (numero_edital, orgao, status_anterior, status_novo, detectado_em)
                        VALUES (?, ?, ?, ?, ?)
                    """, (edital, orgao, status_anterior, novo_status, agora))

                    cursor.execute("""
                        UPDATE status_atual 
                        SET status = ?, atualizado_em = ?, orgao = ?, objeto = ?, uf = ?
                        WHERE numero_edital = ?
                    """, (novo_status, agora, orgao, objeto, uf, edital))

                    mudancas.append({
                        "numero_edital": edital,
                        "orgao": orgao,
                        "status_anterior": status_anterior,
                        "status_novo": novo_status,
                        "detectado_em": agora,
                    })
            else:
                cursor.execute("""
                    INSERT INTO status_atual 
                    (numero_edital, orgao, objeto, uf, status, atualizado_em)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (edital, orgao, objeto, uf, novo_status, agora))

        conn.commit()
        conn.close()

        if mudancas:
            logger.info("Detectadas %d mudanças de status", len(mudancas))
        return mudancas

    def listar_mudancas(self, limite: int = 100, uf: Optional[str] = None) -> List[Dict]:
        """Lista mudanças de status recentes."""
        with closing(self._get_connection()) as conn:
            cursor = conn.cursor()
            if uf:
                cursor.execute("""
                    SELECT m.*, s.uf, s.objeto
                    FROM mudancas_status m
                    LEFT JOIN status_atual s ON m.numero_edital = s.numero_edital
                    WHERE s.uf = ?
                    ORDER BY m.detectado_em DESC LIMIT ?
                """, (uf, limite))
            else:
                cursor.execute("""
                    SELECT m.*, s.uf, s.objeto
                    FROM mudancas_status m
                    LEFT JOIN status_atual s ON m.numero_edital = s.numero_edital
                    ORDER BY m.detectado_em DESC LIMIT ?
                """, (limite,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def obter_historico_edital(self, numero_edital: str) -> List[Dict]:
        """Retorna todo o histórico de mudanças de um edital específico."""
        with closing(self._get_connection()) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM mudancas_status 
                WHERE numero_edital = ? 
                ORDER BY detectado_em ASC
            """, (numero_edital,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def contar_mudancas(self) -> Dict:
        """Retorna estatísticas gerais de mudanças."""
        with closing(self._get_connection()) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as total FROM mudancas_status")
            total = cursor.fetchone()['total']
            cursor.execute("SELECT COUNT(DISTINCT numero_edital) as editais FROM mudancas_status")
            editais = cursor.fetchone()['editais']
            cursor.execute("SELECT COUNT(*) as total FROM status_atual")
            rastreados = cursor.fetchone()['total']
            return {"total_mudancas": total, "editais_com_mudanca": editais, "total_rastreados": rastreados}
