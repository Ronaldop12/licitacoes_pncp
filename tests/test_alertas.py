"""
â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
TESTES PARA SISTEMA DE ALERTAS TELEGRAM - PNCP
â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

Testes unitÃ¡rios e de integraÃ§Ã£o para o sistema de alertas via Telegram.

Uso:
    pytest tests/test_alertas.py -v
    pytest tests/test_alertas.py::test_criar_alerta -v
"""

import pytest
import os
import json
import tempfile
import pandas as pd
from datetime import datetime
from pathlib import Path

# Imports locais
from utils_telegram import (
    TelegramAlerter,
    validar_token,
    validar_chat_id,
    criar_link_pncp
)
from alerts_db import AlertasDB
from monitor_alertas import filtrar_licitacoes_por_alerta


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# FIXTURES
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

@pytest.fixture
def db_teste():
    """Cria banco de dados em memÃ³ria para testes"""
    db = AlertasDB(":memory:")
    yield db


@pytest.fixture
def licitacao_exemplo():
    """Exemplo de licitaÃ§Ã£o para testes"""
    return {
        'id': 1,
        'orgao': 'PREFEITURA DE SÃƒO PAULO',
        'objeto': 'ContrataÃ§Ã£o de serviÃ§os de consultoria em TI',
        'valor_estimado': 250000.00,
        'uf': 'SP',
        'municipio': 'SÃ£o Paulo',
        'data_publicacao': '2026-03-07',
        'numero_edital': 'EDITAL-2026-001',
        'modalidade': 'LicitaÃ§Ã£o',
        'status': 'Publicado'
    }


@pytest.fixture
def licitacoes_multi():
    """MÃºltiplas licitaÃ§Ãµes para testes"""
    return [
        {
            'orgao': 'PREFEITURA SP',
            'objeto': 'Desenvolvimento de software',
            'valor_estimado': 150000,
            'uf': 'SP',
            'municipio': 'SÃ£o Paulo',
            'data_publicacao': '2026-03-07',
            'numero_edital': 'SP-001',
            'modalidade': 'LicitaÃ§Ã£o'
        },
        {
            'orgao': 'PREFEITURA RJ',
            'objeto': 'ImplantaÃ§Ã£o de cloud',
            'valor_estimado': 300000,
            'uf': 'RJ',
            'municipio': 'Rio de Janeiro',
            'data_publicacao': '2026-03-07',
            'numero_edital': 'RJ-001',
            'modalidade': 'LicitaÃ§Ã£o'
        },
        {
            'orgao': 'PREFEITURA MG',
            'objeto': 'Suporte tÃ©cnico',
            'valor_estimado': 50000,
            'uf': 'MG',
            'municipio': 'Belo Horizonte',
            'data_publicacao': '2026-03-07',
            'numero_edital': 'MG-001',
            'modalidade': 'LicitaÃ§Ã£o'
        }
    ]


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# TESTES - VALIDAÃ‡ÃƒO
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

class TestValidacao:
    """Testes de validaÃ§Ã£o de dados"""

    def test_validar_token_valido(self):
        """Token Telegram vÃ¡lido"""
        token = "123456789:ABC-DEF1234ghIKL-zyx57W2v1u123ew11"
        assert validar_token(token) == True

    def test_validar_token_invalido_sem_colon(self):
        """Token sem dois pontos Ã© invÃ¡lido"""
        token = "123456789ABC-DEF1234ghIKL-zyx57W2v1u123ew11"
        assert validar_token(token) == False

    def test_validar_token_invalido_muito_curto(self):
        """Token com segundo parte muito curta Ã© invÃ¡lido"""
        token = "123456789:ABC"
        assert validar_token(token) == False

    def test_validar_token_invalido_parte1_nao_numero(self):
        """Primeira parte deve ser nÃºmero"""
        token = "ABC12345:DEF1234ghIKL-zyx57W2v1u123ew11"
        assert validar_token(token) == False

    def test_validar_token_none(self):
        """None Ã© invÃ¡lido"""
        assert validar_token(None) == False

    def test_validar_chat_id_numero(self):
        """Chat ID numÃ©rico Ã© vÃ¡lido"""
        assert validar_chat_id("123456789") == True

    def test_validar_chat_id_negativo(self):
        """Chat ID negativo (canal/grupo) Ã© vÃ¡lido"""
        assert validar_chat_id("-123456789") == True

    def test_validar_chat_id_username(self):
        """Chat ID como @username Ã© vÃ¡lido"""
        assert validar_chat_id("@meu_canal") == True

    def test_validar_chat_id_invalido_vazio(self):
        """Chat ID vazio Ã© invÃ¡lido"""
        assert validar_chat_id("") == False

    def test_validar_chat_id_invalido_username_incompleto(self):
        """@sem nome Ã© invÃ¡lido"""
        assert validar_chat_id("@") == False


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# TESTES - UTILITÃRIOS TELEGRAM
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

