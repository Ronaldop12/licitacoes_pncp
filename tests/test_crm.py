"""Testes para crm_db.py — CRM e Pipeline de Propostas."""

import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crm_db import CrmDB, ESTAGIOS, ESTAGIOS_ATIVOS, ESTAGIOS_FINAIS


@pytest.fixture
def crm(tmp_path):
    db_path = str(tmp_path / "crm_test.db")
    return CrmDB(db_path=db_path)


class TestCriarProposta:
    def test_criar_basica(self, crm):
        pid = crm.criar_proposta(numero_edital="PE-2026-0001", orgao="Orgao X", objeto="Licenças")
        assert pid == 1

    def test_criar_com_campos_opcionais(self, crm):
        pid = crm.criar_proposta(
            numero_edital="PE-2026-0002",
            orgao="Orgao Y",
            objeto="Servidores",
            valor_estimado=500000.0,
            uf="SP",
            responsavel="João",
            notas="Nota teste",
            tags=["urgente", "TI"],
        )
        assert pid >= 1
        proposta = crm.obter_proposta(pid)
        assert proposta["orgao"] == "Orgao Y"
        assert proposta["valor_estimado"] == 500000.0
        assert proposta["estagio"] == "prospeccao"
        assert proposta["tags"] == ["urgente", "TI"]

    def test_criar_multiplas(self, crm):
        ids = [crm.criar_proposta(numero_edital=f"ED-{i}", orgao="Org", objeto="Obj") for i in range(5)]
        assert len(set(ids)) == 5


class TestObterProposta:
    def test_existente(self, crm):
        pid = crm.criar_proposta(numero_edital="ED-1", orgao="Org", objeto="Obj")
        p = crm.obter_proposta(pid)
        assert p is not None
        assert p["numero_edital"] == "ED-1"

    def test_inexistente(self, crm):
        assert crm.obter_proposta(9999) is None

    def test_por_edital(self, crm):
        crm.criar_proposta(numero_edital="PE-UNICO", orgao="Org", objeto="Obj")
        p = crm.obter_por_edital("PE-UNICO")
        assert p is not None
        assert p["numero_edital"] == "PE-UNICO"

    def test_por_edital_inexistente(self, crm):
        assert crm.obter_por_edital("NAO-EXISTE") is None


class TestAtualizarProposta:
    def test_atualizar_campos_validos(self, crm):
        pid = crm.criar_proposta(numero_edital="ED-1", orgao="Org", objeto="Obj")
        ok = crm.atualizar_proposta(pid, responsavel="Maria", notas="Atualizado")
        assert ok is True
        p = crm.obter_proposta(pid)
        assert p["responsavel"] == "Maria"
        assert p["notas"] == "Atualizado"

    def test_atualizar_campo_invalido(self, crm):
        pid = crm.criar_proposta(numero_edital="ED-1", orgao="Org", objeto="Obj")
        ok = crm.atualizar_proposta(pid, campo_inventado="valor")
        assert ok is False

    def test_atualizar_tags(self, crm):
        pid = crm.criar_proposta(numero_edital="ED-1", orgao="Org", objeto="Obj")
        crm.atualizar_proposta(pid, tags=["cloud", "seguranca"])
        p = crm.obter_proposta(pid)
        assert p["tags"] == ["cloud", "seguranca"]


class TestMoverEstagio:
    def test_mover_valido(self, crm):
        pid = crm.criar_proposta(numero_edital="ED-1", orgao="Org", objeto="Obj")
        ok = crm.mover_estagio(pid, "analise")
        assert ok is True
        p = crm.obter_proposta(pid)
        assert p["estagio"] == "analise"

    def test_mover_todos_estagios(self, crm):
        pid = crm.criar_proposta(numero_edital="ED-1", orgao="Org", objeto="Obj")
        # prospeccao → analise → decisao → elaborando → enviada → aguardando → vencida
        caminho = ["analise", "decisao", "elaborando", "enviada", "aguardando", "vencida"]
        for e in caminho:
            ok = crm.mover_estagio(pid, e)
            assert ok is True
        p = crm.obter_proposta(pid)
        assert p["estagio"] == "vencida"

    def test_mover_para_estagio_invalido(self, crm):
        pid = crm.criar_proposta(numero_edital="ED-1", orgao="Org", objeto="Obj")
        ok = crm.mover_estagio(pid, "estagio_inventado")
        assert ok is False

    def test_nao_move_de_estagio_final(self, crm):
        pid = crm.criar_proposta(numero_edital="ED-1", orgao="Org", objeto="Obj")
        crm.mover_estagio(pid, "vencida")
        ok = crm.mover_estagio(pid, "analise")
        assert ok is False

    def test_mover_proposta_inexistente(self, crm):
        ok = crm.mover_estagio(9999, "analise")
        assert ok is False

    def test_historico_registrado(self, crm):
        pid = crm.criar_proposta(numero_edital="ED-1", orgao="Org", objeto="Obj")
        crm.mover_estagio(pid, "analise", usuario="admin", observacao="Teste")
        hist = crm.historico_proposta(pid)
        # Deve ter 2: criação (→ prospeccao) + movimentação (→ analise)
        assert len(hist) == 2
        assert hist[1]["estagio_novo"] == "analise"
        assert hist[1]["usuario"] == "admin"


