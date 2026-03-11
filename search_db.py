"""
Busca Full-Text com SQLite FTS5.
Indexa licitações para busca rápida e ranking de relevância.
"""

import os
import re
import sqlite3
import logging
from contextlib import closing
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

DB_PATH = os.path.join("dados", "search.db")


class SearchDB:
    """Motor de busca full-text usando SQLite FTS5."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        d = os.path.dirname(db_path)
        if d and not os.path.exists(d):
            os.makedirs(d)
        self._criar_tabelas()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _criar_tabelas(self):
        with closing(self._conn()) as conn:
            # Tabela FTS5 para busca textual
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS licitacoes_fts USING fts5(
                    numero_edital,
                    orgao,
                    objeto,
                    uf,
                    modalidade,
                    valor_estimado UNINDEXED,
                    data_publicacao UNINDEXED,
                    link_edital UNINDEXED,
                    tokenize='unicode61 remove_diacritics 2'
                )
            """)
            # Tabela de controle de indexação
            conn.execute("""
                CREATE TABLE IF NOT EXISTS indexacao_meta (
                    id INTEGER PRIMARY KEY,
                    total_indexados INTEGER DEFAULT 0,
                    ultima_indexacao TEXT,
                    hash_csv TEXT DEFAULT ''
                )
            """)
            conn.commit()

    def indexar_csv(self, csv_path: str, forcar: bool = False) -> Dict:
        """
        Indexa licitações do CSV na tabela FTS5.
        Usa hash do arquivo para evitar re-indexação desnecessária.
        """
        import hashlib
        import pandas as pd

        if not os.path.exists(csv_path):
            return {"ok": False, "erro": "CSV não encontrado"}

        file_hash = hashlib.md5(open(csv_path, "rb").read()).hexdigest()

        # Verificar se já indexou este CSV
        if not forcar:
            with closing(self._conn()) as conn:
                row = conn.execute(
                    "SELECT hash_csv FROM indexacao_meta WHERE id = 1"
                ).fetchone()
                if row and row["hash_csv"] == file_hash:
                    return {"ok": True, "mensagem": "Índice já atualizado", "reindexado": False}

        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            return {"ok": False, "erro": f"Erro ao ler CSV: {e}"}

        colunas_necessarias = {"numero_edital", "orgao", "objeto"}
        if not colunas_necessarias.issubset(set(df.columns)):
            return {"ok": False, "erro": f"Colunas obrigatórias ausentes: {colunas_necessarias - set(df.columns)}"}

        with closing(self._conn()) as conn:
            # Limpar índice anterior
            conn.execute("DELETE FROM licitacoes_fts")

            contagem = 0
            for _, row in df.iterrows():
                conn.execute(
                    "INSERT INTO licitacoes_fts (numero_edital, orgao, objeto, uf, modalidade, valor_estimado, data_publicacao, link_edital) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        str(row.get("numero_edital", "")),
                        str(row.get("orgao", "")),
                        str(row.get("objeto", "")),
                        str(row.get("uf", "")),
                        str(row.get("modalidade", "")),
                        str(row.get("valor_estimado", "")),
                        str(row.get("data_publicacao", "")),
                        str(row.get("link_edital", "")),
                    ),
                )
                contagem += 1

            # Atualizar metadados
            conn.execute("DELETE FROM indexacao_meta")
            conn.execute(
                "INSERT INTO indexacao_meta (id, total_indexados, ultima_indexacao, hash_csv) VALUES (1, ?, ?, ?)",
                (contagem, datetime.now().isoformat(), file_hash),
            )
            conn.commit()

        logger.info("FTS5: %d licitações indexadas", contagem)
        return {"ok": True, "total_indexados": contagem, "reindexado": True}

    def buscar(
        self,
        consulta: str,
        limite: int = 50,
        uf: Optional[str] = None,
    ) -> List[Dict]:
        """
        Busca full-text com ranking de relevância.

        Args:
            consulta: Termos de busca (suporta operadores FTS5: AND, OR, NOT, "frase exata")
            limite: Máximo de resultados
            uf: Filtrar por UF após busca

        Returns:
            Lista de licitações ordenadas por relevância (rank).
        """
        if not consulta or not consulta.strip():
            return []

        # Sanitizar consulta: manter apenas caracteres seguros para FTS5
        consulta_limpa = re.sub(r'[^\w\s"*\-]', ' ', consulta, flags=re.UNICODE).strip()
        if not consulta_limpa:
            return []

        try:
            with closing(self._conn()) as conn:
                if uf:
                    rows = conn.execute(
                        """
                        SELECT *, rank FROM licitacoes_fts
                        WHERE licitacoes_fts MATCH ? AND uf = ?
                        ORDER BY rank
                        LIMIT ?
                        """,
                        (consulta_limpa, uf.upper(), limite),
                    ).fetchall()
                else:
                    rows = conn.execute(
                        """
                        SELECT *, rank FROM licitacoes_fts
                        WHERE licitacoes_fts MATCH ?
                        ORDER BY rank
                        LIMIT ?
                        """,
                        (consulta_limpa, limite),
                    ).fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            logger.warning("Erro na busca FTS5: %s (consulta: %s)", e, consulta_limpa)
            return []

    def sugerir(self, prefixo: str, limite: int = 10) -> List[str]:
        """
        Auto-complete baseado em prefixo (busca com wildcard *).

        Args:
            prefixo: Início do termo para sugestão.
            limite: Máximo de sugestões.

        Returns:
            Lista de objetos que contêm o prefixo.
        """
        if not prefixo or len(prefixo) < 2:
            return []

        prefixo_limpo = re.sub(r'[^\w]', '', prefixo, flags=re.UNICODE)
        if not prefixo_limpo:
            return []

        try:
            with closing(self._conn()) as conn:
                rows = conn.execute(
                    """
                    SELECT DISTINCT objeto FROM licitacoes_fts
                    WHERE objeto MATCH ?
                    ORDER BY rank
                    LIMIT ?
                    """,
                    (f"{prefixo_limpo}*", limite),
                ).fetchall()
            return [r["objeto"] for r in rows]
        except Exception as e:
            logger.warning("Erro na sugestão FTS5: %s", e)
            return []

    def info(self) -> Dict:
        """Retorna informações sobre o índice."""
        with closing(self._conn()) as conn:
            row = conn.execute(
                "SELECT * FROM indexacao_meta WHERE id = 1"
            ).fetchone()
            if row:
                return dict(row)
        return {"total_indexados": 0, "ultima_indexacao": None}
