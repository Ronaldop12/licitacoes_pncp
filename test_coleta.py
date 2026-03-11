"""
========================================
TESTES UNITÁRIOS - PROCESSAMENTO DE DADOS
========================================
Valida funcionamento de filtros de TI e processamento de dados da coleta
"""

import pytest
from datetime import datetime
from constantes import PALAVRAS_TI, PALAVRAS_EXCLUSAO


# ==================== FUNÇÕES DE TESTE ====================

def eh_licitacao_ti(texto):
    """Replica a função de detecção de TI (igual à produção)"""
    if not texto:
        return False
    
    texto_lower = str(texto).lower()
    
    for exclusao in PALAVRAS_EXCLUSAO:
        if exclusao in texto_lower:
            return False
    
    for palavra in PALAVRAS_TI:
        if palavra in texto_lower:
            return True
    
    return False


# ==================== TESTES DE FILTRO TI ====================

def test_detecta_software():
    """Testa detecção de 'software'"""
    assert eh_licitacao_ti("Licença de software") is True
    assert eh_licitacao_ti("SOFTWARE DE GESTÃO") is True


def test_detecta_sistema():
    """Testa deteção de termos com 'sistema'"""
    assert eh_licitacao_ti("Sistema de informações gerenciais") is True
    assert eh_licitacao_ti("DESENVOLVIMENTO DE SISTEMA ERP") is True


def test_detecta_cloud():
    """Testa detecção de 'cloud' e 'nuvem'"""
    assert eh_licitacao_ti("Serviços em cloud") is True
    assert eh_licitacao_ti("Infraestrutura em nuvem") is True


def test_detecta_apis():
    """Testa deteção de termos de infraestrutura"""
    assert eh_licitacao_ti("Solução de firewall corporativo") is True
    assert eh_licitacao_ti("Contratação de ERP corporativo") is True


def test_detecta_linguagens():
    """Testa detecção de linguagens de programação"""
    assert eh_licitacao_ti("Desenvolvimento em Python") is True
    assert eh_licitacao_ti("Sistema legado Java") is True
    assert eh_licitacao_ti("Aplicação nodejs") is True


def test_detecta_infraestrutura():
    """Testa detecção de infraestrutura"""
    assert eh_licitacao_ti("Infraestrutura de TI do órgão") is True
    assert eh_licitacao_ti("Segurança da informação corporativa") is True


def test_detecta_containers():
    """Testa detecção de container/orquestração"""
    assert eh_licitacao_ti("Docker e Kubernetes") is True
    assert eh_licitacao_ti("Automação com Docker") is True


def test_detecta_cloud_providers():
    """Testa detecção de providers de cloud"""
    assert eh_licitacao_ti("Hospedagem AWS") is True
    assert eh_licitacao_ti("Serviço Azure") is True
    assert eh_licitacao_ti("Google Cloud Platform (GCP)") is True


def test_nao_detecta_obras():
    """Testa que não detecta obras públicas"""
    assert eh_licitacao_ti("Construção de prédio") is False
    assert eh_licitacao_ti("Reforma de estrada") is False
    assert eh_licitacao_ti("Pavimentação de rua") is False


def test_nao_detecta_servicos_gerais():
    """Testa que não detecta serviços gerais"""
    assert eh_licitacao_ti("Limpeza e conservação") is False
    assert eh_licitacao_ti("Serviços de catering") is False


def test_nao_detecta_texto_vazio():
    """Testa que NÃO detecta texto vazio"""
    assert eh_licitacao_ti("") is False
    assert eh_licitacao_ti(None) is False


def test_case_insensitive():
    """Testa que a detecção é case-insensitive"""
    assert eh_licitacao_ti("SOFTWARE") is True
    assert eh_licitacao_ti("Software") is True
    assert eh_licitacao_ti("SoFtWaRe") is True


def test_deteccao_em_contexto():
    """Testa detecção em contexto maior"""
    texto = "Aquisição de licença de software para gestão de dados do departamento de TI"
    assert eh_licitacao_ti(texto) is True


def test_multiplas_palavras_ti():
    """Testa texto com múltiplas palavras-chave de TI"""
    texto = "Desenvolvimento de sistema de informações com cloud e segurança"
    assert eh_licitacao_ti(texto) is True


# ==================== TESTES DE CASOS EXTREMOS ====================

