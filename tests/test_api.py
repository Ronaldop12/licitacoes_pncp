"""Testes para api_rest.py — endpoints da API FastAPI."""

import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from api_rest import app


client = TestClient(app)


class TestRoot:
    def test_health(self):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "versao" in data


class TestLicitacoes:
    def test_listar(self):
        response = client.get("/api/v1/licitacoes")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "resultados" in data

    def test_paginacao(self):
        response = client.get("/api/v1/licitacoes?pagina=1&por_pagina=5")
        assert response.status_code == 200
        data = response.json()
        assert data["pagina"] == 1
        assert data["por_pagina"] == 5

    def test_filtro_uf(self):
        response = client.get("/api/v1/licitacoes?uf=SP")
        assert response.status_code == 200

    def test_filtro_busca(self):
        response = client.get("/api/v1/licitacoes?busca=software")
        assert response.status_code == 200

    def test_filtro_valor(self):
        response = client.get("/api/v1/licitacoes?valor_min=100000&valor_max=500000")
        assert response.status_code == 200


class TestEstatisticas:
    def test_estatisticas(self):
        response = client.get("/api/v1/estatisticas")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data


class TestUFs:
    def test_ufs(self):
        response = client.get("/api/v1/ufs")
        assert response.status_code == 200


class TestHistorico:
    def test_historico(self):
        response = client.get("/api/v1/historico")
        assert response.status_code == 200
        assert "coletas" in response.json()


class TestStatus:
    def test_status(self):
        response = client.get("/api/v1/status")
        assert response.status_code == 200
        data = response.json()
        assert data["online"] is True


class TestEditalNaoEncontrado:
    def test_404(self):
        response = client.get("/api/v1/licitacoes/EDITAL_INEXISTENTE_999")
        assert response.status_code == 404
