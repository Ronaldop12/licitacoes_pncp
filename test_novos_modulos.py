"""Testes para os módulos novos: metricas, precos_db, agendador, portais estaduais, pdf_parser, coletor_async."""

import os
import json
import pytest
import pandas as pd

# ===================== MetricasDB =====================

class TestMetricasDB:

    def setup_method(self):
        self.db_path = "dados/test_metricas.db"
        from metricas import MetricasDB
        self.m = MetricasDB(db_path=self.db_path)

    def teardown_method(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_registrar_evento(self):
        self.m.registrar_evento("info", "teste", "mensagem de teste", 42.0)
        eventos = self.m.ultimos_eventos(limite=1)
        assert len(eventos) == 1
        assert eventos[0]["tipo"] == "info"
        assert eventos[0]["componente"] == "teste"
        assert eventos[0]["valor"] == 42.0

    def test_registrar_coleta(self):
        self.m.registrar_coleta(total_ti=100, total_verificadas=5000, duracao_s=10.5, erros=2)
        resumo = self.m.metricas_resumo()
        assert resumo["metricas_coleta"]["coleta_total_ti"] == 100
        assert resumo["metricas_coleta"]["coleta_erros"] == 2

    def test_exportar_prometheus(self):
        self.m.registrar_coleta(total_ti=50, total_verificadas=1000, duracao_s=5.0)
        texto = self.m.exportar_prometheus()
        assert "radar_coleta_total_ti 50" in texto
        assert "# TYPE" in texto

    def test_estatisticas(self):
        self.m.registrar_evento("erro", "api", "timeout")
        stats = self.m.estatisticas()
        assert stats["total_eventos"] >= 1
        assert stats["total_erros"] >= 1
        assert stats["ultimo_evento"] != "N/A"

    def test_salvar_json(self):
        caminho = "dados/test_metricas_export.json"
        self.m.registrar_coleta(total_ti=10, total_verificadas=100, duracao_s=1.0)
        self.m.salvar_json(caminho=caminho)
        assert os.path.exists(caminho)
        with open(caminho, "r") as f:
            data = json.load(f)
        assert "exportado_em" in data
        os.remove(caminho)

    def test_ultimos_eventos_filtra_tipo(self):
        self.m.registrar_evento("info", "a", "x")
        self.m.registrar_evento("erro", "b", "y")
        erros = self.m.ultimos_eventos(tipo="erro")
        assert all(e["tipo"] == "erro" for e in erros)


# ===================== PrecosDB =====================

class TestPrecosDB:

    def setup_method(self):
        self.db_path = "dados/test_precos.db"
        from precos_db import PrecosDB
        self.p = PrecosDB(db_path=self.db_path)

    def teardown_method(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_registrar_precos(self):
        df = pd.DataFrame([
            {"numero_edital": "ED001", "codigo_catmat_catser": "CAT001", "valor_estimado": 1000.0, "orgao": "Org A", "uf": "SP"},
            {"numero_edital": "ED002", "codigo_catmat_catser": "CAT001", "valor_estimado": 2000.0, "orgao": "Org B", "uf": "RJ"},
        ])
        self.p.registrar_precos(df)
        stats = self.p.estatisticas_gerais()
        assert stats["total_registros"] == 2
        assert stats["categorias_distintas"] == 1

    def test_evolucao_por_categoria(self):
        df = pd.DataFrame([
            {"numero_edital": "ED01", "codigo_catmat_catser": "C1", "valor_estimado": 500, "orgao": "A", "uf": "SP"},
            {"numero_edital": "ED02", "codigo_catmat_catser": "C1", "valor_estimado": 700, "orgao": "B", "uf": "SP"},
        ])
        self.p.registrar_precos(df)
        evo = self.p.evolucao_por_categoria("C1")
        assert len(evo) == 2

    def test_resumo_categorias(self):
        df = pd.DataFrame([
            {"numero_edital": "E1", "codigo_catmat_catser": "X1", "valor_estimado": 100, "orgao": "O1", "uf": "SP"},
            {"numero_edital": "E2", "codigo_catmat_catser": "X2", "valor_estimado": 200, "orgao": "O2", "uf": "RJ"},
        ])
        self.p.registrar_precos(df)
        res = self.p.resumo_categorias()
        assert len(res) == 2

    def test_dedup_por_edital(self):
        df = pd.DataFrame([
            {"numero_edital": "DUP01", "codigo_catmat_catser": "C1", "valor_estimado": 100, "orgao": "A", "uf": "SP"},
        ])
        self.p.registrar_precos(df)
        self.p.registrar_precos(df)  # duplicata — deve ser ignorada
        stats = self.p.estatisticas_gerais()
        assert stats["total_registros"] == 1


# ===================== Agendador =====================

class TestAgendador:

    def test_carregar_config_padrao(self):
        from agendador import carregar_config, CONFIG_PADRAO
        cfg = carregar_config()
        assert "coleta_pncp" in cfg
        assert cfg["coleta_pncp"]["habilitado"] is True

    def test_salvar_e_carregar_config(self):
        from agendador import salvar_config, carregar_config, ARQUIVO_CONFIG
        cfg = {"coleta_pncp": {"habilitado": False, "horas": 12}}
        salvar_config(cfg)
        loaded = carregar_config()
        assert loaded["coleta_pncp"]["habilitado"] is False
        # Cleanup
        if os.path.exists(ARQUIVO_CONFIG):
            os.remove(ARQUIVO_CONFIG)

    def test_agendador_sem_apscheduler(self):
        from agendador import AgendadorTarefas
        ag = AgendadorTarefas()
        assert ag.ativo is False
        assert ag.listar_jobs() == []


# ===================== Portais Estaduais =====================

class TestPortaisEstaduais:

    def test_eh_ti_funcao(self):
        from coletor_portais_estaduais import _eh_ti
        assert _eh_ti("aquisição de computadores e notebooks")
        assert _eh_ti("contratação de software ERP")
        assert not _eh_ti("material de limpeza")
        assert not _eh_ti("")

    def test_coletor_orquestrador_instancia(self):
        from coletor_portais_estaduais import ColetorPortaisEstaduais
        c = ColetorPortaisEstaduais()
        assert len(c.coletores) == 3


# ===================== PDF Parser =====================

class TestPDFParser:

    def test_extrair_valores_do_texto(self):
        from pdf_parser import extrair_valores_do_texto
        texto = """
        Valor Total: R$ 1.500.000,00
        Prazo de entrega: 30 dias
        CNPJ: 12.345.678/0001-90
        Email: contato@orgao.gov.br
        Data: 15/03/2025
        SLA de 99,9% de uptime para backup em nuvem
        """
        resultado = extrair_valores_do_texto(texto)
        assert len(resultado["valores_encontrados"]) > 0
        assert "1.500.000,00" in resultado["valores_encontrados"][0]
        assert len(resultado["cnpjs_encontrados"]) > 0
        assert len(resultado["emails_encontrados"]) > 0
        assert len(resultado["datas_encontradas"]) > 0
        assert len(resultado["requisitos_tecnicos"]) > 0

    def test_extrair_valores_texto_vazio(self):
        from pdf_parser import extrair_valores_do_texto
        resultado = extrair_valores_do_texto("")
        assert resultado["valores_encontrados"] == []
        assert resultado["requisitos_tecnicos"] == []


# ===================== Coletor Async =====================

class TestColetorAsync:

    def test_importa_sem_erro(self):
        import coletor_async
        assert hasattr(coletor_async, "coletar_sincrono_wrapper")

    def test_wrapper_existe(self):
        from coletor_async import coletar_sincrono_wrapper
        assert callable(coletar_sincrono_wrapper)
