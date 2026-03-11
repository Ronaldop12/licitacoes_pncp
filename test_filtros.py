"""
========================================
TESTES UNITÁRIOS - VALIDAÇÃO DE UF E FILTROS
========================================
Valida funcionamento dos filtros de estado (UF) e processamento de dados
"""

import pytest
from utils_uf import (
    normalizar_uf, eh_uf_valida, listar_ufs_validas, 
    obter_nome_estado, UF_NOMES, validar_lista_ufs, contar_ufs_invalidas
)


# ==================== TESTES DE NORMALIZAÇÃO ====================

def test_normalizar_uf_valida():
    """Testa normalização de UF válida"""
    assert normalizar_uf('SP') == 'SP'
    assert normalizar_uf('sp') == 'SP'
    assert normalizar_uf('sP') == 'SP'


def test_normalizar_uf_com_espacos():
    """Testa normalização com espaços"""
    assert normalizar_uf('  SP  ') == 'SP'
    assert normalizar_uf(' rj ') == 'RJ'


def test_normalizar_uf_nome_estado():
    """Testa mapping de nome de estado para UF"""
    assert normalizar_uf('São Paulo') == 'SP'
    assert normalizar_uf('rio de janeiro') == 'RJ'
    assert normalizar_uf('RIO GRANDE DO SUL') == 'RS'


def test_normalizar_uf_invalida():
    """Testa que UF inválida retorna None"""
    assert normalizar_uf('XX') is None
    assert normalizar_uf('XYZ') is None


def test_normalizar_uf_vazia():
    """Testa valores vazios/None"""
    assert normalizar_uf(None) is None
    assert normalizar_uf('') is None
    assert normalizar_uf('   ') is None


def test_normalizar_uf_valores_especiais():
    """Testa valores especiais como 'N/A', 'nan'"""
    assert normalizar_uf('N/A') is None
    assert normalizar_uf('nan') is None
    assert normalizar_uf('NAN') is None
    assert normalizar_uf('null') is None


# ==================== TESTES DE VALIDAÇÃO ====================

def test_eh_uf_valida_true():
    """Testa validação positiva de UF"""
    assert eh_uf_valida('SP') is True
    assert eh_uf_valida('sp') is True
    assert eh_uf_valida('São Paulo') is True


def test_eh_uf_valida_false():
    """Testa validação negativa de UF"""
    assert eh_uf_valida('XX') is False
    assert eh_uf_valida(None) is False
    assert eh_uf_valida('N/A') is False


# ==================== TESTES DE OBTENÇÃO DE NOME ====================

def test_obter_nome_estado_valido():
    """Testa obtenção de nome de estado"""
    assert obter_nome_estado('SP') == 'São Paulo'
    assert obter_nome_estado('RJ') == 'Rio de Janeiro'
    assert obter_nome_estado('DF') == 'Distrito Federal'


def test_obter_nome_estado_invalido():
    """Testa obtenção de nome para estado inválido"""
    assert obter_nome_estado('XX') is None
    assert obter_nome_estado(None) is None


# ==================== TESTES DE LISTAGEM ====================

def test_listar_ufs_validas():
    """Testa listagem de UFs válidas"""
    ufs = listar_ufs_validas()
    assert len(ufs) == 27  # 26 estados + DF
    assert 'SP' in ufs
    assert 'RJ' in ufs
    assert 'XX' not in ufs
    assert ufs == sorted(ufs)  # Deve estar ordenada


def test_ufs_nomes_todos_validos():
    """Testa que dicionário UF_NOMES contém todas as UFs válidas"""
    for uf in listar_ufs_validas():
        assert uf in UF_NOMES
        assert len(UF_NOMES[uf]) > 0


# ==================== TESTES DE VALIDAÇÃO DE LISTA ====================

def test_validar_lista_ufs_mixta():
    """Testa validação de lista com UFs mistas"""
    entrada = ['SP', 'sp', 'São Paulo', 'xx', 'RJ', 'N/A', None]
    resultado = validar_lista_ufs(entrada)
    
    # Deve conter apenas SP e RJ, sem duplicatas, ordenado
    assert resultado == ['RJ', 'SP']
    assert len(resultado) == 2


