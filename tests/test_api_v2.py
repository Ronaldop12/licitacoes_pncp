"""Testes para novos endpoints da API — JWT, busca FTS5, exportação XLSX, notificações."""

import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from api_rest import app

client = TestClient(app)


class TestJWTAuth:
    def test_login_sem_credenciais(self):
        resp = client.post("/api/v1/auth/login", json={})
        assert resp.status_code == 400

    def test_login_credenciais_invalidas(self):
        resp = client.post("/api/v1/auth/login", json={"username": "x", "senha": "y"})
        assert resp.status_code == 401

    def test_me_sem_token(self):
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    def test_me_token_invalido(self):
        resp = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalido"})
        assert resp.status_code == 401


class TestBuscaFTS:
    def test_busca_basica(self):
        resp = client.get("/api/v1/busca", params={"q": "software"})
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "resultados" in data
        assert "consulta" in data

    def test_busca_com_uf(self):
        resp = client.get("/api/v1/busca", params={"q": "software", "uf": "SP"})
        assert resp.status_code == 200

    def test_busca_muito_curta(self):
        resp = client.get("/api/v1/busca", params={"q": "a"})
        assert resp.status_code == 422  # Validação min_length

    def test_sugerir(self):
        resp = client.get("/api/v1/busca/sugerir", params={"prefixo": "soft"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_reindexar(self):
        resp = client.post("/api/v1/busca/reindexar")
        assert resp.status_code == 200


class TestExportarXLSX:
    def test_exportar_sem_dados(self):
        resp = client.get("/api/v1/exportar/xlsx")
        # Pode ser 200 se há dados ou 404 se não
        assert resp.status_code in (200, 404)

    def test_exportar_com_filtro_uf(self):
        resp = client.get("/api/v1/exportar/xlsx", params={"uf": "SP"})
        assert resp.status_code in (200, 404)


class TestNotificacoes:
    def test_status(self):
        resp = client.get("/api/v1/notificacoes/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_canais" in data
        assert "slack" in data
        assert "discord" in data

    def test_teste_sem_canais(self):
        resp = client.post("/api/v1/notificacoes/teste")
        # Sem canais configurados → 400
        assert resp.status_code == 400


class TestRateLimiting:
    def test_endpoint_responde(self):
        """Rate limiter não deve bloquear requisições normais."""
        for _ in range(5):
            resp = client.get("/")
            assert resp.status_code == 200
