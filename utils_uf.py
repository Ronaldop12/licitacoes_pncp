"""
========================================
UTILITÁRIOS DE VALIDAÇÃO DE UF E DADOS
========================================
Funções para validar e normalizar Estados (UF) e outros dados.
"""

# Lista oficial de UFs brasileiros
UFS_VALIDAS = {
    'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
    'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
    'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
}

UF_NOMES = {
    'AC': 'Acre',
    'AL': 'Alagoas',
    'AP': 'Amapá',
    'AM': 'Amazonas',
    'BA': 'Bahia',
    'CE': 'Ceará',
    'DF': 'Distrito Federal',
    'ES': 'Espírito Santo',
    'GO': 'Goiás',
    'MA': 'Maranhão',
    'MT': 'Mato Grosso',
    'MS': 'Mato Grosso do Sul',
    'MG': 'Minas Gerais',
    'PA': 'Pará',
    'PB': 'Paraíba',
    'PR': 'Paraná',
    'PE': 'Pernambuco',
    'PI': 'Piauí',
    'RJ': 'Rio de Janeiro',
    'RN': 'Rio Grande do Norte',
    'RS': 'Rio Grande do Sul',
    'RO': 'Rondônia',
    'RR': 'Roraima',
    'SC': 'Santa Catarina',
    'SP': 'São Paulo',
    'SE': 'Sergipe',
    'TO': 'Tocantins'
}


def normalizar_uf(uf_valor):
    """
    Normaliza um valor de UF para formato padrão (2 letras maiúsculas)
    
    Args:
        uf_valor: Valor a normalizar (string ou None)
        
    Returns:
        UF normalizada (ex: 'SP') ou None se inválida
        
    Exemplos:
        normalizar_uf('sp') → 'SP'
        normalizar_uf('SAO PAULO') → 'SP'
        normalizar_uf('N/A') → None
        normalizar_uf(None) → None
        normalizar_uf('XX') → None (inválido)
    """
    if uf_valor is None:
        return None
    
    uf_str = str(uf_valor).strip().upper()
    
    # Valores inválidos
    if not uf_str or uf_str in ('N/A', 'NAN', 'NONE', 'NULL', ''):
        return None
    
    # Já é UF válida (2 letras)
    if len(uf_str) == 2 and uf_str in UFS_VALIDAS:
        return uf_str
    
    # Tentar mapear nome do estado para UF (exato primeiro)
    for uf, nome in UF_NOMES.items():
        if nome.upper() == uf_str:
            return uf
    
    # Se não encontrou exato, tentar por prefixo/contains (para "São Paulo" → "SP")
    for uf, nome in UF_NOMES.items():
        if uf_str in nome.upper():
            return uf
    
    # Não conseguiu mapear
    return None


def eh_uf_valida(uf_valor):
    """
    Verifica se uma UF é válida
    
    Args:
        uf_valor: Valor a verificar
        
    Returns:
        True se é UF válida, False caso contrário
    """
    uf_norm = normalizar_uf(uf_valor)
    return uf_norm is not None


def obter_nome_estado(uf):
    """
    Obtém nome completo do estado
    
    Args:
        uf: Sigla do estado (ex: 'SP')
        
    Returns:
        Nome completo (ex: 'São Paulo') ou None se inválido
    """
    uf_norm = normalizar_uf(uf)
    if uf_norm:
        return UF_NOMES.get(uf_norm)
    return None


def listar_ufs_validas():
    """Retorna lista de UFs válidas"""
    return sorted(list(UFS_VALIDAS))


def listar_ufs_com_nomes():
    """Retorna dicionário com UF → Nome"""
    return {k: UF_NOMES[k] for k in sorted(UF_NOMES.keys())}


def validar_lista_ufs(lista_ufs):
    """
    Valida lista de UFs
    
    Args:
        lista_ufs: Lista de UFs
        
    Returns:
        Lista contendo apenas UFs válidas e normalizadas
    """
    ufs_validas = []
    for uf in lista_ufs:
        uf_norm = normalizar_uf(uf)
        if uf_norm and uf_norm not in ufs_validas:
            ufs_validas.append(uf_norm)
    return sorted(ufs_validas)


def contar_ufs_invalidas(series_uf):
    """
    Conta quantas UFs inválidas existem em um Series do Pandas
    
    Args:
        series_uf: pandas.Series com valores de UF
        
    Returns:
        Número de UFs inválidas/vazias
    """
    import pandas as pd
    
    if series_uf is None or len(series_uf) == 0:
        return 0
    
    invalidas = 0
    for valor in series_uf:
        if not eh_uf_valida(valor):
            invalidas += 1
    return invalidas


if __name__ == "__main__":
    # Testes rápidos
    print("=== TESTES DE UF ===\n")
    
    testes = [
        'SP',
        'sp',
        'São Paulo',
        'N/A',
        'XX',
        None,
        'RJ rio',
        ''
    ]
    
    for teste in testes:
        resultado = normalizar_uf(teste)
        valido = eh_uf_valida(teste)
        print(f"{str(teste):20} → {str(resultado):5} (válido: {valido})")