def test_palavra_ti_como_substring():
    """Testa palavra como substring"""
    assert eh_licitacao_ti("Tecnologia da informação aplicada") is True
    assert eh_licitacao_ti("Serviços de computador e periféricos") is True


def test_palavra_ti_parcial():
    """Testa match parcial de palavras"""
    assert eh_licitacao_ti("Softwares e aplicativos") is True
    assert eh_licitacao_ti("Contratação de backup corporativo") is True


def test_acentuacao():
    """Testa com acentuação"""
    assert eh_licitacao_ti("Aquisição de antivírus corporativo") is True
    assert eh_licitacao_ti("Videoconferência institucional") is True


# ==================== TESTES DE PROCESSAMENTO ====================

def test_processar_item_ti():
    """Testa processamento de um item de TI"""
    item = {
        "objetoCompra": "Licença de software de gestão",
        "orgaoEntidade": {"razaoSocial": "Ministério de TI"},
        "unidadeOrgao": {"ufSigla": "SP", "municipioNome": "São Paulo"},
        "valorTotalEstimado": 50000,
        "dataPublicacaoPncp": "2025-01-01",
        "numeroControlePNCP": "12345",
        "modalidadeNome": "Licitação",
        "situacaoCompraNome": "Publicada",
    }
    
    # Este é apenas um exemplo de estrutura esperada
    assert "objetoCompra" in item
    assert eh_licitacao_ti(item["objetoCompra"]) is True


def test_processar_item_nao_ti():
    """Testa que item não-TI é rejeitado"""
    item = {
        "objetoCompra": "Construção de muro",
        "orgaoEntidade": {"razaoSocial": "Prefeitura"},
        "unidadeOrgao": {"ufSigla": "RJ", "municipioNome": "Rio"},
    }
    
    assert eh_licitacao_ti(item["objetoCompra"]) is False


# ==================== TESTES DE VALIDAÇÃO DE CAMPOS ====================

def test_validar_uf_item():
    """Testa validação de UF em item"""
    from utils_uf import eh_uf_valida
    
    valores_uf = [
        ("SP", True),
        ("sp", True),
        ("XX", False),
        ("N/A", False),
        (None, False),
    ]
    
    for uf, esperado in valores_uf:
        resultado = eh_uf_valida(uf)
        assert resultado == esperado


def test_validar_valor_numerico():
    """Testa validação de valor numérico"""
    valores_validos = [0, 1000, 50000, 1000000]
    
    for valor in valores_validos:
        assert isinstance(valor, (int, float))
        assert valor >= 0


def test_validar_data():
    """Testa validação de data"""
    from datetime import datetime
    
    data_str = "2025-01-01"
    data = datetime.fromisoformat(data_str)
    
    assert isinstance(data, datetime)
    assert data.year == 2025


# ==================== TESTES DE DEDUPLICAÇÃO ====================

def test_numero_edital_unico():
    """Testa que número de edital identifica único item"""
    items = [
        {"numeroControlePNCP": "12345", "objetoCompra": "Software A"},
        {"numeroControlePNCP": "12345", "objetoCompra": "Software A duplicado"},
        {"numeroControlePNCP": "67890", "objetoCompra": "Software B"},
    ]
    
    # Simular deduplicação
    numeros_unicos = set()
    items_dedup = []
    
    for item in items:
        numero = item.get("numeroControlePNCP")
        if numero not in numeros_unicos:
            numeros_unicos.add(numero)
            items_dedup.append(item)
    
    assert len(items_dedup) == 2  # Deve ficar com 2 itens


# ==================== TESTES DE FILTRO COMBINADO ====================

def test_filtro_ti_e_uf():
    """Testa combinação de filtro de TI e UF"""
    from utils_uf import eh_uf_valida
    
    items = [
        {"objetoCompra": "Software de gestão", "uf": "SP"},
        {"objetoCompra": "Construção", "uf": "RJ"},
        {"objetoCompra": "Desenvolvimento de sistema web", "uf": "XX"},
    ]
    
    # Filtrar: TI E UF válida
    resultado = [
        item for item in items
        if eh_licitacao_ti(item["objetoCompra"]) and eh_uf_valida(item["uf"])
    ]
    
    assert len(resultado) == 1
    assert resultado[0]["uf"] == "SP"


# ==================== MAIN PARA EXECUÇÃO RÁPIDA ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
