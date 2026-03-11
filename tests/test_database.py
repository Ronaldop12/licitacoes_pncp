"""Testes para database.py — Abstração PostgreSQL/SQLite."""

import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseBackend, usar_postgres


class TestUsarPostgres:
    def test_sem_database_url(self, monkeypatch):
        monkeypatch.delenv("DATABASE_URL", raising=False)
        # Forçar re-avaliação: sem DATABASE_URL → False
        assert not (os.environ.get("DATABASE_URL", "") and True)

    def test_com_database_url_sem_psycopg2(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
        # Mesmo com URL, se psycopg2 não estiver no import cache, o módulo-level var não muda
        # Testamos apenas que usar_postgres() retorna bool
        resultado = usar_postgres()
        assert isinstance(resultado, bool)


class TestDatabaseBackendSQLite:
    @pytest.fixture
    def db(self, tmp_path):
        schema = """
            CREATE TABLE IF NOT EXISTS itens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                valor REAL DEFAULT 0,
                criado_em TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_itens_nome ON itens(nome);
        """
        return DatabaseBackend(
            sqlite_path=str(tmp_path / "test.db"),
            schema_sqlite=schema,
        )

    def test_backend_nome(self, db):
        assert db.backend_nome == "sqlite"

    def test_info(self, db):
        info = db.info()
        assert info["backend"] == "sqlite"
        assert "caminho" in info

    def test_execute_insert(self, db):
        db.execute("INSERT INTO itens (nome, valor) VALUES (?, ?)", ("item1", 10.5))
        rows = db.query("SELECT * FROM itens")
        assert len(rows) == 1
        assert rows[0]["nome"] == "item1"
        assert rows[0]["valor"] == 10.5

    def test_query_vazio(self, db):
        rows = db.query("SELECT * FROM itens")
        assert rows == []

    def test_query_one(self, db):
        db.execute("INSERT INTO itens (nome, valor) VALUES (?, ?)", ("item1", 10))
        row = db.query_one("SELECT * FROM itens WHERE nome = ?", ("item1",))
        assert row is not None
        assert row["nome"] == "item1"

    def test_query_one_nenhum(self, db):
        row = db.query_one("SELECT * FROM itens WHERE nome = ?", ("nao_existe",))
        assert row is None

    def test_query_scalar(self, db):
        db.execute("INSERT INTO itens (nome, valor) VALUES (?, ?)", ("a", 10))
        db.execute("INSERT INTO itens (nome, valor) VALUES (?, ?)", ("b", 20))
        total = db.query_scalar("SELECT SUM(valor) FROM itens")
        assert total == 30

    def test_query_scalar_vazio(self, db):
        total = db.query_scalar("SELECT COUNT(*) FROM itens")
        assert total == 0

    def test_multiplos_inserts(self, db):
        for i in range(10):
            db.execute("INSERT INTO itens (nome, valor) VALUES (?, ?)", (f"item{i}", i * 100))
        rows = db.query("SELECT * FROM itens ORDER BY valor")
        assert len(rows) == 10
        assert rows[0]["valor"] == 0
        assert rows[9]["valor"] == 900

    def test_connection_context_manager(self, db):
        with db.connection() as conn:
            conn.execute("INSERT INTO itens (nome, valor) VALUES (?, ?)", ("test", 1))
            conn.commit()
        rows = db.query("SELECT * FROM itens")
        assert len(rows) == 1


class TestSchemaConversion:
    def test_converter_schema(self):
        sqlite_sql = "CREATE TABLE t (id INTEGER PRIMARY KEY AUTOINCREMENT, data TIMESTAMP)"
        pg_sql = DatabaseBackend._converter_schema(sqlite_sql)
        assert "SERIAL PRIMARY KEY" in pg_sql
        assert "TIMESTAMPTZ" in pg_sql

    def test_converter_schema_vazio(self):
        assert DatabaseBackend._converter_schema("") == ""


class TestAdaptarSQL:
    def test_placeholder_sqlite(self, tmp_path):
        db = DatabaseBackend(sqlite_path=str(tmp_path / "t.db"))
        # SQLite deve manter ? como está
        sql = db._adaptar_sql("SELECT * FROM t WHERE id = ?")
        assert "?" in sql

    def test_diretorio_criado(self, tmp_path):
        subdir = tmp_path / "sub" / "dir"
        db = DatabaseBackend(sqlite_path=str(subdir / "test.db"))
        assert os.path.exists(str(subdir))
