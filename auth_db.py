"""
Gerenciamento de autenticação e favoritos do dashboard.
"""

import sqlite3
import json
import logging
import os
import time
import bcrypt
from contextlib import closing
from datetime import datetime
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

DB_PATH = os.path.join("dados", "usuarios.db")

# Colunas permitidas para UPDATE (whitelist contra SQL injection)
_COLUNAS_USUARIOS = {"nome", "email", "papel", "ativo", "senha_hash"}
_COLUNAS_FAVORITOS = {"notas"}

# Proteção contra brute-force: {username: [(timestamp, falhou)]}
_LOGIN_ATTEMPTS: Dict[str, list] = {}
_MAX_ATTEMPTS = 5
_LOCKOUT_SECONDS = 300  # 5 minutos


def _hash_senha(senha: str) -> str:
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verificar_senha(senha: str, hash_armazenado: str) -> bool:
    try:
        return bcrypt.checkpw(senha.encode("utf-8"), hash_armazenado.encode("utf-8"))
    except Exception:
        return False


class AuthDB:
    """Gerenciador de usuários, autenticação e favoritos."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        diretorio = os.path.dirname(db_path)
        if diretorio and not os.path.exists(diretorio):
            os.makedirs(diretorio)
        self._criar_tabelas()
        self._garantir_admin()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _criar_tabelas(self):
        with closing(self._get_connection()) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    senha_hash TEXT NOT NULL,
                    nome TEXT NOT NULL DEFAULT '',
                    email TEXT DEFAULT '',
                    papel TEXT NOT NULL DEFAULT 'usuario',
                    ativo INTEGER NOT NULL DEFAULT 1,
                    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ultimo_login TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS favoritos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id INTEGER NOT NULL,
                    numero_edital TEXT NOT NULL,
                    orgao TEXT DEFAULT '',
                    objeto TEXT DEFAULT '',
                    valor_estimado REAL DEFAULT 0,
                    uf TEXT DEFAULT '',
                    notas TEXT DEFAULT '',
                    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
                    UNIQUE(usuario_id, numero_edital)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS buscas_salvas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id INTEGER NOT NULL,
                    nome TEXT NOT NULL,
                    filtros TEXT NOT NULL DEFAULT '{}',
                    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
                )
            """)

            # DB-04: Índices para consultas frequentes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_usuarios_username ON usuarios(username)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_favoritos_usuario_id ON favoritos(usuario_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_buscas_usuario_id ON buscas_salvas(usuario_id)")

            conn.commit()

    def _garantir_admin(self):
        """Cria usuário admin padrão se não existir."""
        admin_user = os.getenv("ADMIN_USERNAME", "admin")
        admin_hash = os.getenv("ADMIN_PASSWORD_HASH", "")
        admin_nome = os.getenv("ADMIN_NAME", "Administrador")
        admin_email = os.getenv("ADMIN_EMAIL", "")

        with closing(self._get_connection()) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM usuarios WHERE username = ?", (admin_user,))
            if not cursor.fetchone():
                if not admin_hash:
                    import secrets
                    senha_gerada = secrets.token_urlsafe(12)
                    admin_hash = _hash_senha(senha_gerada)
                    # Salva a senha no arquivo para consulta no primeiro acesso
                    senha_file = os.path.join(os.path.dirname(self.db_path), ".admin_senha_inicial")
                    with open(senha_file, "w", encoding="utf-8") as f:
                        f.write(senha_gerada)
                    print(f"[ADMIN] Senha inicial salva em {senha_file}")
                    print(f"[ADMIN] Use ADMIN_PASSWORD_HASH no .env para definir senha fixa.")
                cursor.execute(
                    "INSERT INTO usuarios (username, senha_hash, nome, email, papel) VALUES (?, ?, ?, ?, ?)",
                    (admin_user, admin_hash, admin_nome, admin_email, "admin"),
                )
                conn.commit()

    # ==================== AUTENTICAÇÃO ====================

    def autenticar(self, username: str, senha: str) -> Optional[Dict]:
        # Proteção contra brute-force
        agora = time.time()
        tentativas = _LOGIN_ATTEMPTS.get(username, [])
        # Limpar tentativas antigas
        tentativas = [t for t in tentativas if agora - t < _LOCKOUT_SECONDS]
        _LOGIN_ATTEMPTS[username] = tentativas

        if len(tentativas) >= _MAX_ATTEMPTS:
            logger.warning("Login bloqueado por brute-force para: %s", username)
            return None

        with closing(self._get_connection()) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM usuarios WHERE username = ? AND ativo = 1", (username,)
            )
            row = cursor.fetchone()
            if row and _verificar_senha(senha, row["senha_hash"]):
                # Limpar tentativas no sucesso
                _LOGIN_ATTEMPTS.pop(username, None)
                cursor.execute(
                    "UPDATE usuarios SET ultimo_login = CURRENT_TIMESTAMP WHERE id = ?",
                    (row["id"],),
                )
                conn.commit()
                return dict(row)

            # Registrar tentativa falha
            _LOGIN_ATTEMPTS.setdefault(username, []).append(agora)
            return None

    def criar_usuario(self, username: str, senha: str, nome: str = "",
                      email: str = "", papel: str = "usuario") -> bool:
        try:
            with closing(self._get_connection()) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO usuarios (username, senha_hash, nome, email, papel) VALUES (?, ?, ?, ?, ?)",
                    (username, _hash_senha(senha), nome, email, papel),
                )
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False
        except Exception as e:
            logger.error("Erro ao criar usuário: %s", e)
            return False

    def listar_usuarios(self) -> List[Dict]:
        with closing(self._get_connection()) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, nome, email, papel, ativo, criado_em, ultimo_login FROM usuarios")
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def alterar_senha(self, usuario_id: int, nova_senha: str) -> bool:
        try:
            with closing(self._get_connection()) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE usuarios SET senha_hash = ? WHERE id = ?",
                    (_hash_senha(nova_senha), usuario_id),
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error("Erro ao alterar senha: %s", e)
            return False

    # ==================== FAVORITOS ====================

    def adicionar_favorito(self, usuario_id: int, numero_edital: str,
                           orgao: str = "", objeto: str = "",
                           valor_estimado: float = 0, uf: str = "",
                           notas: str = "") -> bool:
        try:
            with closing(self._get_connection()) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO favoritos 
                    (usuario_id, numero_edital, orgao, objeto, valor_estimado, uf, notas)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (usuario_id, numero_edital, orgao, objeto, valor_estimado, uf, notas))
                conn.commit()
                return True
        except Exception as e:
            logger.error("Erro ao adicionar favorito: %s", e)
            return False

    def remover_favorito(self, usuario_id: int, numero_edital: str) -> bool:
        try:
            with closing(self._get_connection()) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM favoritos WHERE usuario_id = ? AND numero_edital = ?",
                    (usuario_id, numero_edital),
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error("Erro ao remover favorito: %s", e)
            return False

    def listar_favoritos(self, usuario_id: int) -> List[Dict]:
        with closing(self._get_connection()) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM favoritos WHERE usuario_id = ? ORDER BY criado_em DESC",
                (usuario_id,),
            )
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def eh_favorito(self, usuario_id: int, numero_edital: str) -> bool:
        with closing(self._get_connection()) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM favoritos WHERE usuario_id = ? AND numero_edital = ?",
                (usuario_id, numero_edital),
            )
            result = cursor.fetchone()
            return result is not None

    def contar_favoritos(self, usuario_id: int) -> int:
        with closing(self._get_connection()) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) as total FROM favoritos WHERE usuario_id = ?",
                (usuario_id,),
            )
            row = cursor.fetchone()
            return row["total"] if row else 0

    # ==================== BUSCAS SALVAS ====================

    def salvar_busca(self, usuario_id: int, nome: str, filtros: Dict) -> bool:
        try:
            with closing(self._get_connection()) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO buscas_salvas (usuario_id, nome, filtros) VALUES (?, ?, ?)",
                    (usuario_id, nome, json.dumps(filtros, ensure_ascii=False)),
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error("Erro ao salvar busca: %s", e)
            return False

    def listar_buscas(self, usuario_id: int) -> List[Dict]:
        with closing(self._get_connection()) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM buscas_salvas WHERE usuario_id = ? ORDER BY criado_em DESC",
                (usuario_id,),
            )
            rows = cursor.fetchall()
            result = []
            for r in rows:
                d = dict(r)
                d["filtros"] = json.loads(d["filtros"]) if d["filtros"] else {}
                result.append(d)
            return result

    def deletar_busca(self, busca_id: int, usuario_id: int) -> bool:
        try:
            with closing(self._get_connection()) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM buscas_salvas WHERE id = ? AND usuario_id = ?",
                    (busca_id, usuario_id),
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error("Erro ao deletar busca: %s", e)
            return False

    # ==================== PERMISSÕES POR ROLE ====================

    # Papéis válidos: admin, analista, viewer
    PERMISSOES = {
        "admin": {
            "ver_dados", "buscar", "exportar", "favoritos",
            "alertas", "coleta", "admin_usuarios", "api_config",
            "fontes_complementares", "historico",
        },
        "analista": {
            "ver_dados", "buscar", "exportar", "favoritos",
            "alertas", "fontes_complementares", "historico",
        },
        "viewer": {
            "ver_dados", "buscar",
        },
        "usuario": {  # legado, mapeia para analista
            "ver_dados", "buscar", "exportar", "favoritos",
            "alertas", "fontes_complementares", "historico",
        },
    }

    @staticmethod
    def tem_permissao(papel: str, permissao: str) -> bool:
        """Verifica se um papel tem determinada permissão."""
        return permissao in AuthDB.PERMISSOES.get(papel, set())

    def alterar_papel(self, usuario_id: int, novo_papel: str) -> bool:
        """Altera o papel/role de um usuário."""
        if novo_papel not in self.PERMISSOES:
            return False
        try:
            with closing(self._get_connection()) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE usuarios SET papel = ? WHERE id = ?",
                    (novo_papel, usuario_id),
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error("Erro ao alterar papel: %s", e)
            return False

    def desativar_usuario(self, usuario_id: int) -> bool:
        """Desativa um usuário."""
        try:
            with closing(self._get_connection()) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE usuarios SET ativo = 0 WHERE id = ?",
                    (usuario_id,),
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error("Erro ao desativar usuário: %s", e)
            return False

    def ativar_usuario(self, usuario_id: int) -> bool:
        """Ativa um usuário."""
        try:
            with closing(self._get_connection()) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE usuarios SET ativo = 1 WHERE id = ?",
                    (usuario_id,),
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error("Erro ao ativar usuário: %s", e)
            return False