class TestTarefas:
    def test_adicionar_tarefa(self, crm):
        pid = crm.criar_proposta(numero_edital="ED-1", orgao="Org", objeto="Obj")
        tid = crm.adicionar_tarefa(pid, descricao="Analisar edital")
        assert tid >= 1

    def test_listar_tarefas(self, crm):
        pid = crm.criar_proposta(numero_edital="ED-1", orgao="Org", objeto="Obj")
        crm.adicionar_tarefa(pid, descricao="Tarefa 1")
        crm.adicionar_tarefa(pid, descricao="Tarefa 2", responsavel="Ana", prazo="2026-04-01")
        tarefas = crm.listar_tarefas(pid)
        assert len(tarefas) == 2
        assert tarefas[1]["responsavel"] == "Ana"

    def test_concluir_tarefa(self, crm):
        pid = crm.criar_proposta(numero_edital="ED-1", orgao="Org", objeto="Obj")
        tid = crm.adicionar_tarefa(pid, descricao="Tarefa")
        crm.concluir_tarefa(tid)
        tarefas = crm.listar_tarefas(pid)
        assert tarefas[0]["concluida"] == 1


class TestPipelineRelatorios:
    def test_listar_pipeline_vazio(self, crm):
        resultado = crm.listar_pipeline()
        assert resultado == []

    def test_listar_pipeline_com_dados(self, crm):
        crm.criar_proposta(numero_edital="ED-1", orgao="Org", objeto="Obj")
        crm.criar_proposta(numero_edital="ED-2", orgao="Org", objeto="Obj")
        resultado = crm.listar_pipeline()
        assert len(resultado) == 2

    def test_listar_pipeline_por_estagio(self, crm):
        p1 = crm.criar_proposta(numero_edital="ED-1", orgao="Org", objeto="Obj")
        crm.criar_proposta(numero_edital="ED-2", orgao="Org", objeto="Obj")
        crm.mover_estagio(p1, "analise")
        resultado = crm.listar_pipeline(estagio="analise")
        assert len(resultado) == 1

    def test_pipeline_resumo_vazio(self, crm):
        resumo = crm.pipeline_resumo()
        assert resumo["total_propostas"] == 0
        assert resumo["total_ativas"] == 0

    def test_pipeline_resumo_com_dados(self, crm):
        p1 = crm.criar_proposta(numero_edital="ED-1", orgao="Org", objeto="Obj")
        p2 = crm.criar_proposta(numero_edital="ED-2", orgao="Org", objeto="Obj")
        crm.mover_estagio(p1, "analise")
        crm.mover_estagio(p2, "vencida")
        resumo = crm.pipeline_resumo()
        assert resumo["total_propostas"] == 2
        assert resumo["por_estagio"].get("analise", 0) == 1
        assert resumo["por_estagio"].get("vencida", 0) == 1

    def test_taxa_conversao_vazio(self, crm):
        conv = crm.taxa_conversao()
        assert conv["total_propostas"] == 0
        assert conv["taxa_conversao"] == 0

    def test_taxa_conversao_com_dados(self, crm):
        p1 = crm.criar_proposta(numero_edital="ED-1", orgao="Org", objeto="Obj")
        p2 = crm.criar_proposta(numero_edital="ED-2", orgao="Org", objeto="Obj")
        p3 = crm.criar_proposta(numero_edital="ED-3", orgao="Org", objeto="Obj")
        crm.mover_estagio(p1, "vencida")
        crm.mover_estagio(p2, "perdida")
        # p3 continua em prospeccao (não finalizada)
        conv = crm.taxa_conversao()
        assert conv["finalizadas"] == 2
        assert conv["vencidas"] == 1
        assert conv["taxa_conversao"] == 50.0


class TestConstantes:
    def test_estagios_definidos(self):
        assert len(ESTAGIOS) == 9
        assert "prospeccao" in ESTAGIOS
        assert "vencida" in ESTAGIOS

    def test_estagios_finais(self):
        assert ESTAGIOS_FINAIS == {"vencida", "perdida", "desistencia"}

    def test_estagios_ativos(self):
        assert "prospeccao" in ESTAGIOS_ATIVOS
        assert "vencida" not in ESTAGIOS_ATIVOS
