"""
Coletor assíncrono para a API PNCP.
Paraleliza a coleta das 13 modalidades usando asyncio + aiohttp.
Suporte a coleta por faixas de data, métricas integradas e resumo detalhado.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable

logger = logging.getLogger(__name__)

try:
    import aiohttp
    AIOHTTP_DISPONIVEL = True
except ImportError:
    AIOHTTP_DISPONIVEL = False
    logger.warning("aiohttp não instalado. Coleta assíncrona indisponível. pip install aiohttp")

API_URL = "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao"
MAX_LICITACOES = 20000
TIMEOUT = 120
MAX_TENTATIVAS = 3
CONCORRENCIA_MAX = 5  # requisições simultâneas (balanceado para rate limit)
CONCORRENCIA_POR_MODALIDADE = 2  # faixas de data simultâneas por modalidade

# Mesmas palavras-chave do coletor síncrono
from constantes import PALAVRAS_TI, PALAVRAS_EXCLUSAO


def _eh_ti(texto: str) -> bool:
    if not texto:
        return False
    t = texto.lower()
    for exc in PALAVRAS_EXCLUSAO:
        if exc in t:
            return False
    for p in PALAVRAS_TI:
        if p in t:
            return True
    return False


def _processar_item(item: Dict) -> Optional[Dict]:
    """Processa um item da API em registro padronizado."""
    try:
        objeto = item.get("objetoCompra", "")
        if not _eh_ti(objeto):
            return None

        orgao_entidade = item.get("orgaoEntidade", {})
        unidade_orgao = item.get("unidadeOrgao", {})

        nome_orgao = orgao_entidade.get("razaoSocial", "N/A") if isinstance(orgao_entidade, dict) else str(orgao_entidade)
        uf = unidade_orgao.get("ufSigla", "N/A") if isinstance(unidade_orgao, dict) else "N/A"
        municipio = unidade_orgao.get("municipioNome", "N/A") if isinstance(unidade_orgao, dict) else "N/A"
        cnpj = orgao_entidade.get("cnpj", "") if isinstance(orgao_entidade, dict) else ""

        numero_controle = item.get("numeroControlePNCP", "N/A")
        link = f"https://pncp.gov.br/app/editais/{numero_controle}" if numero_controle and numero_controle != "N/A" else ""

        return {
            "orgao": nome_orgao,
            "cnpj_orgao": cnpj,
            "objeto": objeto,
            "valor_estimado": item.get("valorTotalEstimado", 0),
            "data_publicacao": item.get("dataPublicacaoPncp", "N/A"),
            "data_abertura": item.get("dataAberturaProposta", "N/A"),
            "data_encerramento": item.get("dataEncerramentoProposta", "N/A"),
            "uf": uf,
            "municipio": municipio,
            "numero_edital": numero_controle,
            "modalidade": item.get("modalidadeNome", "N/A"),
            "status": item.get("situacaoCompraNome", "N/A"),
            "criterio_julgamento": item.get("tipoCriterioJulgamentoNome", "N/A"),
            "link_edital": link,
            "fonte": "PNCP",
            "categoria_item": item.get("categoriaNome", "N/A"),
            "codigo_catmat_catser": item.get("codigoClasseItemMaterial",
                                             item.get("codigoGrupoMaterial", "N/A")),
        }
    except Exception as e:
        logger.warning("Erro ao processar item: %s", e)
        return None


async def _coletar_modalidade(
    session: "aiohttp.ClientSession",
    semaforo: asyncio.Semaphore,
    modalidade: int,
    data_inicio: str,
    data_final: str,
    editais_vistos: set,
) -> List[Dict]:
    """Coleta todas as páginas de uma modalidade."""
    resultados = []
    pagina = 1
    paginas_vazias = 0

    while len(resultados) < MAX_LICITACOES and paginas_vazias < 3:
        params = {
            "dataInicial": data_inicio,
            "dataFinal": data_final,
            "codigoModalidadeContratacao": modalidade,
            "pagina": pagina,
        }

        dados_pagina = None
        for tentativa in range(MAX_TENTATIVAS):
            try:
                async with semaforo:
                    async with session.get(API_URL, params=params, timeout=aiohttp.ClientTimeout(total=TIMEOUT)) as resp:
                        if resp.status == 200:
                            dados_pagina = await resp.json()
                            break
                        if resp.status == 204:
                            return resultados
                        if resp.status == 500:
                            await asyncio.sleep(3 * (tentativa + 1))
                            continue
                        logger.warning("Modalidade %d p%d: HTTP %d", modalidade, pagina, resp.status)
                        return resultados
            except (asyncio.TimeoutError, aiohttp.ClientError) as e:
                logger.warning("Modalidade %d p%d tentativa %d: %s", modalidade, pagina, tentativa + 1, e)
                await asyncio.sleep(2)

        if dados_pagina is None:
            break

        itens = dados_pagina.get("data", [])
        if not itens:
            paginas_vazias += 1
            if paginas_vazias >= 3:
                break
            pagina += 1
            await asyncio.sleep(1)
            continue

        paginas_vazias = 0
        for item in itens:
            ne = item.get("numeroControlePNCP", "")
            if ne in editais_vistos:
                continue
            reg = _processar_item(item)
            if reg:
                resultados.append(reg)
                editais_vistos.add(ne)

        pagina += 1
        await asyncio.sleep(1)  # respeitar rate limit

    logger.info("Modalidade %d: %d licitações TI", modalidade, len(resultados))
    return resultados


async def coletar_async(
    dias_atras: int = 15,
    concorrencia: int = CONCORRENCIA_MAX,
    callback_progresso: Optional[Callable] = None,
) -> Dict:
    """
    Coleta assíncrona de todas as 13 modalidades em paralelo (com semáforo).
    Divide período em faixas de 5 dias para paralelizar ainda mais.

    Args:
        dias_atras: Quantos dias para trás coletar.
        concorrencia: Máximo de requisições simultâneas.
        callback_progresso: Função chamada a cada modalidade concluída (modal, qtd).

    Returns:
        Dicionário com resultados e métricas detalhadas por modalidade.
    """
    if not AIOHTTP_DISPONIVEL:
        raise ImportError("aiohttp é necessário para coleta assíncrona. pip install aiohttp")

    data_fim = datetime.now()
    data_inicio = data_fim - timedelta(days=dias_atras)

    # Dividir período em faixas de 5 dias para coletas longas
    faixas = []
    if dias_atras > 7:
        d = data_inicio
        while d < data_fim:
            fim_faixa = min(d + timedelta(days=5), data_fim)
            faixas.append((d.strftime("%Y%m%d"), fim_faixa.strftime("%Y%m%d")))
            d = fim_faixa
    else:
        faixas.append((data_inicio.strftime("%Y%m%d"), data_fim.strftime("%Y%m%d")))

    modalidades = list(range(1, 14))
    editais_vistos: set = set()
    semaforo = asyncio.Semaphore(concorrencia)
    metricas_por_modalidade: Dict[int, Dict] = {}

    logger.info(
        "Coleta assíncrona: %d modalidades × %d faixa(s), período %s a %s, concorrência=%d",
        len(modalidades), len(faixas),
        data_inicio.strftime("%Y-%m-%d"), data_fim.strftime("%Y-%m-%d"),
        concorrencia,
    )
    inicio = time.time()

    connector = aiohttp.TCPConnector(limit=concorrencia, limit_per_host=concorrencia)
    timeout_cfg = aiohttp.ClientTimeout(total=TIMEOUT, connect=30)

    async with aiohttp.ClientSession(
        connector=connector,
        timeout=timeout_cfg,
        headers={"Accept": "application/json", "User-Agent": "RadarLicitacoesTI/2.0-async"},
    ) as session:
        tarefas = []
        for m in modalidades:
            for di, df in faixas:
                tarefas.append(
                    _coletar_modalidade(session, semaforo, m, di, df, editais_vistos)
                )
        resultados_brutos = await asyncio.gather(*tarefas, return_exceptions=True)

    todos = []
    erros_total = 0
    for i, r in enumerate(resultados_brutos):
        modal = modalidades[i % len(modalidades)] if i < len(resultados_brutos) else 0
        if isinstance(r, Exception):
            logger.error("Erro em modalidade %d: %s", modal, r)
            erros_total += 1
            continue
        todos.extend(r)

    # Construir métricas por modalidade
    _contagem_modal: Dict[int, int] = {}
    for item in todos:
        m = item.get("modalidade", "N/A")
        _contagem_modal[m] = _contagem_modal.get(m, 0) + 1

    duracao = time.time() - inicio

    resumo = {
        "licitacoes": todos,
        "total": len(todos),
        "duracao_segundos": round(duracao, 1),
        "modalidades_coletadas": len(modalidades),
        "faixas_paralelas": len(faixas),
        "erros": erros_total,
        "por_modalidade": _contagem_modal,
        "editais_unicos": len(editais_vistos),
        "periodo": {
            "inicio": data_inicio.strftime("%Y-%m-%d"),
            "fim": data_fim.strftime("%Y-%m-%d"),
            "dias": dias_atras,
        },
    }

    logger.info(
        "Coleta assíncrona concluída: %d licitações TI em %.1fs (%d erros, %d faixas paralelas)",
        len(todos), duracao, erros_total, len(faixas),
    )

    if callback_progresso:
        callback_progresso(resumo)

    return resumo


def coletar_sincrono_wrapper(dias_atras: int = 15) -> List[Dict]:
    """Wrapper síncrono para a coleta assíncrona (para uso em scripts convencionais)."""
    resultado = asyncio.run(coletar_async(dias_atras))
    return resultado.get("licitacoes", resultado) if isinstance(resultado, dict) else resultado