class TestUtilitariosTelegram:
    """Testes de funÃ§Ãµes utilitÃ¡rias"""

    def test_criar_link_pncp(self):
        """Cria link PNCP corretamente"""
        link = criar_link_pncp("EDITAL-2026-001")
        assert "https://www.pncp.gov.br/app/editais" in link
        assert "EDITAL-2026-001" in link

    def test_criar_link_pncp_com_especiais(self):
        """Cria link com caracteres especiais"""
        link = criar_link_pncp("EDITAL-2026/001")
        assert link  # Apenas verificar que nÃ£o raise exception


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# TESTES - FORMATAÃ‡ÃƒO
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

class TestFormatacao:
    """Testes de formataÃ§Ã£o de mensagens"""

    def test_formatar_alerta_licitacao(self, licitacao_exemplo):
        """Formata licitaÃ§Ã£o como alerta"""
        bot = TelegramAlerter("123456789:ABC-DEF1234ghIKL-zyx57W2v1u123ew11")
        msg = bot.formatar_alerta_licitacao(licitacao_exemplo)

        assert "NOVA LICITA" in msg
        assert "Paulo" in msg
        assert "250000" in msg or "250.000" in msg
        assert "SP" in msg
        assert "PNCP" in msg

    def test_formatar_alerta_com_campos_faltantes(self):
        """Formata com campos faltantes"""
        bot = TelegramAlerter("123456789:ABC-DEF1234ghIKL-zyx57W2v1u123ew11")
        lic_incompleta = {'orgao': 'Teste'}
        msg = bot.formatar_alerta_licitacao(lic_incompleta)

        assert "Teste" in msg
        assert "N/A" in msg or "None" not in msg

    def test_formatar_confirmacao_config(self):
        """Formata confirmaÃ§Ã£o de configuraÃ§Ã£o"""
        bot = TelegramAlerter("123456789:ABC-DEF1234ghIKL-zyx57W2v1u123ew11")
        config = {
            'nome': 'Alerta Teste',
            'ativo': True,
            'ufs': ['SP', 'RJ'],
            'valor_min': 100000,
            'valor_max': 500000,
            'orgaos': ['*'],
            'palavras_chave': []
        }
        msg = bot.formatar_confirmacao_config(config)

        assert "Alerta Configurado" in msg or "Confirmado" in msg
        assert "Teste" in msg
        assert "SP" in msg


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# TESTES - BANCO DE DADOS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

class TestAlertasDB:
    """Testes de gerenciamento de banco de dados"""

    def test_criar_alerta(self, db_teste):
        """Cria novo alerta"""
        resultado = db_teste.criar_alerta(
            nome="Teste",
            chat_id="-123456789",
            ufs=["SP"],
            valor_min=0,
            valor_max=500000
        )
        assert resultado == True

    def test_criar_alerta_duplicado(self, db_teste):
        """NÃ£o cria alerta com mesmo nome"""
        db_teste.criar_alerta("Duplicado", "-123", ["SP"])
        resultado = db_teste.criar_alerta("Duplicado", "-456", ["RJ"])
        assert resultado == False

    def test_listar_alertas(self, db_teste):
        """Lista todos os alertas"""
        db_teste.criar_alerta("Alert1", "-111", ["SP"])
        db_teste.criar_alerta("Alert2", "-222", ["RJ"])

        alertas = db_teste.listar_alertas()
        assert len(alertas) == 2
        assert alertas[0]['nome'] == "Alert1"

    def test_listar_apenas_ativos(self, db_teste):
        """Lista apenas alertas ativos"""
        db_teste.criar_alerta("Ativo", "-111", ["SP"], ativo=True)
        db_teste.criar_alerta("Inativo", "-222", ["RJ"], ativo=False)

        ativos = db_teste.listar_alertas(apenas_ativos=True)
        assert len(ativos) == 1
        assert ativos[0]['nome'] == "Ativo"

    def test_obter_alerta(self, db_teste):
        """ObtÃ©m alerta especÃ­fico"""
        db_teste.criar_alerta("GetTest", "-999", ["MG"])
        alertas = db_teste.listar_alertas()

        alerta = db_teste.obter_alerta(alertas[0]['id'])
        assert alerta is not None
        assert alerta['nome'] == "GetTest"

    def test_atualizar_alerta(self, db_teste):
        """Atualiza um alerta"""
        db_teste.criar_alerta("Original", "-111", ["SP"])
        alertas = db_teste.listar_alertas()

        db_teste.atualizar_alerta(alertas[0]['id'], nome="Atualizado")
        alerta = db_teste.obter_alerta(alertas[0]['id'])
        assert alerta['nome'] == "Atualizado"

    def test_deletar_alerta(self, db_teste):
        """Deleta um alerta"""
        db_teste.criar_alerta("ParaDeletar", "-111", ["SP"])
        alertas = db_teste.listar_alertas()
        alerta_id = alertas[0]['id']

        resultado = db_teste.deletar_alerta(alerta_id)
        assert resultado == True

        alertas_restantes = db_teste.listar_alertas()
        assert len(alertas_restantes) == 0

    def test_registrar_alerta_enviado(self, db_teste):
        """Registra alerta como enviado"""
        db_teste.criar_alerta("Test", "-111", ["SP"])
        alertas = db_teste.listar_alertas()

        resultado = db_teste.registrar_alerta_enviado(
            alertas[0]['id'],
            "EDITAL-001",
            250000,
            "Prefeitura"
        )
        assert resultado == True

        historico = db_teste.listar_historico()
        assert len(historico) == 1
        assert historico[0]['numero_edital'] == "EDITAL-001"

    def test_listar_historico(self, db_teste):
        """Lista histÃ³rico de alertas"""
        db_teste.criar_alerta("Test", "-111", ["SP"])
        alertas = db_teste.listar_alertas()

        # Registrar vÃ¡rios
        for i in range(3):
            db_teste.registrar_alerta_enviado(
                alertas[0]['id'],
                f"EDITAL-{i}",
                100000 * (i + 1),
                f"Org {i}"
            )

        historico = db_teste.listar_historico()
        assert len(historico) == 3

    def test_monitoramento_status(self, db_teste):
        """Atualiza e obtÃ©m status de monitoramento"""
        status = db_teste.obter_status_monitoramento()
        assert status is not None

        db_teste.atualizar_monitoramento(
            intervalo_segundos=600,
            total_alertas_enviados=10
        )

        status = db_teste.obter_status_monitoramento()
        assert status['intervalo_segundos'] == 600
        assert status['total_alertas_enviados'] == 10


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# TESTES - INTEGRAÃ‡ÃƒO
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

