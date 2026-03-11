"""
Testes do módulo pdf_parser — extração de PDFs e cache de análises.
"""

import os
import sys
import json
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pdf_parser import (
    extrair_valores_do_texto,
    extrair_itens_licitacao,
    AnalisesDB,
)


# ========== TESTES DE EXTRAÇÃO DE VALORES ==========

class TestExtrairValores:

    def test_valores_monetarios(self):
        texto = "O valor estimado é R$ 150.000,00 e o lote 2 custa R$ 85.500,50."
        resultado = extrair_valores_do_texto(texto)
        assert len(resultado["valores_encontrados"]) >= 2
        assert any("150.000" in v for v in resultado["valores_encontrados"])

    def test_datas(self):
        texto = "Abertura em 15/03/2026 e encerramento em 30/04/2026."
        resultado = extrair_valores_do_texto(texto)
        assert "15/03/2026" in resultado["datas_encontradas"]
        assert "30/04/2026" in resultado["datas_encontradas"]

    def test_cnpjs(self):
        texto = "CNPJ: 00.000.000/0001-00 - Ministério da Educação"
        resultado = extrair_valores_do_texto(texto)
        assert "00.000.000/0001-00" in resultado["cnpjs_encontrados"]

    def test_emails(self):
        texto = "Contato: licitacao@orgao.gov.br e suporte@ti.gov.br"
        resultado = extrair_valores_do_texto(texto)
        assert len(resultado["emails_encontrados"]) >= 2

    def test_requisitos_tecnicos(self):
        texto = "A solução deve garantir SLA de 99,9% com backup diário e LGPD."
        resultado = extrair_valores_do_texto(texto)
        assert "SLA" in resultado["requisitos_tecnicos"]
        assert "backup" in resultado["requisitos_tecnicos"]
        assert "LGPD" in resultado["requisitos_tecnicos"]

    def test_texto_vazio(self):
        resultado = extrair_valores_do_texto("")
        assert resultado["valores_encontrados"] == []
        assert resultado["requisitos_tecnicos"] == []

    def test_texto_sem_dados(self):
        resultado = extrair_valores_do_texto("Texto qualquer sem dados estruturados.")
        assert resultado["valores_encontrados"] == []
        assert resultado["datas_encontradas"] == []


# ========== TESTES DE EXTRAÇÃO DE ITENS ==========

class TestExtrairItens:

    def test_itens_basicos(self):
        texto = """
        Item 1: Licença de software antivírus para 500 estações.
        Quantidade: 500 unidades. Valor total: R$ 75.000,00.
        Item 2: Serviço de suporte técnico 24x7 por 12 meses.
        Quantidade: 12 meses. Valor total: R$ 120.000,00.
        """
        itens = extrair_itens_licitacao(texto)
        assert len(itens) >= 2
        assert itens[0]["numero"] == 1
        assert itens[1]["numero"] == 2

    def test_lotes(self):
        texto = """
        Lote 1: Servidores e storage para data center.
        Valor: R$ 500.000,00.
        Lote 2: Switches e roteadores de rede.
        Valor: R$ 200.000,00.
        """
        itens = extrair_itens_licitacao(texto)
        assert len(itens) >= 2

    def test_sem_itens(self):
        texto = "Contratação global de serviço sem divisão em lotes."
        itens = extrair_itens_licitacao(texto)
        assert itens == []

    def test_texto_vazio(self):
        itens = extrair_itens_licitacao("")
        assert itens == []

    def test_item_com_valores(self):
        texto = """
        Item 1: Notebook Dell Latitude 14" com 16GB RAM.
        Valor unitário: R$ 5.500,00. Valor total: R$ 55.000,00.
        Quantidade: 10 unidades.
        """
        itens = extrair_itens_licitacao(texto)
        assert len(itens) >= 1
        item = itens[0]
        assert item["numero"] == 1
        if "valor_total" in item and item.get("valor_total"):
            assert item["valor_total"] > 0


# ========== TESTES DO CACHE DE ANÁLISES ==========

class TestAnalisesDB:

    @pytest.fixture
    def db(self, tmp_path):
        return AnalisesDB(db_path=str(tmp_path / "test_analises.db"))

    def test_criar_tabelas(self, db):
        stats = db.estatisticas()
        assert stats["total_analisados"] == 0

    def test_salvar_e_obter_analise(self, db):
        resultado = {
            "arquivos": [{"titulo": "edital.pdf", "tipo": "PDF", "url": "http://test"}],
            "texto_completo": "Texto de exemplo para edital de TI com SLA e backup.",
            "analise": {
                "valores_encontrados": ["R$ 100.000,00"],
                "datas_encontradas": ["15/03/2026"],
                "cnpjs_encontrados": ["00.000.000/0001-00"],
                "emails_encontrados": ["test@gov.br"],
                "requisitos_tecnicos": ["SLA", "backup"],
            },
            "itens": [
                {"numero": 1, "descricao": "Licença de software", "quantidade": 10, "valor_total": 100000.0},
            ],
        }

        assert db.salvar_analise("PE-2026-001", "00000000000100", resultado)

        cached = db.obter_analise("PE-2026-001")
        assert cached is not None
        assert cached["numero_edital"] == "PE-2026-001"
        assert cached["qtd_arquivos"] == 1
        assert cached["qtd_itens"] == 1
        assert "SLA" in cached["requisitos_tecnicos"]
        assert len(cached["itens"]) == 1

    def test_listar_analises(self, db):
        for i in range(5):
            db.salvar_analise(f"PE-2026-{i:03d}", "00000000000100", {
                "arquivos": [], "texto_completo": "", "analise": {}, "itens": []
            })
        lista = db.listar_analises(limite=3)
        assert len(lista) == 3

    def test_estatisticas(self, db):
        db.salvar_analise("PE-001", "123", {
            "arquivos": [], "texto_completo": "", "analise": {},
            "itens": [{"numero": 1, "descricao": "Item"}],
        })
        db.salvar_analise("PE-002", "456", {
            "arquivos": [], "texto_completo": "", "analise": {},
            "itens": [],
        })
        stats = db.estatisticas()
        assert stats["total_analisados"] == 2
        assert stats["com_itens_extraidos"] == 1

    def test_upsert_analise(self, db):
        """Salvar mesma análise duas vezes substitui."""
        db.salvar_analise("PE-001", "123", {
            "arquivos": [], "texto_completo": "versao 1", "analise": {}, "itens": [],
        })
        db.salvar_analise("PE-001", "123", {
            "arquivos": [{"titulo": "a"}], "texto_completo": "versao 2", "analise": {},
            "itens": [{"numero": 1}],
        })
        cached = db.obter_analise("PE-001")
        assert cached["qtd_arquivos"] == 1
        assert cached["qtd_itens"] == 1

    def test_obter_analise_inexistente(self, db):
        assert db.obter_analise("NAOEXISTE") is None
