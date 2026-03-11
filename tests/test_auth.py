"""Testes para auth_db.py — autenticação, favoritos, roles, buscas salvas."""

import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth_db import AuthDB


@pytest.fixture
def db(tmp_path):
    """Cria um AuthDB em banco temporário."""
    # Remover variáveis de ambiente que interferem
    env_backup = {}
    for key in ("ADMIN_USERNAME", "ADMIN_PASSWORD_HASH", "ADMIN_NAME", "ADMIN_EMAIL"):
        env_backup[key] = os.environ.pop(key, None)

    db_path = str(tmp_path / "test_usuarios.db")
    auth = AuthDB(db_path=db_path)

    yield auth

    for key, val in env_backup.items():
        if val is not None:
            os.environ[key] = val


class TestAutenticacao:
    def test_admin_criado_automaticamente(self, db):
        usuarios = db.listar_usuarios()
        assert any(u["username"] == "admin" for u in usuarios)

    def test_criar_usuario(self, db):
        assert db.criar_usuario("joao", "senha123", nome="João", email="j@test.com")
        usuarios = db.listar_usuarios()
        joao = [u for u in usuarios if u["username"] == "joao"]
        assert len(joao) == 1
        assert joao[0]["nome"] == "João"
        assert joao[0]["papel"] == "usuario"

    def test_criar_usuario_duplicado(self, db):
        db.criar_usuario("maria", "abc123")
        assert db.criar_usuario("maria", "outra") is False

    def test_autenticar_valido(self, db):
        db.criar_usuario("teste", "minhasenha")
        user = db.autenticar("teste", "minhasenha")
        assert user is not None
        assert user["username"] == "teste"

    def test_autenticar_invalido(self, db):
        db.criar_usuario("teste", "minhasenha")
        assert db.autenticar("teste", "errada") is None
        assert db.autenticar("inexistente", "qualquer") is None

    def test_alterar_senha(self, db):
        db.criar_usuario("user1", "antiga")
        user = db.autenticar("user1", "antiga")
        assert db.alterar_senha(user["id"], "nova123")
        assert db.autenticar("user1", "antiga") is None
        assert db.autenticar("user1", "nova123") is not None


class TestRoles:
    def test_permissoes_admin(self, db):
        assert AuthDB.tem_permissao("admin", "admin_usuarios")
        assert AuthDB.tem_permissao("admin", "ver_dados")
        assert AuthDB.tem_permissao("admin", "exportar")
        assert AuthDB.tem_permissao("admin", "coleta")

    def test_permissoes_analista(self, db):
        assert AuthDB.tem_permissao("analista", "ver_dados")
        assert AuthDB.tem_permissao("analista", "exportar")
        assert AuthDB.tem_permissao("analista", "favoritos")
        assert not AuthDB.tem_permissao("analista", "admin_usuarios")
        assert not AuthDB.tem_permissao("analista", "coleta")

    def test_permissoes_viewer(self, db):
        assert AuthDB.tem_permissao("viewer", "ver_dados")
        assert AuthDB.tem_permissao("viewer", "buscar")
        assert not AuthDB.tem_permissao("viewer", "exportar")
        assert not AuthDB.tem_permissao("viewer", "favoritos")
        assert not AuthDB.tem_permissao("viewer", "admin_usuarios")

    def test_alterar_papel(self, db):
        db.criar_usuario("analista1", "senha")
        user = db.autenticar("analista1", "senha")
        assert db.alterar_papel(user["id"], "analista")
        # Verificar
        usuarios = db.listar_usuarios()
        a = [u for u in usuarios if u["username"] == "analista1"][0]
        assert a["papel"] == "analista"

    def test_alterar_papel_invalido(self, db):
        db.criar_usuario("x", "y")
        user = db.autenticar("x", "y")
        assert db.alterar_papel(user["id"], "superadmin") is False

    def test_desativar_ativar(self, db):
        db.criar_usuario("temp", "123")
        user = db.autenticar("temp", "123")
        db.desativar_usuario(user["id"])
        assert db.autenticar("temp", "123") is None
        db.ativar_usuario(user["id"])
        assert db.autenticar("temp", "123") is not None


class TestFavoritos:
    def test_adicionar_listar(self, db):
        db.criar_usuario("u1", "s1")
        user = db.autenticar("u1", "s1")
        uid = user["id"]

        assert db.adicionar_favorito(uid, "EDIT-001", orgao="Org1", uf="SP")
        favs = db.listar_favoritos(uid)
        assert len(favs) == 1
        assert favs[0]["numero_edital"] == "EDIT-001"

    def test_eh_favorito(self, db):
        db.criar_usuario("u2", "s2")
        user = db.autenticar("u2", "s2")
        uid = user["id"]

        assert not db.eh_favorito(uid, "EDIT-002")
        db.adicionar_favorito(uid, "EDIT-002")
        assert db.eh_favorito(uid, "EDIT-002")

    def test_remover_favorito(self, db):
        db.criar_usuario("u3", "s3")
        user = db.autenticar("u3", "s3")
        uid = user["id"]

        db.adicionar_favorito(uid, "EDIT-003")
        assert db.contar_favoritos(uid) == 1
        db.remover_favorito(uid, "EDIT-003")
        assert db.contar_favoritos(uid) == 0

    def test_favoritos_isolados_por_usuario(self, db):
        db.criar_usuario("a", "a")
        db.criar_usuario("b", "b")
        ua = db.autenticar("a", "a")
        ub = db.autenticar("b", "b")

        db.adicionar_favorito(ua["id"], "EDIT-X")
        assert db.contar_favoritos(ua["id"]) == 1
        assert db.contar_favoritos(ub["id"]) == 0


class TestBuscasSalvas:
    def test_salvar_listar(self, db):
        db.criar_usuario("s1", "s1")
        user = db.autenticar("s1", "s1")

        filtros = {"busca": "cloud", "uf": "SP"}
        assert db.salvar_busca(user["id"], "Cloud SP", filtros)
        buscas = db.listar_buscas(user["id"])
        assert len(buscas) == 1
        assert buscas[0]["nome"] == "Cloud SP"
        assert buscas[0]["filtros"]["busca"] == "cloud"

    def test_deletar(self, db):
        db.criar_usuario("s2", "s2")
        user = db.autenticar("s2", "s2")

        db.salvar_busca(user["id"], "Teste", {"x": 1})
        buscas = db.listar_buscas(user["id"])
        assert db.deletar_busca(buscas[0]["id"], user["id"])
        assert len(db.listar_buscas(user["id"])) == 0
