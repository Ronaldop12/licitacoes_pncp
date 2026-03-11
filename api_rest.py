"""
API REST — Radar de Licitações de TI
Endpoints para integração com outros sistemas.

Uso:
    uvicorn api_rest:app --host 0.0.0.0 --port 8000

Requer:
    pip install fastapi uvicorn
"""

import os
import re
import json
import hashlib
import logging
import tempfile
import time as _time
from datetime import datetime, timedelta
from typing import Optional, List

import jwt
import pandas as pd
from fastapi import FastAPI, HTTPException, Query, Depends, Security, Request, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import APIKeyHeader

from auth_db import AuthDB
from historico_db import HistoricoDB
from metricas import MetricasDB
from precos_db import PrecosDB
from alerts_db import AlertasDB
from fases_db import FasesDB
from pdf_parser import AnalisesDB, processar_edital_com_cache
from metricas import inicializar_sentry, capturar_excecao, health_check as system_health_check
from crm_db import CrmDB
from search_db import SearchDB
from notificacoes import NotificadorMultiCanal

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Radar Licitações TI — API",
    description="API REST para consulta de licitações de TI do PNCP e fontes complementares.",
    version="1.0.0",
    docs_url=None if os.environ.get("ENV") == "production" else "/docs",
    redoc_url=None if os.environ.get("ENV") == "production" else "/redoc",
)

# --- CORS (restritivo por padrão) ---
_cors_env = os.environ.get("CORS_ORIGINS", "")
if _cors_env:
    _cors_origins = [o.strip() for o in _cors_env.split(",") if o.strip()]
else:
    _cors_origins = ["http://localhost:8501"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "X-API-Key", "Content-Type"],
)

# --- Rate Limiting ---
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded

    _rate_limit = os.environ.get("RATE_LIMIT", "60/minute")
    limiter = Limiter(key_func=get_remote_address, default_limits=[_rate_limit])
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    _RATE_LIMIT_ATIVO = True
except ImportError:
    _RATE_LIMIT_ATIVO = False
    limiter = None

# --- JWT Authentication ---
_JWT_SECRET = os.environ.get("JWT_SECRET", "")
_JWT_ALGORITHM = "HS256"
_JWT_EXPIRE_HOURS = int(os.environ.get("JWT_EXPIRE_HOURS", "24"))

# --- API Key Authentication ---
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
_VALID_API_KEYS: set = set()

def _carregar_api_keys():
    """Carrega API keys válidas do .env (API_KEYS=key1,key2,...)"""
    global _VALID_API_KEYS
    keys_env = os.environ.get("API_KEYS", "")
    if keys_env:
        _VALID_API_KEYS = {k.strip() for k in keys_env.split(",") if k.strip()}

_carregar_api_keys()

# Endpoints públicos (sem auth)
_PUBLIC_PATHS = {"/", "/api/v1/status", "/health"}


@app.middleware("http")
async def autenticar_api_key(request: Request, call_next):
    """Middleware de autenticação via API Key."""
    path = request.url.path
    # Endpoints públicos e docs não precisam de auth
    if path in _PUBLIC_PATHS or path.startswith("/docs") or path.startswith("/redoc") or path.startswith("/openapi"):
        return await call_next(request)

    # Se não há API keys configuradas, aceitar tudo (modo dev)
    if not _VALID_API_KEYS:
        return await call_next(request)

    api_key = request.headers.get("X-API-Key", "")
    if api_key not in _VALID_API_KEYS:
        return JSONResponse(status_code=401, content={"detail": "API key inválida ou ausente"})

    return await call_next(request)


# --- Global exception handler ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Erro não tratado em %s: %s", request.url.path, exc, exc_info=True)
    capturar_excecao(exc, {"path": request.url.path, "method": request.method})
    return JSONResponse(status_code=500, content={"detail": "Erro interno do servidor"})

# --- Inicializar Sentry (se configurado) ---
inicializar_sentry()

CSV_PATH = "dados/licitacoes.csv"
CSV_COMPLEMENTAR = "dados/licitacoes_complementares.csv"
STATE_FILE = "radar_state.json"

db_auth = AuthDB()
db_hist = HistoricoDB()
db_metricas = MetricasDB()
db_precos = PrecosDB()
db_alertas = AlertasDB()
db_fases = FasesDB()
db_analises = AnalisesDB()
db_crm = CrmDB()
db_search = SearchDB()

