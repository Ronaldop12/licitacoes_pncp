"""
═══════════════════════════════════════════════════════════════════════════════
GERENCIAMENTO DE BANCO DE DADOS DE ALERTAS - Sistema PNCP
═══════════════════════════════════════════════════════════════════════════════

Módulo para gerenciar persistência de configurações de alertas usando SQLite.

Uso:
    from alerts_db import AlertasDB
    db = AlertasDB()
    db.criar_alerta("SP", "-123456789", 0, 500000)
    alertas = db.listar_alertas()
"""

import sqlite3
import json
import logging
from contextlib import closing
from datetime import datetime
from typing import List, Dict, Any, Optional
import os

logger = logging.getLogger(__name__)

# Colunas permitidas para UPDATE (whitelist contra SQL injection)
_COLUNAS_ALERTAS = {
    "nome", "chat_id", "ufs", "valor_min", "valor_max",
    "orgaos", "palavras_chave", "ativo", "frequencia_min",
}
_COLUNAS_MONITORAMENTO = {
    "intervalo_segundos", "ativo", "ultimo_check", "hash_anterior",
    "total_alertas_enviados", "total_licitacoes_monitoradas", "ultimo_erro",
}

DB_PATH = "dados/alertas.db"


class AlertasDB:
    """Gerenciador de banco de dados de alertas"""

    def __init__(self, db_path: str = DB_PATH):
        """
        Inicializa o gerenciador de alertas
        
        Args:
            db_path: Caminho do arquivo SQLite (ou ":memory:" para teste)
        """
        self.db_path = db_path
        
        if db_path == ":memory:":
            # Named in-memory DB: closing() on individual connections is safe
            # while _keeper holds the shared database alive.
            self._mem_uri = f"file:alertas_{id(self)}?mode=memory&cache=shared"
            self._keeper = sqlite3.connect(self._mem_uri, uri=True)
        else:
            self._mem_uri = None
            self._keeper = None
            os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        
        self._criar_tabelas()
        logger.info("AlertasDB inicializado: %s", db_path)

    def _get_connection(self) -> sqlite3.Connection:
        """Obtém conexão com o banco de dados"""
        if self._mem_uri:
            conn = sqlite3.connect(self._mem_uri, uri=True, check_same_thread=False)
        else:
            conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _criar_tabelas(self):
        """Cria tabelas se não existirem"""
        try:
            with closing(self._get_connection()) as conn:
                cursor = conn.cursor()

                # Tabela de alertas
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS alertas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome TEXT NOT NULL UNIQUE,
                        chat_id TEXT NOT NULL,
                        ufs TEXT NOT NULL,
                        valor_min REAL DEFAULT 0,
                        valor_max REAL DEFAULT 999999999,
                        orgaos TEXT DEFAULT '*',
                        palavras_chave TEXT DEFAULT '',
                        ativo INTEGER DEFAULT 1,
                        frequencia_min INTEGER DEFAULT 60,
                        criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
                        ultimo_alerta TEXT,
                        proxximo_alerta TEXT
                    )
                """)

                # Tabela de historico de alertas enviados
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS historico_alertas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        alerta_id INTEGER NOT NULL,
                        numero_edital TEXT NOT NULL,
                        valor REAL NOT NULL,
                        orgao TEXT NOT NULL,
                        data_envio TEXT DEFAULT CURRENT_TIMESTAMP,
                        status TEXT DEFAULT 'enviado',
                        FOREIGN KEY (alerta_id) REFERENCES alertas(id)
                    )
                """)

                # Tabela de monitora estado do sistema
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS monitoramento (
                        id INTEGER PRIMARY KEY,
                        intervalo_segundos INTEGER DEFAULT 300,
                        ativo INTEGER DEFAULT 1,
                        ultimo_check TEXT,
                        hash_anterior TEXT,
                        total_licitacoes INTEGER DEFAULT 0,
                        total_alertas_enviados INTEGER DEFAULT 0,
                        ultimo_erro TEXT
                    )
                """)

                # Índices
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_alertas_chat_id ON alertas(chat_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_alertas_ativo ON alertas(ativo)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_hist_alerta_id ON historico_alertas(alerta_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_hist_data_envio ON historico_alertas(data_envio)")

                # Inserir registro padrão de monitoramento
                cursor.execute("""
                    INSERT OR IGNORE INTO monitoramento (id, intervalo_segundos, ativo)
                    VALUES (1, 300, 1)
                """)

                conn.commit()
                logger.info("✓ Tabelas do banco criadas com sucesso")

        except Exception as e:
            logger.error("✗ Erro ao criar tabelas: %s", e)
            raise

    def criar_alerta(
        self,
        nome: str,
        chat_id: str,
        ufs: List[str],
        valor_min: float = 0,
        valor_max: float = 999999999,
        orgaos: List[str] = None,
        palavras_chave: List[str] = None,
        ativo: bool = True
    ) -> bool:
        """
        Cria novo alerta
        
        Args:
            nome: Nome único do alerta
            chat_id: ID do chat Telegram
            ufs: Lista de UFs para monitorar
            valor_min: Valor mínimo da licitação
            valor_max: Valor máximo da licitação
            orgaos: Lista de órgãos (padrão: todos)
            palavras_chave: Palavras-chave para filtro
            ativo: Se o alerta está ativo
            
        Returns:
            True se criado com sucesso, False caso contrário
        """
        try:
            with closing(self._get_connection()) as conn:
                cursor = conn.cursor()

                ufs_str = json.dumps(ufs)
                orgaos_str = json.dumps(orgaos or ["*"])
                palavras_str = json.dumps(palavras_chave or [])

                cursor.execute("""
                    INSERT INTO alertas 
                    (nome, chat_id, ufs, valor_min, valor_max, orgaos, palavras_chave, ativo)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (nome, chat_id, ufs_str, valor_min, valor_max, orgaos_str, palavras_str, 1 if ativo else 0))

                conn.commit()
            logger.info("✓ Alerta criado: %s", nome)
            return True

        except sqlite3.IntegrityError:
            logger.warning("⚠ Alerta com nome '%s' já existe", nome)
            return False
        except Exception as e:
            logger.error("✗ Erro ao criar alerta: %s", e)
            return False

    def listar_alertas(self, apenas_ativos: bool = False) -> List[Dict[str, Any]]:
        """
        Lista todos os alertas
        
        Args:
            apenas_ativos: Se True, retorna apenas alertas ativos
            
        Returns:
            Lista de dicionários com alertas
        """
        try:
            with closing(self._get_connection()) as conn:
                cursor = conn.cursor()

                query = "SELECT * FROM alertas"
                if apenas_ativos:
                    query += " WHERE ativo = 1"

                cursor.execute(query)
                rows = cursor.fetchall()

            alertas = []
            for row in rows:
                alerta = dict(row)
                # Parsear JSONs
                alerta['ufs'] = json.loads(alerta['ufs'])
                alerta['orgaos'] = json.loads(alerta['orgaos'])
                alerta['palavras_chave'] = json.loads(alerta['palavras_chave'])
                alertas.append(alerta)

            return alertas

        except Exception as e:
            logger.error("✗ Erro ao listar alertas: %s", e)
            return []

    def obter_alerta(self, alerta_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtém um alerta específico
        
        Args:
            alerta_id: ID do alerta
            
        Returns:
            Dicionário com dados do alerta ou None
        """
        try:
            with closing(self._get_connection()) as conn:
                cursor = conn.cursor()

                cursor.execute("SELECT * FROM alertas WHERE id = ?", (alerta_id,))
                row = cursor.fetchone()

            if row:
                alerta = dict(row)
                alerta['ufs'] = json.loads(alerta['ufs'])
                alerta['orgaos'] = json.loads(alerta['orgaos'])
                alerta['palavras_chave'] = json.loads(alerta['palavras_chave'])
                return alerta

            return None

        except Exception as e:
            logger.error("✗ Erro ao obter alerta: %s", e)
            return None

    def atualizar_alerta(self, alerta_id: int, **kwargs) -> bool:
        """
        Atualiza um alerta
        
        Args:
            alerta_id: ID do alerta
            **kwargs: Campos a atualizar
            
        Returns:
            True se atualizado com sucesso
        """
        try:
            # Parsear listas para JSON se necessário
            if 'ufs' in kwargs and isinstance(kwargs['ufs'], list):
                kwargs['ufs'] = json.dumps(kwargs['ufs'])
            if 'orgaos' in kwargs and isinstance(kwargs['orgaos'], list):
                kwargs['orgaos'] = json.dumps(kwargs['orgaos'])
            if 'palavras_chave' in kwargs and isinstance(kwargs['palavras_chave'], list):
                kwargs['palavras_chave'] = json.dumps(kwargs['palavras_chave'])

            # Whitelist de colunas para prevenir SQL injection
            campos_seguros = {k: v for k, v in kwargs.items() if k in _COLUNAS_ALERTAS}
            if not campos_seguros:
                return False

            fields = ", ".join([f"{k} = ?" for k in campos_seguros.keys()])
            values = list(campos_seguros.values()) + [alerta_id]

            with closing(self._get_connection()) as conn:
                cursor = conn.cursor()
                cursor.execute(f"UPDATE alertas SET {fields} WHERE id = ?", values)
                conn.commit()

            logger.info("✓ Alerta %s atualizado", alerta_id)
            return True

        except Exception as e:
            logger.error("✗ Erro ao atualizar alerta: %s", e)
            return False

    def deletar_alerta(self, alerta_id: int) -> bool:
        """
        Deleta um alerta e seu histórico
        
        Args:
            alerta_id: ID do alerta
            
        Returns:
            True se deletado com sucesso
        """
        try:
            with closing(self._get_connection()) as conn:
                cursor = conn.cursor()

                cursor.execute("DELETE FROM historico_alertas WHERE alerta_id = ?", (alerta_id,))
                cursor.execute("DELETE FROM alertas WHERE id = ?", (alerta_id,))

                conn.commit()

            logger.info("✓ Alerta %s deletado", alerta_id)
            return True

        except Exception as e:
            logger.error("✗ Erro ao deletar alerta: %s", e)
            return False

    def registrar_alerta_enviado(
        self,
        alerta_id: int,
        numero_edital: str,
        valor: float,
        orgao: str
    ) -> bool:
        """
        Registra um alerta como enviado
        
        Args:
            alerta_id: ID do alerta
            numero_edital: Número do edital
            valor: Valor da licitação
            orgao: Órgão responsável
            
        Returns:
            True se registrado com sucesso
        """
        try:
            with closing(self._get_connection()) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO historico_alertas (alerta_id, numero_edital, valor, orgao)
                    VALUES (?, ?, ?, ?)
                """, (alerta_id, numero_edital, valor, orgao))

                # Atualizar último alerta
                cursor.execute("""
                    UPDATE alertas 
                    SET ultimo_alerta = CURRENT_TIMESTAMP,
                        proxximo_alerta = datetime(CURRENT_TIMESTAMP, '+' || frequencia_min || ' minutes')
                    WHERE id = ?
                """, (alerta_id,))

                conn.commit()

            logger.info("✓ Alerta %s registrado: %s", alerta_id, numero_edital)
            return True

        except Exception as e:
            logger.error("✗ Erro ao registrar alerta enviado: %s", e)
            return False

    def listar_historico(self, alerta_id: int = None, limite: int = 100) -> List[Dict[str, Any]]:
        """
        Lista histórico de alertas enviados
        
        Args:
            alerta_id: ID do alerta (None para todos)
            limite: Número máximo de registros
            
        Returns:
            Lista de históricos
        """
        try:
            with closing(self._get_connection()) as conn:
                cursor = conn.cursor()

                if alerta_id:
                    cursor.execute("""
                        SELECT * FROM historico_alertas 
                        WHERE alerta_id = ?
                        ORDER BY data_envio DESC
                        LIMIT ?
                    """, (alerta_id, limite))
                else:
                    cursor.execute("""
                        SELECT * FROM historico_alertas 
                        ORDER BY data_envio DESC
                        LIMIT ?
                    """, (limite,))

                rows = cursor.fetchall()

            return [dict(row) for row in rows]

        except Exception as e:
            logger.error("✗ Erro ao listar histórico: %s", e)
            return []

    def atualizar_monitoramento(self, **kwargs) -> bool:
        """
        Atualiza configurações de monitoramento
        
        Args:
            **kwargs: Campos a atualizar
            
        Returns:
            True se atualizado com sucesso
        """
        try:
            with closing(self._get_connection()) as conn:
                cursor = conn.cursor()

                # Whitelist de colunas para prevenir SQL injection
                campos_seguros = {k: v for k, v in kwargs.items() if k in _COLUNAS_MONITORAMENTO}
                if not campos_seguros:
                    return False

                fields = ", ".join([f"{k} = ?" for k in campos_seguros.keys()])
                values = list(campos_seguros.values())

                cursor.execute(f"UPDATE monitoramento SET {fields} WHERE id = 1", values)
                conn.commit()

            return True

        except Exception as e:
            logger.error("✗ Erro ao atualizar monitoramento: %s", e)
            return False

    def obter_status_monitoramento(self) -> Optional[Dict[str, Any]]:
        """
        Obtém status atual de monitoramento
        
        Returns:
            Dicionário com status ou None
        """
        try:
            with closing(self._get_connection()) as conn:
                cursor = conn.cursor()

                cursor.execute("SELECT * FROM monitoramento WHERE id = 1")
                row = cursor.fetchone()

            return dict(row) if row else None

        except Exception as e:
            logger.error("\u2717 Erro ao obter status: %s", e)
            return None