def test_validar_lista_ufs_vazia():
    """Testa validação de lista vazia"""
    assert validar_lista_ufs([]) == []
    assert validar_lista_ufs(['XX', 'N/A', None]) == []


# ==================== TESTES DE CONTAGEM ====================

def test_contar_ufs_invalidas_pandas():
    """Testa contagem de UFs inválidas em Series pandas"""
    try:
        import pandas as pd
        
        series = pd.Series(['SP', 'RJ', 'XX', 'N/A', None, 'MG'])
        invalidas = contar_ufs_invalidas(series)
        
        # XX, N/A, None são inválidas = 3
        assert invalidas == 3
    except ImportError:
        pytest.skip("pandas não instalado")


def test_contar_ufs_invalidas_vazio():
    """Testa contagem com Series vazia"""
    try:
        import pandas as pd
        
        series = pd.Series([], dtype='object')
        assert contar_ufs_invalidas(series) == 0
    except ImportError:
        pytest.skip("pandas não instalado")


# ==================== TESTES DE CASOS EXTREMOS ====================

def test_normalizar_uf_caracteres_especiais():
    """Testa UF com caracteres especiais"""
    assert normalizar_uf('S.P') is None
    assert normalizar_uf('S-P') is None
    assert normalizar_uf('S P') is None  # Com espaço no meio


def test_normalizar_uf_numeros():
    """Testa UF com números"""
    assert normalizar_uf('S1') is None
    assert normalizar_uf('12') is None


def test_normalizar_uf_muito_longa():
    """Testa string muito longa"""
    # Tenta mapear nome de estado longo
    assert normalizar_uf('Mato Grosso do Sul') == 'MS'
    assert normalizar_uf('Rio Grande do Norte') == 'RN'


# ==================== TESTES DE INTEGRAÇÃO ====================

def test_pipeline_normalizacao_completa():
    """Testa pipeline completo de normalização"""
    entradas_esperadas = {
        'SP': 'SP',
        'sp': 'SP',
        'São Paulo': 'SP',
        '  RJ  ': 'RJ',
        'n/a': None,
        'XX': None,
        None: None,
    }
    
    for entrada, esperado in entradas_esperadas.items():
        resultado = normalizar_uf(entrada)
        assert resultado == esperado, f"Falha em {entrada}: esperado {esperado}, got {resultado}"


def test_todas_ufs_sao_normalizaveis():
    """Testa que todas as UFs do dicionário são normalizáveis"""
    for uf, nome in UF_NOMES.items():
        # UF deve ser normalizável
        assert normalizar_uf(uf) == uf
        # Nome também deve ser normalizável
        assert normalizar_uf(nome) == uf


# ==================== FIXTURES PARA TESTES DE FILTROS ====================

@pytest.fixture
def df_licitacoes_sample():
    """Fixture com DataFrame de exemplo"""
    try:
        import pandas as pd
        
        data = {
            'uf': ['SP', 'sp', 'São Paulo', 'RJ', 'XX', 'N/A', None, 'MG'],
            'orgao': ['Org A', 'Org B', 'Org C', 'Org D', 'Org E', 'Org F', 'Org G', 'Org H'],
            'valor_estimado': [1000, 5000, 10000, 50000, 100000, 500000, 1000000, 250000],
        }
        
        return pd.DataFrame(data)
    except ImportError:
        pytest.skip("pandas não instalado")


def test_filtro_uf_pandas(df_licitacoes_sample):
    """Testa filtro de UF em DataFrame"""
    try:
        import pandas as pd
        
        # Normalizar UFs
        df = df_licitacoes_sample.copy()
        df['uf'] = df['uf'].apply(normalizar_uf)
        
        # Filtrar por SP (deve encontrar 3)
        resultado = df[df['uf'] == 'SP']
        assert len(resultado) == 3
        
        # Filtrar por RJ (deve encontrar 1)
        resultado = df[df['uf'] == 'RJ']
        assert len(resultado) == 1
        
        # Contar UFs válidas (não None/null)
        ufs_validas = df[df['uf'].notna()]
        assert len(ufs_validas) == 5
    except ImportError:
        pytest.skip("pandas não instalado")


# ==================== MAIN PARA EXECUÇÃO RÁPIDA ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
