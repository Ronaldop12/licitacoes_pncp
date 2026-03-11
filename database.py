"""
Abstração de banco de dados com suporte a PostgreSQL e SQLite.
Usa PostgreSQL se DATABASE_URL estiver configurado, caso contrário SQLite.
Fornece interface unificada para todos os módulos do sistema.
"""

import os
import logging
import sqlite3
from contextlib import contextmanager
from typing import Optional

logger = logging.getLogger(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL", "")

_pg_disponivel = False
try:
    import psycopg2
    import psycopg2.extras
    _pg_disponivel = True
except ImportError:
    pass


def usar_postgres() -> bool:
    """Retorna True se PostgreSQL está configurado e disponível."""
    return bool(DATABASE_URL) and _pg_disponivel


class DatabaseBackend:
    """
    Backend de banco de dados com suporte a PostgreSQL e SQLite.
    Adapta automaticamente a sintaxe SQL entre os dois.
    """

    def __init__(self, sqlite_path: str, schema_sqlite: str = "", schema_pg: str = ""):
        """
        Args:
            sqlite_path: Caminho para o arquivo SQLite (fallback).
            schema_sqlite: SQL de criação de tabelas (sintaxe SQLite).
            schema_pg: SQL de criação de tabelas (sintaxe PostgreSQL).
                       Se vazio, converte automaticamente do SQLite.
        """
        self.sqlite_path = sqlite_path
        self._schema_sqlite = schema_sqlite
        self._schema_pg = schema_pg or self._converter_schema(schema_sqlite)
        self._usar_pg = usar_postgres()

        if not self._usar_pg:
            d = os.path.dirname(sqlite_path)
            if d and not os.path.exists(d):
                os.makedirs(d)

        self._inicializar_schema()

    @staticmethod
    def _converter_schema(sql_sqlite: str) -> str:
        """Converte schema SQLite para PostgreSQL."""
        if not sql_sqlite:
            return ""
        pg = sql_sqlite
        pg = pg.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
        pg = pg.replace("TIMESTAMP", "TIMESTAMPTZ")
        pg = pg.replace("CREATE INDEX IF NOT EXISTS", "CREATE INDEX IF NOT EXISTS")
        return pg

    def _inicializar_schema(self):
        """Cria tabelas se não existirem."""
        schema = self._schema_pg if self._usar_pg else self._schema_sqlite
        if not schema:
            return
        with self.connection() as conn:
            cursor = conn.cursor()
            for stmt in schema.split(";"):
                stmt = stmt.strip()
                if stmt:
                    try:
                        cursor.execute(stmt)
                    except Exception as e:
                        logger.debug("Schema stmt ignorado: %s", e)
            conn.commit()

    @contextmanager
    def connection(self):
        """Context manager que retorna uma conexão ao banco ativo."""
        if self._usar_pg:
            conn = psycopg2.connect(DATABASE_URL)
            try:
                yield conn
            finally:
                conn.close()
        else:
            conn = sqlite3.connect(self.sqlite_path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            try:
                yield conn
            finally:
                conn.close()

    def execute(self, sql: str, params=None):
        """Executa SQL e retorna cursor."""
        sql = self._adaptar_sql(sql)
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params or ())
            conn.commit()
            return cursor

    def query(self, sql: str, params=None) -> list:
        """Executa SELECT e retorna lista de dicts."""
        sql = self._adaptar_sql(sql)
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params or ())
            if self._usar_pg:
                colunas = [desc[0] for desc in cursor.description] if cursor.description else []
                return [dict(zip(colunas, row)) for row in cursor.fetchall()]
            else:
                rows = cursor.fetchall()
                return [dict(r) for r in rows]

    def query_one(self, sql: str, params=None) -> Optional[dict]:
        """Executa SELECT e retorna um único resultado."""
        rows = self.query(sql, params)
        return rows[0] if rows else None

    def query_scalar(self, sql: str, params=None):
        """Executa SELECT e retorna um único valor escalar."""
        sql = self._adaptar_sql(sql)
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params or ())
            row = cursor.fetchone()
            return row[0] if row else None

    def _adaptar_sql(self, sql: str) -> str:
        """Adapta SQL genérico para o backend ativo."""
        if self._usar_pg:
            # SQLite usa ? para placeholders, Postgres usa %s
            sql = sql.replace("?", "%s")
            # datetime SQLite → Postgres
            sql = sql.replace("datetime('now'", "NOW(")
            sql = sql.replace("datetime('now', '-1 day')", "NOW() - INTERVAL '1 day'")
        return sql

    @property
    def backend_nome(self) -> str:
        return "postgresql" if self._usar_pg else "sqlite"

    def info(self) -> dict:
        """Retorna informações sobre o backend ativo."""
        if self._usar_pg:
            return {
                "backend": "postgresql",
                "url": DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else "configurado",
            }
        return {
            "backend": "sqlite",
            "caminho": self.sqlite_path,
            "tamanho_bytes": os.path.getsize(self.sqlite_path) if os.path.exists(self.sqlite_path) else 0,
        }