class TestIntegracao:
    """Testes de integraÃ§Ã£o"""

    def test_fluxo_completo_alerta(self, db_teste, licitacao_exemplo):
        """Fluxo completo: criar alerta, registrar, listar"""
        # 1. Criar alerta
        db_teste.criar_alerta(
            "Fluxo Teste",
            "-123",
            ["SP"],
            valor_min=100000,
            valor_max=300000
        )

        # 2. Registrar envio
        alertas = db_teste.listar_alertas()
        db_teste.registrar_alerta_enviado(
            alertas[0]['id'],
            "EDITAL-001",
            250000,
            "PREFEITURA SP"
        )

        # 3. Verificar
        historico = db_teste.listar_historico(alertas[0]['id'])
        assert len(historico) == 1
        assert historico[0]['valor'] == 250000

    def test_multiplos_alertas_mesmo_chat(self, db_teste):
        """MÃºltiplos alertas para o mesmo chat"""
        chat_id = "-999"
        db_teste.criar_alerta("Alert SP", chat_id, ["SP"])
        db_teste.criar_alerta("Alert RJ", chat_id, ["RJ"])

        alertas = db_teste.listar_alertas()
        chat_alertas = [a for a in alertas if a['chat_id'] == chat_id]
        assert len(chat_alertas) == 2

    def test_filtro_uf_com_coringa_retorna_todas(self, licitacoes_multi):
        """UF com '*' deve considerar todas as licitacoes."""
        alerta = {
            "nome": "Todas UFs",
            "ufs": ["*"],
            "valor_min": 0,
            "valor_max": 999999999,
            "orgaos": ["*"],
            "palavras_chave": [],
        }

        resultado = filtrar_licitacoes_por_alerta(licitacoes_multi, alerta)
        assert len(resultado) == len(licitacoes_multi)

    def test_filtro_uf_especifica_restringe_resultados(self, licitacoes_multi):
        """UF especifica deve manter o comportamento de filtro."""
        alerta = {
            "nome": "Somente RJ",
            "ufs": ["RJ"],
            "valor_min": 0,
            "valor_max": 999999999,
            "orgaos": ["*"],
            "palavras_chave": [],
        }

        resultado = filtrar_licitacoes_por_alerta(licitacoes_multi, alerta)
        assert len(resultado) == 1
        assert resultado[0]["uf"] == "RJ"


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# TESTES - DADOS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

class TestDados:
    """Testes com dados de exemplo"""

    def test_parse_json_alertas(self, db_teste):
        """Parseia corretamente JSONs armazenados"""
        db_teste.criar_alerta(
            "JSON Test",
            "-123",
            ["SP", "RJ"],
            orgaos=["PREFEITURA", "CAMARA"],
            palavras_chave=["software", "cloud"]
        )

        alerta = db_teste.listar_alertas()[0]
        assert isinstance(alerta['ufs'], list)
        assert isinstance(alerta['orgaos'], list)
        assert isinstance(alerta['palavras_chave'], list)
        assert alerta['ufs'] == ["SP", "RJ"]
        assert "software" in alerta['palavras_chave']

    def test_valor_padrao_alertas(self, db_teste):
        """Valores padrÃ£o sÃ£o aplicados corretamente"""
        db_teste.criar_alerta("Default Test", "-123", ["SP"])
        alerta = db_teste.listar_alertas()[0]

        assert alerta['valor_min'] == 0
        assert alerta['valor_max'] == 999999999
        assert alerta['orgaos'] == ["*"]
        assert alerta['ativo'] == 1


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# EXECUTAR TESTES
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

