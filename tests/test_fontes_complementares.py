"""Testes para coletor_fontes_complementares.py"""

import os
import pytest
import pandas as pd


class TestColetorBase:

    def test_eh_ti_positivo(self):
        from coletor_fontes_complementares import ColetorBase
        c = ColetorBase("teste")
        assert c._eh_ti("Aquisição de software ERP para gestão")
        assert c._eh_ti("Contratação de infraestrutura de rede")
        assert c._eh_ti("Licenciamento de antivírus corporativo")

    def test_eh_ti_negativo(self):
        from coletor_fontes_complementares import ColetorBase
        c = ColetorBase("teste")
        assert not c._eh_ti("Material de limpeza e higiene")
        assert not c._eh_ti("Reforma de prédio público")
        assert not c._eh_ti("")
        assert not c._eh_ti(None)

    def test_exportar_csv_sem_dados(self, tmp_path):
        from coletor_fontes_complementares import ColetorBase
        c = ColetorBase("teste")
        caminho = str(tmp_path / "vazio.csv")
        assert c.exportar_csv(caminho) is False

    def test_exportar_csv_com_dados(self, tmp_path):
        from coletor_fontes_complementares import ColetorBase
        c = ColetorBase("teste")
        c.dados = [{"campo1": "valor1", "campo2": 100}]
        caminho = str(tmp_path / "dados.csv")
        assert c.exportar_csv(caminho) is True
        assert os.path.exists(caminho)
        df = pd.read_csv(caminho)
        assert len(df) == 1


class TestColetorQueridoDiario:

    def test_instancia(self):
        from coletor_fontes_complementares import ColetorQueridoDiario
        qd = ColetorQueridoDiario()
        assert qd.nome == "QueridoDiário"
        assert qd.API_URL.startswith("https://")


class TestColetorPortalTransparencia:

    def test_instancia_sem_chave(self):
        from coletor_fontes_complementares import ColetorPortalTransparencia
        pt = ColetorPortalTransparencia(chave_api="")
        assert pt.nome == "PortalTransparência"

    def test_instancia_com_chave(self):
        from coletor_fontes_complementares import ColetorPortalTransparencia
        pt = ColetorPortalTransparencia(chave_api="abc123")
        assert pt.chave_api == "abc123"


class TestColetorComprasGov:

    def test_instancia(self):
        from coletor_fontes_complementares import ColetorComprasGov
        cg = ColetorComprasGov()
        assert cg.nome == "Compras.gov.br"


class TestColetorMultiFontes:

    def test_instancia(self):
        from coletor_fontes_complementares import ColetorMultiFontes
        cm = ColetorMultiFontes(chave_transparencia="")
        assert cm.resultados == {}
        assert cm.erros == {}


class TestHelpers:

    def test_carregar_chave_transparencia(self, tmp_path, monkeypatch):
        from coletor_fontes_complementares import carregar_chave_transparencia
        # Sem arquivo .env específico, deve retornar string (pode ser vazia)
        result = carregar_chave_transparencia()
        assert isinstance(result, str)

    def test_salvar_chave_transparencia(self, tmp_path, monkeypatch):
        from coletor_fontes_complementares import salvar_chave_transparencia
        # Não deve lançar exceção mesmo com chave vazia
        salvar_chave_transparencia("")