# --- Notificações multi-canal ---
_notificador = NotificadorMultiCanal()
_slack_url = os.environ.get("SLACK_WEBHOOK_URL", "")
_discord_url = os.environ.get("DISCORD_WEBHOOK_URL", "")
if _slack_url:
    _notificador.adicionar_slack(_slack_url)
if _discord_url:
    _notificador.adicionar_discord(_discord_url)


# --- JWT helpers ---

def _gerar_jwt(usuario: dict) -> str:
    """Gera token JWT para o usuário autenticado."""
    payload = {
        "sub": usuario["username"],
        "papel": usuario.get("papel", "usuario"),
        "uid": usuario.get("id", 0),
        "exp": datetime.utcnow() + timedelta(hours=_JWT_EXPIRE_HOURS),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, _JWT_SECRET, algorithm=_JWT_ALGORITHM)


def _decodificar_jwt(token: str) -> Optional[dict]:
    """Decodifica e valida JWT. Retorna payload ou None."""
    if not _JWT_SECRET:
        return None
    try:
        return jwt.decode(token, _JWT_SECRET, algorithms=[_JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# --- Cache de CSV em memória ---
_csv_cache: dict = {"hash": None, "df": None}

def _carregar_df(caminho: str) -> pd.DataFrame:
    """Carrega CSV com cache baseado em hash do arquivo."""
    if not os.path.exists(caminho):
        return pd.DataFrame()
    try:
        file_hash = hashlib.md5(open(caminho, "rb").read()).hexdigest()
        if caminho == CSV_PATH and _csv_cache["hash"] == file_hash and _csv_cache["df"] is not None:
            return _csv_cache["df"]
        df = pd.read_csv(caminho)
        if 'valor_estimado' in df.columns:
            df['valor_estimado'] = pd.to_numeric(df['valor_estimado'], errors='coerce').fillna(0)
        if caminho == CSV_PATH:
            _csv_cache["hash"] = file_hash
            _csv_cache["df"] = df
        return df
    except Exception:
        return pd.DataFrame()


# ==================== ENDPOINTS ====================

@app.get("/")
def root():
    return {"status": "ok", "servico": "Radar Licitações TI API", "versao": "2.0.0"}


@app.get("/health")
def health():
    """Health check detalhado do sistema."""
    resultado = system_health_check()
    status_code = 200 if resultado["status"] == "healthy" else 503
    return JSONResponse(content=resultado, status_code=status_code)


@app.get("/api/v1/licitacoes")
def listar_licitacoes(
    uf: Optional[str] = Query(None, description="Filtrar por UF (ex: SP)"),
    modalidade: Optional[str] = Query(None, description="Filtrar por modalidade"),
    busca: Optional[str] = Query(None, description="Busca textual no objeto"),
    valor_min: Optional[float] = Query(None, ge=0),
    valor_max: Optional[float] = Query(None, ge=0),
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(50, ge=1, le=500),
):
    """Retorna licitações com filtros e paginação."""
    df = _carregar_df(CSV_PATH)
    if df.empty:
        return {"total": 0, "pagina": pagina, "resultados": []}

    if uf:
        df = df[df['uf'].str.upper() == uf.upper()] if 'uf' in df.columns else df
    if modalidade:
        df = df[df['modalidade'].str.contains(modalidade, case=False, na=False)] if 'modalidade' in df.columns else df
    if busca:
        busca_escaped = re.escape(busca)
        df = df[df['objeto'].str.contains(busca_escaped, case=False, na=False)] if 'objeto' in df.columns else df
    if valor_min is not None and 'valor_estimado' in df.columns:
        df = df[df['valor_estimado'] >= valor_min]
    if valor_max is not None and 'valor_estimado' in df.columns:
        df = df[df['valor_estimado'] <= valor_max]

    total = len(df)
    inicio = (pagina - 1) * por_pagina
    df_pagina = df.iloc[inicio:inicio + por_pagina]

    return {
        "total": total,
        "pagina": pagina,
        "por_pagina": por_pagina,
        "paginas": (total + por_pagina - 1) // por_pagina,
        "resultados": df_pagina.fillna("").to_dict(orient="records"),
    }


@app.get("/api/v1/licitacoes/{numero_edital}")
def obter_licitacao(numero_edital: str):
    """Retorna uma licitação específica pelo número de edital."""
    df = _carregar_df(CSV_PATH)
    if df.empty or 'numero_edital' not in df.columns:
        raise HTTPException(404, "Licitação não encontrada")

    resultado = df[df['numero_edital'].astype(str) == numero_edital]
    if resultado.empty:
        raise HTTPException(404, "Licitação não encontrada")

    return resultado.iloc[0].fillna("").to_dict()


@app.get("/api/v1/estatisticas")
def estatisticas():
    """Retorna estatísticas gerais das licitações."""
    df = _carregar_df(CSV_PATH)
    if df.empty:
        return {"total": 0}

    return {
        "total": len(df),
        "orgaos": int(df['orgao'].nunique()) if 'orgao' in df.columns else 0,
        "ufs": int(df['uf'].nunique()) if 'uf' in df.columns else 0,
        "valor_total": float(df['valor_estimado'].sum()) if 'valor_estimado' in df.columns else 0,
        "valor_medio": float(df['valor_estimado'].mean()) if 'valor_estimado' in df.columns else 0,
        "maior_valor": float(df['valor_estimado'].max()) if 'valor_estimado' in df.columns else 0,
        "modalidades": df['modalidade'].value_counts().to_dict() if 'modalidade' in df.columns else {},
        "top_ufs": df['uf'].value_counts().head(10).to_dict() if 'uf' in df.columns else {},
        "top_orgaos": df['orgao'].value_counts().head(10).to_dict() if 'orgao' in df.columns else {},
    }


@app.get("/api/v1/ufs")
def listar_ufs():
    """Lista UFs disponíveis com totalizadores."""
    df = _carregar_df(CSV_PATH)
    if df.empty or 'uf' not in df.columns:
        return []

    resultado = df.groupby('uf').agg(
        quantidade=('uf', 'size'),
        valor_total=('valor_estimado', 'sum'),
    ).reset_index().sort_values('quantidade', ascending=False)

    return resultado.to_dict(orient="records")


@app.get("/api/v1/historico")
def historico_coletas(limite: int = Query(20, ge=1, le=100)):
    """Retorna histórico de coletas."""
    coletas = db_hist.listar_coletas(limite=limite)
    return {"total": len(coletas), "coletas": coletas}


@app.get("/api/v1/precos/categorias")
def precos_categorias(limite: int = Query(20, ge=1, le=100)):
    """Retorna resumo de preços por categoria CATMAT/CATSER."""
    df = db_precos.resumo_categorias(limite=limite)
    return df.to_dict(orient="records")


@app.get("/api/v1/precos/evolucao/{codigo}")
def precos_evolucao(codigo: str):
    """Retorna evolução de preços para uma categoria."""
    dados = db_precos.evolucao_por_categoria(codigo)
    if dados.empty:
        raise HTTPException(404, "Categoria não encontrada")
    return dados.to_dict(orient="records")


@app.get("/metrics")
def prometheus_metrics():
    """Endpoint Prometheus-compatible para monitoramento."""
    from fastapi.responses import PlainTextResponse
    texto = db_metricas.exportar_prometheus()
    return PlainTextResponse(content=texto, media_type="text/plain; charset=utf-8")


@app.get("/api/v1/metricas")
def metricas_json():
    """Retorna métricas operacionais em JSON."""
    return db_metricas.estatisticas()


@app.get("/api/v1/alertas")
def listar_alertas(ativos: bool = Query(False, description="Apenas alertas ativos")):
    """Lista alertas configurados."""
    alertas = db_alertas.listar_alertas(apenas_ativos=ativos)
    return {"total": len(alertas), "alertas": alertas}


@app.get("/api/v1/alertas/{alerta_id}")
def obter_alerta(alerta_id: int):
    """Retorna detalhes de um alerta específico."""
    alerta = db_alertas.obter_alerta(alerta_id)
    if not alerta:
        raise HTTPException(404, "Alerta não encontrado")
    return alerta


@app.get("/api/v1/alertas/{alerta_id}/historico")
def historico_alerta(alerta_id: int, limite: int = Query(50, ge=1, le=500)):
    """Retorna histórico de envios de um alerta."""
    historico = db_alertas.listar_historico(alerta_id=alerta_id, limite=limite)
    return {"total": len(historico), "historico": historico}


@app.get("/api/v1/fases/mudancas")
def listar_mudancas_fases(
    uf: Optional[str] = Query(None),
    limite: int = Query(50, ge=1, le=500),
):
    """Lista mudanças de status/fase detectadas."""
    mudancas = db_fases.listar_mudancas(limite=limite, uf=uf)
    return {"total": len(mudancas), "mudancas": mudancas}


@app.get("/api/v1/fases/contagem")
def contagem_fases():
    """Retorna contagem de mudanças de fase por tipo."""
    return db_fases.contar_mudancas()


@app.get("/api/v1/fases/{numero_edital}")
def historico_fases_edital(numero_edital: str):
    """Retorna histórico de fases de um edital específico."""
    historico = db_fases.obter_historico_edital(numero_edital)
    if not historico:
        raise HTTPException(404, "Edital não encontrado no histórico de fases")
    return historico


@app.get("/api/v1/calendario.ics")
def calendario_ical(tipo: str = Query("abertura", description="abertura ou encerramento")):
    """Exporta licitações em formato iCalendar (.ics)."""
    from fastapi.responses import Response
    from exportar_ical import gerar_ics
    df = _carregar_df(CSV_PATH)
    if df.empty:
        raise HTTPException(404, "Nenhuma licitação disponível")
    col_data = "data_abertura" if tipo == "abertura" else "data_encerramento"
    conteudo = gerar_ics(df, coluna_data=col_data)
    return Response(
        content=conteudo,
        media_type="text/calendar",
        headers={"Content-Disposition": f"attachment; filename=licitacoes_{tipo}.ics"},
    )


# --- Endpoints de Análise de Editais (PDF) ---

@app.get("/api/v1/editais/analise/{numero_edital}")
def analisar_edital(
    numero_edital: str,
    cnpj: str = Query(..., description="CNPJ do órgão"),
    forcar: bool = Query(False, description="Forçar re-análise"),
):
    """Analisa um edital: baixa PDFs, extrai texto, itens e valores."""
    resultado = processar_edital_com_cache(cnpj, numero_edital, forcar=forcar)
    if not resultado:
        raise HTTPException(404, "Não foi possível processar o edital")
    # Remover texto completo da resposta API (muito grande)
    resultado.pop("texto_completo", None)
    return resultado


@app.get("/api/v1/editais/analises")
def listar_analises_editais(limite: int = Query(50, ge=1, le=200)):
    """Lista editais já analisados."""
    return db_analises.listar_analises(limite=limite)


@app.get("/api/v1/editais/analises/estatisticas")
def estatisticas_analises():
    """Estatísticas de análises de editais."""
    return db_analises.estatisticas()


# --- Endpoints avançados de Preços ---

@app.get("/api/v1/precos/tendencia/{codigo}")
def tendencia_preco(codigo: str):
    """Retorna tendência de preço para uma categoria CATMAT/CATSER."""
    t = db_precos.tendencia_categoria(codigo)
    if not t:
        raise HTTPException(404, "Categoria sem dados suficientes")
    return t


@app.get("/api/v1/precos/comparar/{codigo}")
def comparar_orgaos(codigo: str):
    """Compara preços entre órgãos para uma categoria."""
    df = db_precos.comparar_orgaos_categoria(codigo)
    if df.empty:
        raise HTTPException(404, "Categoria não encontrada")
    return df.to_dict(orient="records")


@app.get("/api/v1/precos/outliers/{codigo}")
def outliers_preco(codigo: str, fator: float = Query(2.0, ge=1.0, le=5.0)):
    """Detecta outliers de preço para uma categoria."""
    df = db_precos.detectar_outliers(codigo, fator=fator)
    return df.to_dict(orient="records") if not df.empty else []


@app.get("/api/v1/precos/ranking")
def ranking_variacoes(limite: int = Query(20, ge=1, le=100)):
    """Ranking de categorias por variação de preço."""
    return db_precos.ranking_categorias_variacao(limite=limite)


@app.get("/api/v1/precos/uf/{codigo}")
def precos_por_uf(codigo: str):
    """Comparação de preços por UF para uma categoria."""
    df = db_precos.evolucao_por_uf(codigo)
    if df.empty:
        raise HTTPException(404, "Categoria não encontrada")
    return df.to_dict(orient="records")


# ── CRM / Pipeline ──────────────────────────────────────────────
@app.post("/api/v1/crm/propostas")
def crm_criar_proposta(dados: dict):
    """Cria uma nova proposta no pipeline."""
    campos_obrigatorios = ["numero_edital", "orgao", "objeto"]
    faltando = [c for c in campos_obrigatorios if c not in dados]
    if faltando:
        raise HTTPException(400, f"Campos obrigatórios ausentes: {faltando}")
    proposta_id = db_crm.criar_proposta(
        numero_edital=dados["numero_edital"],
        orgao=dados["orgao"],
        objeto=dados["objeto"],
        valor_estimado=dados.get("valor_estimado", 0),
        responsavel=dados.get("responsavel", ""),
        notas=dados.get("notas", ""),
    )
    return {"id": proposta_id, "estagio": "prospeccao"}


@app.get("/api/v1/crm/propostas")
def crm_listar_propostas(
    estagio: str = Query(None),
):
    """Lista propostas, opcionalmente filtradas por estágio."""
    return db_crm.listar_pipeline(estagio=estagio)


@app.get("/api/v1/crm/propostas/{proposta_id}")
def crm_detalhe_proposta(proposta_id: int):
    """Retorna detalhes de uma proposta + histórico + tarefas."""
    proposta = db_crm.obter_proposta(proposta_id)
    if not proposta:
        raise HTTPException(404, "Proposta não encontrada")
    return {
        **proposta,
        "historico": db_crm.historico_proposta(proposta_id),
        "tarefas": db_crm.listar_tarefas(proposta_id),
    }


@app.put("/api/v1/crm/propostas/{proposta_id}/estagio")
def crm_atualizar_estagio(proposta_id: int, dados: dict):
    """Move proposta para novo estágio do pipeline."""
    if "estagio" not in dados:
        raise HTTPException(400, "Campo 'estagio' é obrigatório")
    ok = db_crm.mover_estagio(
        proposta_id,
        dados["estagio"],
        usuario=dados.get("usuario", "api"),
        observacao=dados.get("observacao", ""),
    )
    if not ok:
        raise HTTPException(400, "Não foi possível mover para esse estágio")
    return {"ok": True, "estagio": dados["estagio"]}


@app.put("/api/v1/crm/propostas/{proposta_id}")
def crm_atualizar_proposta(proposta_id: int, dados: dict):
    """Atualiza campos da proposta (valor_estimado, responsavel, notas)."""
    campos_permitidos = {"valor_estimado", "responsavel", "notas"}
    atualizacoes = {k: v for k, v in dados.items() if k in campos_permitidos}
    if not atualizacoes:
        raise HTTPException(400, f"Nenhum campo válido para atualizar. Permitidos: {campos_permitidos}")
    db_crm.atualizar_proposta(proposta_id, **atualizacoes)
    return {"ok": True}


@app.get("/api/v1/crm/pipeline")
def crm_pipeline():
    """Visão geral do pipeline por estágio."""
    return db_crm.pipeline_resumo()


@app.get("/api/v1/crm/conversao")
def crm_taxa_conversao():
    """Taxa de conversão do pipeline."""
    return db_crm.taxa_conversao()


@app.post("/api/v1/crm/propostas/{proposta_id}/tarefas")
def crm_criar_tarefa(proposta_id: int, dados: dict):
    """Cria tarefa associada a uma proposta."""
    if "descricao" not in dados:
        raise HTTPException(400, "Campo 'descricao' é obrigatório")
    tarefa_id = db_crm.adicionar_tarefa(
        proposta_id=proposta_id,
        descricao=dados["descricao"],
        responsavel=dados.get("responsavel", ""),
        prazo=dados.get("prazo", ""),
    )
    return {"id": tarefa_id}


@app.put("/api/v1/crm/tarefas/{tarefa_id}/concluir")
def crm_concluir_tarefa(tarefa_id: int):
    """Marca tarefa como concluída."""
    db_crm.concluir_tarefa(tarefa_id)
    return {"ok": True}


# ── JWT Authentication ──────────────────────────────────────────
@app.post("/api/v1/auth/login")
def auth_login(dados: dict = Body(...)):
    """Autentica usuário e retorna JWT token."""
    username = dados.get("username", "")
    senha = dados.get("senha", "")
    if not username or not senha:
        raise HTTPException(400, "username e senha são obrigatórios")
    usuario = db_auth.autenticar(username, senha)
    if not usuario:
        raise HTTPException(401, "Credenciais inválidas")
    if not _JWT_SECRET:
        raise HTTPException(503, "JWT não configurado (defina JWT_SECRET no .env)")
    token = _gerar_jwt(usuario)
    return {
        "token": token,
        "tipo": "Bearer",
        "expira_em": _JWT_EXPIRE_HOURS * 3600,
        "usuario": {
            "username": usuario["username"],
            "nome": usuario.get("nome", ""),
            "papel": usuario.get("papel", "usuario"),
        },
    }


@app.get("/api/v1/auth/me")
def auth_me(request: Request):
    """Retorna dados do usuário autenticado via JWT."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(401, "Token não fornecido. Use: Authorization: Bearer <token>")
    token = auth_header[7:]
    payload = _decodificar_jwt(token)
    if not payload:
        raise HTTPException(401, "Token inválido ou expirado")
    return {
        "username": payload["sub"],
        "papel": payload.get("papel", "usuario"),
        "uid": payload.get("uid"),
    }


# ── Full-text Search (FTS5) ────────────────────────────────────
@app.get("/api/v1/busca")
def busca_fulltext(
    q: str = Query(..., min_length=2, description="Termos de busca"),
    uf: Optional[str] = Query(None),
    limite: int = Query(50, ge=1, le=200),
):
    """Busca full-text com ranking de relevância (FTS5)."""
    # Auto-indexar se necessário
    info = db_search.info()
    if not info.get("total_indexados"):
        db_search.indexar_csv(CSV_PATH)
    resultados = db_search.buscar(q, limite=limite, uf=uf)
    return {"total": len(resultados), "consulta": q, "resultados": resultados}


@app.get("/api/v1/busca/sugerir")
def busca_sugerir(
    prefixo: str = Query(..., min_length=2, description="Prefixo para auto-complete"),
):
    """Auto-complete baseado em prefixo (FTS5 wildcard)."""
    return db_search.sugerir(prefixo)


@app.post("/api/v1/busca/reindexar")
def busca_reindexar():
    """Força re-indexação do CSV no motor de busca FTS5."""
    resultado = db_search.indexar_csv(CSV_PATH, forcar=True)
    return resultado


# ── Exportação XLSX ─────────────────────────────────────────────
@app.get("/api/v1/exportar/xlsx")
def exportar_xlsx(
    uf: Optional[str] = Query(None),
    busca: Optional[str] = Query(None),
    valor_min: Optional[float] = Query(None, ge=0),
    valor_max: Optional[float] = Query(None, ge=0),
):
    """Exporta licitações filtradas em formato Excel (.xlsx)."""
    import io
    df = _carregar_df(CSV_PATH)
    if df.empty:
        raise HTTPException(404, "Nenhuma licitação disponível")

    if uf and 'uf' in df.columns:
        df = df[df['uf'].str.upper() == uf.upper()]
    if busca and 'objeto' in df.columns:
        busca_escaped = re.escape(busca)
        df = df[df['objeto'].str.contains(busca_escaped, case=False, na=False)]
    if valor_min is not None and 'valor_estimado' in df.columns:
        df = df[df['valor_estimado'] >= valor_min]
    if valor_max is not None and 'valor_estimado' in df.columns:
        df = df[df['valor_estimado'] <= valor_max]

    if df.empty:
        raise HTTPException(404, "Nenhuma licitação com os filtros aplicados")

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Licitacoes")
    buffer.seek(0)

    nome = f"licitacoes_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={nome}"},
    )


# ── Notificações multi-canal ───────────────────────────────────
@app.get("/api/v1/notificacoes/status")
def notificacoes_status():
    """Retorna status dos canais de notificação configurados."""
    return {
        "total_canais": _notificador.total_canais,
        "slack": bool(_slack_url),
        "discord": bool(_discord_url),
        "telegram": bool(os.environ.get("TELEGRAM_TOKEN")),
    }


@app.post("/api/v1/notificacoes/teste")
def notificacoes_teste():
    """Envia mensagem de teste para todos os canais configurados."""
    if _notificador.total_canais == 0:
        raise HTTPException(400, "Nenhum canal configurado. Defina SLACK_WEBHOOK_URL ou DISCORD_WEBHOOK_URL.")
    resultados = {}
    for canal in _notificador.canais:
        nome = type(canal).__name__
        resultados[nome] = canal.enviar(f"🧪 Teste do Radar Licitações TI — {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    return {"resultados": resultados}


@app.get("/api/v1/status")
def status_sistema():
    """Retorna status atual do sistema."""
    estado = None
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                estado = json.load(f)
        except Exception:
            pass

    return {
        "online": True,
        "dados_disponiveis": os.path.exists(CSV_PATH),
        "ultima_coleta": estado,
        "timestamp": datetime.now().isoformat(),
    }
