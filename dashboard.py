"""
========================================
DASHBOARD INTERATIVO RADAR DE LICITAÇÕES TI
========================================
Dashboard web para visualização de licitações de TI

Uso:
    streamlit run dashboard.py

Requisitos:
- streamlit
- pandas
- plotly
- openpyxl
========================================
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import re
from datetime import datetime
import json
import hashlib
from dotenv import load_dotenv
from utils_uf import normalizar_uf, eh_uf_valida, listar_ufs_validas, obter_nome_estado, UF_NOMES, contar_ufs_invalidas
from alerts_db import AlertasDB
from auth_db import AuthDB
from utils_telegram import TelegramAlerter, validar_token, validar_chat_id
from coletor_fontes_complementares import (
    ColetorMultiFontes, carregar_chave_transparencia, salvar_chave_transparencia,
    OUTPUT_COMPLEMENTAR, STATE_FILE_COMPLEMENTAR,
    OUTPUT_QUERIDO_DIARIO, OUTPUT_TRANSPARENCIA, OUTPUT_COMPRAS_GOV,
)
from exportar_ical import gerar_ics
from historico_db import HistoricoDB
from fases_db import FasesDB
from precos_db import PrecosDB
from metricas import MetricasDB
from pdf_parser import processar_edital_completo, processar_edital_com_cache, AnalisesDB
from agendador import AgendadorTarefas
from crm_db import CrmDB

# Carregar variáveis de ambiente
load_dotenv()

# ==================== VALIDAÇÃO DE SEGURANÇA ====================

_cookie_key = os.environ.get("COOKIE_KEY", "")
if os.environ.get("ENV") == "production" and _cookie_key in ("", "chave-secreta-alterar-em-producao"):
    raise SystemExit("ERRO: COOKIE_KEY não configurada. Defina uma chave segura no .env antes de iniciar em produção.")

# ==================== CONFIGURAÇÕES ====================

PAGE_TITLE = "Radar de Licitações de TI"
PAGE_ICON = "📡"
# Tentar múltiplos caminhos de dados
CSV_PATH = "licitacoes_TI.csv"  # Arquivo principal
CSV_PATH_ALT = "dados/licitacoes.csv"  # Caminho alternativo
EXCEL_PATH = "radar_licitacoes_TI_PRO.xlsx"
STATE_FILE = "radar_state.json"

# Configurar página
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CSS CUSTOMIZADO ====================

st.markdown("""
<style>
    [data-testid="stMetricValue"] {
        font-size: 24px;
    }
    
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    
    .favorito-btn {
        cursor: pointer;
        font-size: 1.2em;
    }
</style>
""", unsafe_allow_html=True)

# ==================== SISTEMA DE LOGIN ====================

db_auth = AuthDB()

def tela_login():
    """Exibe a tela de login/registro."""
    st.markdown("# 📡 Radar de Licitações de TI")
    st.markdown("### Acesso ao Sistema")
    
    tab_login, tab_registro = st.tabs(["🔑 Login", "📝 Registrar"])
    
    with tab_login:
        with st.form("form_login"):
            username = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            submitted = st.form_submit_button("Entrar", use_container_width=True)
            
            if submitted:
                if username and senha:
                    usuario = db_auth.autenticar(username, senha)
                    if usuario:
                        st.session_state['usuario'] = {
                            'id': usuario['id'],
                            'username': usuario['username'],
                            'nome': usuario['nome'],
                            'papel': usuario['papel'],
                        }
                        st.session_state['logado'] = True
                        st.rerun()
                    else:
                        st.error("Usuário ou senha inválidos")
                else:
                    st.warning("Preencha todos os campos")
        
        st.caption("Primeiro acesso? Verifique dados/.admin_senha_inicial ou configure ADMIN_PASSWORD_HASH no .env")
    
    with tab_registro:
        with st.form("form_registro"):
            novo_user = st.text_input("Nome de usuário")
            novo_nome = st.text_input("Nome completo")
            novo_email = st.text_input("Email")
            nova_senha = st.text_input("Senha", type="password", key="reg_senha")
            confirma_senha = st.text_input("Confirmar senha", type="password")
            reg_submitted = st.form_submit_button("Registrar", use_container_width=True)
            
            if reg_submitted:
                if not novo_user or not nova_senha:
                    st.warning("Usuário e senha são obrigatórios")
                elif nova_senha != confirma_senha:
                    st.error("Senhas não conferem")
                elif len(nova_senha) < 6:
                    st.error("Senha deve ter no mínimo 6 caracteres")
                else:
                    if db_auth.criar_usuario(novo_user, nova_senha, nome=novo_nome, email=novo_email):
                        st.success("Conta criada! Faça login.")
                    else:
                        st.error("Usuário já existe")

# Verificar se está logado
if not st.session_state.get('logado', False):
    tela_login()
    st.stop()

# A partir daqui, o usuário está autenticado
usuario_logado = st.session_state['usuario']

# Helper de permissão
def tem_perm(permissao: str) -> bool:
    return AuthDB.tem_permissao(usuario_logado.get('papel', 'viewer'), permissao)

# ==================== FUNÇÕES DE CARREGAMENTO ====================

def _get_csv_hash():
    """Gera hash do arquivo CSV para invalidar cache quando dados mudam"""
    if os.path.exists(CSV_PATH_ALT):
        stat = os.stat(CSV_PATH_ALT)
        return f"alt_{stat.st_mtime}"
    if os.path.exists(CSV_PATH):
        stat = os.stat(CSV_PATH)
        return f"main_{stat.st_mtime}"
    return "empty"

@st.cache_data(hash_funcs={_get_csv_hash: str}, ttl=300)  # 5 minutos TTL + hash-based invalidation
def carregar_dados():
    """Carrega dados do CSV ou XLSX"""
    # Invalidar cache ao detectar mudanças no arquivo
    _ = _get_csv_hash()
    
    # Preferir CSV alternativo em dados/ quando existir
    def _post_process(df):
        if 'data_publicacao' in df.columns:
            df['data_publicacao'] = pd.to_datetime(df['data_publicacao'], errors='coerce')
        if 'valor_estimado' in df.columns:
            df['valor_estimado'] = pd.to_numeric(df['valor_estimado'], errors='coerce').fillna(0)
        return df

    # 1) tentar caminho alternativo (mais provável conter colunas completas)
    if os.path.exists(CSV_PATH_ALT):
        try:
            df_alt = pd.read_csv(CSV_PATH_ALT)
            df_alt = _post_process(df_alt)
            # Se o alternativo tiver coluna 'uf', é preferível
            if 'uf' in df_alt.columns and len(df_alt) > 0:
                return df_alt
        except Exception:
            pass

    # 2) tentar CSV principal
    if os.path.exists(CSV_PATH):
        try:
            df = pd.read_csv(CSV_PATH)
            df = _post_process(df)
            # Se arquivo principal estiver completo (contiver 'uf'), use-o
            if 'uf' in df.columns and len(df) > 0:
                return df
            # caso contrário, se houver df_alt carregado anteriormente use-o
            if 'df_alt' in locals() and isinstance(df_alt, pd.DataFrame) and len(df_alt) > 0:
                return df_alt
            return df
        except Exception as e:
            st.error(f"Erro ao carregar {CSV_PATH}: {e}")
            # fallback para alternativo se existir
            if 'df_alt' in locals() and isinstance(df_alt, pd.DataFrame):
                return df_alt
            return pd.DataFrame()

    # 3) tentar Excel se nenhum CSV disponível
    if os.path.exists(EXCEL_PATH):
        try:
            df = pd.read_excel(EXCEL_PATH)
            df = _post_process(df)
            return df
        except Exception:
            return pd.DataFrame()

    # nada encontrado
    return pd.DataFrame()


@st.cache_data
def carregar_estado():
    """Carrega Estado da execução"""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None
    return None


def formatar_moeda(valor):
    """Formata valor como moeda"""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def formatar_numero(valor):
    """Formata número com separador de milhares"""
    return f"{valor:,.0f}".replace(",", ".")


def gerar_link_edital(numero_edital):
    """Gera link para edital no PNCP portal"""
    if pd.isna(numero_edital) or numero_edital == 0 or numero_edital == '':
        return 'https://www.pncp.gov.br'
    return f'https://www.pncp.gov.br/app/editais?numero={str(numero_edital).replace(".", "").replace("/", "-")}'


def gerar_link_pdf_edital(cnpj_orgao, numero_edital_seq):
    """Gera link direto para download do PDF do edital via API PNCP."""
    if not cnpj_orgao or pd.isna(cnpj_orgao) or cnpj_orgao == 'N/A':
        return None
    if not numero_edital_seq or pd.isna(numero_edital_seq) or numero_edital_seq == 'N/A':
        return None
    cnpj_limpo = str(cnpj_orgao).replace('.', '').replace('/', '').replace('-', '').strip()
    seq_limpo = str(numero_edital_seq).replace('/', '-').strip()
    return f"https://pncp.gov.br/api/pncp/v1/orgaos/{cnpj_limpo}/compras/{seq_limpo}/arquivos"


def normalizar_dataframe(df):
    """
    Garante que o DataFrame tem todas as colunas necessárias
    Cria colunas vazias se não existirem (NÃO substitui dados existentes)
    Normaliza valores de UF para padrão ABNT
    """
    colunas_obrigatorias = {
        'orgao': 'N/A',
        'cnpj_orgao': 'N/A',
        'objeto': 'N/A',
        'valor_estimado': 0,
        'data_publicacao': 'N/A',
        'data_abertura': 'N/A',
        'data_encerramento': 'N/A',
        'uf': 'N/A',
        'municipio': 'N/A',
        'numero_edital': 'N/A',
        'modalidade': 'N/A',
        'status': 'N/A',
        'criterio_julgamento': 'N/A',
        'link_edital': '',
        'fonte': 'PNCP',
        'categoria_item': 'N/A',
        'codigo_catmat_catser': 'N/A',
    }
    
    # APENAS CRIAR COLUNAS QUE NÃO EXISTEM (não sobrescrever existentes)
    for coluna, valor_padrao in colunas_obrigatorias.items():
        if coluna not in df.columns:
            df[coluna] = valor_padrao
        elif coluna == 'valor_estimado':
            # Apenas converter para numérico, não substituir com 0
            df[coluna] = pd.to_numeric(df[coluna], errors='coerce').fillna(0)
        elif coluna == 'data_publicacao':
            # Apenas converter para datetime
            df[coluna] = pd.to_datetime(df[coluna], errors='coerce')
        elif coluna == 'uf':
            # NORMALIZAR UFs: aplicar função de normalização
            df[coluna] = df[coluna].apply(lambda x: normalizar_uf(x) if pd.notna(x) else 'N/A')
    
    return df


# ==================== TÍTULO E HEADER ====================

col_titulo, col_user = st.columns([4, 1])
with col_titulo:
    st.markdown("# 📡 Radar de Licitações de TI")
    st.markdown("### Portal Nacional de Contratações Públicas (PNCP)")
with col_user:
    st.markdown(f"**👤 {usuario_logado['nome'] or usuario_logado['username']}**")
    st.caption(f"Perfil: {usuario_logado['papel']}")
    if st.button("🚪 Sair", key="btn_logout"):
        st.session_state.clear()
        st.rerun()

# Info sobre última atualização
estado = carregar_estado()
if estado:
    col1, col2, col3 = st.columns(3)
    with col1:
        # Usar data atual se não houver data_execucao no arquivo de estado
        data_exec = estado.get('data_execucao', datetime.now().isoformat())
        if 'T' in data_exec:
            data_formatada = data_exec.split('T')[0]
        else:
            data_formatada = data_exec
        st.metric("Última atualização", data_formatada)
    with col2:
        total_ti = estado.get('total_ti', 0)
        st.metric("Licitações encontradas", formatar_numero(total_ti))
    with col3:
        total_lic = estado.get('total_licitacoes', 0)
        st.metric("Total verificado", formatar_numero(total_lic))

# ==================== CARREGAR DADOS ====================

st.divider()

df = carregar_dados()

# Normalizar DataFrame para garantir todas as colunas
df = normalizar_dataframe(df)

if df.empty:
    st.error("❌ Nenhum dado disponível. Por favor, execute o script de coleta primeiro.")
    st.info("Execute em terminal: `python pncp_radar_ti_plus.py`")
    st.stop()

# ==================== BARRA LATERAL (FILTROS) ====================

st.sidebar.markdown("## 🔍 FILTROS")

# Preparar listas de opções dos filtros - com tratamento robusto de dados vazios
# Estados (UF)
def normalizar_lista_ufs(series_uf):
    """Normaliza e valida lista de UFs do DataFrame"""
    ufs_normalizadas = {}  # dict para evitar duplicatas e manter ordem por frequência
    for uf_bruto in series_uf.dropna().unique():
        uf_norm = normalizar_uf(uf_bruto)
        if uf_norm:
            ufs_normalizadas[uf_norm] = UF_NOMES.get(uf_norm, uf_norm)
    return ufs_normalizadas

ufs_dict = normalizar_lista_ufs(df['uf'])
ufs_lista = sorted(ufs_dict.keys())
ufs_invalidas_count = contar_ufs_invalidas(df['uf'])

# ===== DEBUG & RELOAD =====
with st.sidebar.expander("🔧 Debug & Reload"):
    col_debug1, col_debug2 = st.columns(2)
    with col_debug1:
        if st.button("🔄 Forçar Reload", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    with col_debug2:
        if st.button("🗑️ Limpar Cache", use_container_width=True):
            st.cache_data.clear()
            st.session_state.clear()
    
    # Informação sobre arquivo carregado
    if os.path.exists(CSV_PATH_ALT):
        st.info(f"📂 Carregando: `dados/licitacoes.csv` ({len(df)} linhas)")
    elif os.path.exists(CSV_PATH):
        st.info(f"📂 Carregando: `licitacoes_TI.csv` ({len(df)} linhas)")
    else:
        st.warning("Nenhum arquivo de dados encontrado")
    
    st.caption(f"Total UFs encontrados: **{len(ufs_dict)} de 27**")
    st.divider()

st.sidebar.markdown("## 📊 FILTROS DE DADOS")


st.sidebar.markdown("**Estado (UF)**")
if len(ufs_lista) > 0:
    # Exibir com nome completo no dropdown
    opcoes_display = [f"{uf} - {ufs_dict[uf]}" for uf in ufs_lista]
    
    selecionadas_display = st.sidebar.multiselect(
        "Escolha os estados",
        opcoes_display,
        default=opcoes_display,  # Seleciona todos por padrão
        label_visibility="collapsed"
    )
    
    # Extrair apenas as UFs selecionadas (remover nome)
    estado_selecionado = [sel.split(" - ")[0] for sel in selecionadas_display]
    
    # Se nenhum estado foi selecionado, usar todos
    if len(estado_selecionado) == 0:
        estado_selecionado = ufs_lista
    
    if ufs_invalidas_count > 0:
        st.sidebar.caption(f"⚠️ {ufs_invalidas_count} registros com UF inválida")
else:
    estado_selecionado = []
    st.sidebar.error("❌ Nenhum dado de Estado válido encontrado")
    if ufs_invalidas_count > 0:
        st.sidebar.caption(f"Todos os {ufs_invalidas_count} registros têm UF inválida")

# Órgãos
orgaos_brutos = df['orgao'].dropna().unique()
orgaos = []
for org in orgaos_brutos:
    org_str = str(org).strip()
    if org_str and org_str != 'N/A' and org_str != 'nan' and len(org_str) > 0:
        if org_str not in orgaos:
            orgaos.append(org_str)

orgaos = sorted(orgaos)[:50]
if len(orgaos) == 0:
    orgaos = []

st.sidebar.markdown("**Órgão (Top 50)**")
if len(orgaos) > 0:
    orgao_selecionado = st.sidebar.multiselect(
        "Escolha os órgãos",
        orgaos,
        default=orgaos[:5] if len(orgaos) > 5 else orgaos,
        label_visibility="collapsed"
    )
    # Se nenhum órgão foi selecionado, usar todos
    if len(orgao_selecionado) == 0:
        orgao_selecionado = orgaos
else:
    orgao_selecionado = []
    st.sidebar.info("Sem dados de órgãos para filtrar")

# Filtro por Valor
st.sidebar.markdown("**Valor da Licitação**")
valores_validos = df['valor_estimado'][(df['valor_estimado'] > 0) & (df['valor_estimado'].notna())]
valor_min_default = 0
valor_max_default = 1000000

if len(valores_validos) > 0:
    valor_min_default = int(valores_validos.min())
    valor_max_default = int(valores_validos.max())

col_val1, col_val2 = st.sidebar.columns(2)
with col_val1:
    valor_min = st.number_input("Mín. (R$)", value=valor_min_default, label_visibility="collapsed")
with col_val2:
    valor_max = st.number_input("Máx. (R$)", value=valor_max_default, label_visibility="collapsed")

# Filtro por Modalidade
st.sidebar.markdown("**Modalidade**")
modalidades_lista = sorted(df['modalidade'].dropna().unique().tolist())
modalidades_lista = [m for m in modalidades_lista if str(m) not in ('N/A', 'nan', '')]
if modalidades_lista:
    modalidade_selecionada = st.sidebar.multiselect(
        "Escolha as modalidades",
        modalidades_lista,
        default=modalidades_lista,
        label_visibility="collapsed"
    )
    if not modalidade_selecionada:
        modalidade_selecionada = modalidades_lista
else:
    modalidade_selecionada = []

# Filtro por Status
st.sidebar.markdown("**Status**")
status_lista = sorted(df['status'].dropna().unique().tolist())
status_lista = [s for s in status_lista if str(s) not in ('N/A', 'nan', '')]
if status_lista:
    status_selecionado = st.sidebar.multiselect(
        "Escolha os status",
        status_lista,
        default=status_lista,
        label_visibility="collapsed"
    )
    if not status_selecionado:
        status_selecionado = status_lista
else:
    status_selecionado = []

# Busca avançada multi-campo
st.sidebar.markdown("**🔍 Busca Avançada**")
busca_avancada = st.sidebar.text_input(
    "Buscar em todos os campos",
    placeholder="Ex: cloud AND software, NOT esgoto, termo OR outro",
    label_visibility="collapsed"
)
st.sidebar.caption("Suporta: `OR` (ou), `AND` (e), `NOT` (excluir), vírgula")

# ==================== APLICAR FILTROS ====================

df_filtrado = df.copy()

# Aplicar filtro de UF
if len(estado_selecionado) > 0:
    df_filtrado = df_filtrado[df_filtrado['uf'].isin(estado_selecionado)]

# Aplicar filtro de Órgão
if len(orgao_selecionado) > 0:
    df_filtrado = df_filtrado[df_filtrado['orgao'].isin(orgao_selecionado)]

# Aplicar filtro de Valor
df_filtrado = df_filtrado[
    (df_filtrado['valor_estimado'] >= valor_min) & (df_filtrado['valor_estimado'] <= valor_max)
]

# Aplicar filtro de Modalidade
if modalidade_selecionada:
    df_filtrado = df_filtrado[df_filtrado['modalidade'].isin(modalidade_selecionada)]

# Aplicar filtro de Status
if status_selecionado:
    df_filtrado = df_filtrado[df_filtrado['status'].isin(status_selecionado)]

# Aplicar busca avançada multi-campo com AND/OR/NOT
if busca_avancada:
    campos_busca = ['orgao', 'objeto', 'numero_edital', 'municipio', 'cnpj_orgao', 'modalidade', 'status']
    
    # Construir texto concatenado para busca eficiente
    df_filtrado['_busca'] = df_filtrado[campos_busca].astype(str).agg(' '.join, axis=1).str.lower()
    
    # Separar termos NOT (exclusão)
    termos_not = re.findall(r'NOT\s+(\S+)', busca_avancada, re.IGNORECASE)
    busca_sem_not = re.sub(r'NOT\s+\S+', '', busca_avancada, flags=re.IGNORECASE).strip()
    
    # Verificar se há AND entre termos
    if re.search(r'\bAND\b', busca_sem_not, re.IGNORECASE):
        termos_and = [t.strip() for t in re.split(r'\s+AND\s+', busca_sem_not, flags=re.IGNORECASE) if t.strip()]
        mask = pd.Series(True, index=df_filtrado.index)
        for termo in termos_and:
            # Dentro de cada AND term, suportar OR via vírgula
            sub_termos = [s.strip() for s in re.split(r'\s+OR\s+|,', termo, flags=re.IGNORECASE) if s.strip()]
            sub_mask = pd.Series(False, index=df_filtrado.index)
            for sub in sub_termos:
                sub_mask = sub_mask | df_filtrado['_busca'].str.contains(sub.lower(), na=False)
            mask = mask & sub_mask
    else:
        # OR / virgula
        termos_or = [t.strip() for t in re.split(r'\s+OR\s+|,', busca_sem_not, flags=re.IGNORECASE) if t.strip()]
        mask = pd.Series(False, index=df_filtrado.index)
        for termo in termos_or:
            mask = mask | df_filtrado['_busca'].str.contains(termo.lower(), na=False)
    
    # Aplicar exclusões NOT
    for excl in termos_not:
        mask = mask & ~df_filtrado['_busca'].str.contains(excl.lower(), na=False)
    
    df_filtrado = df_filtrado[mask]
    df_filtrado = df_filtrado.drop(columns=['_busca'])

st.sidebar.divider()
st.sidebar.info(f"📊 **Resultados:** {len(df_filtrado)} licitações de TI encontradas")

# ==================== BUSCAS SALVAS ====================

st.sidebar.markdown("## 💾 BUSCAS SALVAS")

with st.sidebar.expander("Salvar busca atual"):
    nome_busca = st.text_input("Nome da busca", placeholder="Ex: Licitações SP cloud", key="nome_busca_salvar")
    if st.button("💾 Salvar", key="btn_salvar_busca"):
        if nome_busca:
            filtros_salvar = {
                "busca_avancada": busca_avancada or "",
                "valor_min": valor_min,
                "valor_max": valor_max,
            }
            db_auth.salvar_busca(usuario_logado['id'], nome_busca, filtros_salvar)
            st.success(f"Busca '{nome_busca}' salva!")
        else:
            st.warning("Dê um nome à busca")

buscas = db_auth.listar_buscas(usuario_logado['id'])
if buscas:
    for busca_item in buscas[:5]:
        col_b1, col_b2 = st.sidebar.columns([3, 1])
        with col_b1:
            filtros_busca = busca_item.get('filtros', {})
            st.caption(f"🔖 **{busca_item['nome']}** — {filtros_busca.get('busca_avancada', 'sem filtro')}")
        with col_b2:
            if st.button("🗑️", key=f"del_busca_{busca_item['id']}"):
                db_auth.deletar_busca(busca_item['id'], usuario_logado['id'])
                st.rerun()
else:
    st.sidebar.caption("Nenhuma busca salva")

# ==================== ADMIN ====================

if usuario_logado['papel'] == 'admin':
    st.sidebar.divider()
    st.sidebar.markdown("## 👥 ADMIN")
    with st.sidebar.expander("Gerenciar Usuários"):
        usuarios_list = db_auth.listar_usuarios()
        for u in usuarios_list:
            st_u = "🟢" if u['ativo'] else "🔴"
            col_u1, col_u2, col_u3 = st.columns([3, 1, 1])
            with col_u1:
                st.caption(f"{st_u} **{u['username']}** ({u['papel']}) — {u['nome']}")
            with col_u2:
                novo_papel = st.selectbox(
                    "Role", ["admin", "analista", "viewer"],
                    index=["admin", "analista", "viewer"].index(u['papel']) if u['papel'] in ["admin", "analista", "viewer"] else 1,
                    key=f"role_{u['id']}",
                    label_visibility="collapsed"
                )
                if novo_papel != u['papel']:
                    if st.button("✅", key=f"apply_role_{u['id']}"):
                        db_auth.alterar_papel(u['id'], novo_papel)
                        st.rerun()
            with col_u3:
                if u['username'] != usuario_logado['username']:
                    if u['ativo']:
                        if st.button("🚫", key=f"deact_{u['id']}", help="Desativar"):
                            db_auth.desativar_usuario(u['id'])
                            st.rerun()
                    else:
                        if st.button("✅", key=f"act_{u['id']}", help="Ativar"):
                            db_auth.ativar_usuario(u['id'])
                            st.rerun()

# ==================== SEÇÃO DE ALERTAS TELEGRAM ====================

st.sidebar.markdown("## 🔔 ALERTAS TELEGRAM")

# Inicializar banco de alertas
db_alertas = AlertasDB()

# Subtabs para alertas
alert_tab1, alert_tab2 = st.sidebar.tabs(["⚙️ Configurar", "📊 Histórico"])

with alert_tab1:
    # Carregar configuração
    try:
        with open("config/alertas_config.json", 'r', encoding='utf-8') as f:
            config_master = json.load(f)
    except:
        config_master = {"telegram_token": "", "alertas": []}
    
    token_salvo = config_master.get("telegram_token", "").strip()
    
    # Seção 1: Setup do Token
    st.markdown("### 1️⃣ Configurar Bot")
    
    with st.expander("🤖 Token do Telegram (clique para expandir)", expanded=(not token_salvo or token_salvo == "SEU_TOKEN_AQUI")):
        st.caption("Obtenha seu token em: @BotFather no Telegram")
        
        token_input = st.text_input(
            "Token do Bot Telegram",
            value=token_salvo if token_salvo != "SEU_TOKEN_AQUI" else "",
            type="password",
            label_visibility="collapsed"
        )
        
        col_bot1, col_bot2 = st.columns(2)
        
        with col_bot1:
            if st.button("✅ Validar Token", key="btn_validar_token"):
                if token_input:
                    if validar_token(token_input):
                        bot_temp = TelegramAlerter(token_input)
                        if bot_temp.testar_conexao():
                            st.success("✓ Token válido e conectado!")
                        else:
                            st.error("✗ Token inválido ou sem conexão")
                    else:
                        st.error("✗ Formato de token inválido")
                else:
                    st.warning("⚠ Digite um token primeiro")
        
        with col_bot2:
            if st.button("💾 Salvar Token", key="btn_salvar_token"):
                if token_input and validar_token(token_input):
                    config_master["telegram_token"] = token_input
                    with open("config/alertas_config.json", 'w', encoding='utf-8') as f:
                        json.dump(config_master, f, indent=2, ensure_ascii=False)
                    st.success("✓ Token salvo!")
                else:
                    st.error("✗ Token inválido")
    
    # Seção 2: Criar novo alerta
    st.markdown("### 2️⃣ Novo Alerta")
    
    if not token_salvo or token_salvo == "SEU_TOKEN_AQUI":
        st.warning("⚠ Configure o token primeiro para criar alertas")
    else:
        with st.form("form_novo_alerta"):
            nome_alerta = st.text_input("Nome do alerta (único)", placeholder="Ex: Licitações SP - Altos Valores")
            
            chat_id_input = st.text_input(
                "Chat ID do Telegram",
                placeholder="Ex: -1234567890 ou @seu_canal",
                help="ID numérico (negativo para grupo/canal) ou @username"
            )
            
            cols_uf = st.columns(2)
            with cols_uf[0]:
                ufs_select = st.multiselect(
                    "Estados (UFs)",
                    sorted(ufs_dict.keys()),
                    default=sorted(ufs_dict.keys())
                )
            
            with cols_uf[1]:
                orgaos_select = st.multiselect(
                    "Órgãos (deixe vazio = todos)",
                    orgaos[:20] if len(orgaos) > 0 else [],
                    max_selections=5
                )
            
            cols_val = st.columns(2)
            with cols_val[0]:
                valor_min_alerta = st.number_input(
                    "Valor mínimo (R$)",
                    value=0,
                    min_value=0,
                    step=10000
                )
            
            with cols_val[1]:
                valor_max_alerta = st.number_input(
                    "Valor máximo (R$)",
                    value=1000000,
                    min_value=0,
                    step=10000
                )
            
            palavras_chave = st.text_input(
                "Palavras-chave (separadas por vírgula)",
                placeholder="Ex: software, cloud, api",
                help="Deixe vazio para alertar todas as licitações que atendem ao filtro"
            )
            
            ativo = st.checkbox("Ativar este alerta", value=True)
            
            if st.form_submit_button("➕ Criar Alerta", use_container_width=True):
                if not nome_alerta:
                    st.error("✗ Nome obrigatório")
                elif not chat_id_input or not validar_chat_id(chat_id_input):
                    st.error("✗ Chat ID inválido")
                elif not ufs_select:
                    st.error("✗ Selecione pelo menos uma UF")
                else:
                    # Processar palavras-chave
                    palavras = [p.strip() for p in palavras_chave.split(",") if p.strip()] if palavras_chave else []
                    
                    # Criar alerta no banco
                    sucesso = db_alertas.criar_alerta(
                        nome=nome_alerta,
                        chat_id=chat_id_input,
                        ufs=ufs_select,
                        valor_min=valor_min_alerta,
                        valor_max=valor_max_alerta,
                        orgaos=orgaos_select if orgaos_select else ["*"],
                        palavras_chave=palavras,
                        ativo=ativo
                    )
                    
                    if sucesso:
                        st.success(f"✓ Alerta '{nome_alerta}' criado com sucesso!")
                        
                        # Testar envio
                        if st.checkbox("Enviar alerta de teste?"):
                            try:
                                bot = TelegramAlerter(token_salvo)
                                msg = bot.formatar_confirmacao_config({
                                    'nome': nome_alerta,
                                    'ativo': ativo,
                                    'ufs': ufs_select,
                                    'valor_min': valor_min_alerta,
                                    'valor_max': valor_max_alerta,
                                    'orgaos': orgaos_select if orgaos_select else ["Todos"],
                                    'palavras_chave': palavras
                                })
                                
                                resultado = bot.enviar_mensagem(chat_id_input, msg)
                                if resultado and resultado.get('ok'):
                                    st.success("✓ Alerta de teste enviado!")
                                else:
                                    st.error("✗ Erro ao enviar teste")
                            except Exception as e:
                                st.error(f"✗ Erro: {e}")
                    else:
                        st.error("✗ Erro ao criar alerta (verificar se nome já existe)")
    
    # Seção 3: Gerenciar alertas
    st.markdown("### 3️⃣ Seus Alertas")
    
    alertas_lista = db_alertas.listar_alertas()
    
    if alertas_lista:
        for alerta in alertas_lista:
            with st.expander(f"{'🟢' if alerta['ativo'] else '🔴'} {alerta['nome']}", expanded=False):
                col_info1, col_info2 = st.columns(2)
                
                with col_info1:
                    st.write(f"**Chat ID:** `{alerta['chat_id']}`")
                    st.write(f"**UFs:** {', '.join(alerta['ufs'])}")
                    st.write(f"**Valor:** R$ {alerta['valor_min']:,.0f} - R$ {alerta['valor_max']:,.0f}")
                
                with col_info2:
                    st.write(f"**Órgãos:** {', '.join(alerta['orgaos'])}")
                    st.write(f"**Palavras-chave:** {', '.join(alerta['palavras_chave']) if alerta['palavras_chave'] else '(nenhuma)'}")
                    st.write(f"**Status:** {'✅ Ativo' if alerta['ativo'] else '❌ Inativo'}")
                
                # Ações
                col_acao1, col_acao2, col_acao3 = st.columns(3)
                
                with col_acao1:
                    novo_status = not alerta['ativo']
                    status_txt = "Ativar" if not alerta['ativo'] else "Desativar"
                    if st.button(f"🔄 {status_txt}", key=f"toggle_{alerta['id']}"):
                        db_alertas.atualizar_alerta(alerta['id'], ativo=1 if novo_status else 0)
                        st.success(f"✓ Alerta {status_txt.lower()}o!")
                        st.rerun()
                
                with col_acao2:
                    if st.button("🗑️ Deletar", key=f"delete_{alerta['id']}"):
                        db_alertas.deletar_alerta(alerta['id'])
                        st.success(f"✓ Alerta deletado!")
                        st.rerun()
                
                with col_acao3:
                    if token_salvo and token_salvo != "SEU_TOKEN_AQUI":
                        if st.button("📤 Testar", key=f"test_{alerta['id']}"):
                            try:
                                bot = TelegramAlerter(token_salvo)
                                msg = bot.formatar_confirmacao_config({
                                    'nome': alerta['nome'],
                                    'ativo': alerta['ativo'],
                                    'ufs': alerta['ufs'],
                                    'valor_min': alerta['valor_min'],
                                    'valor_max': alerta['valor_max'],
                                    'orgaos': alerta['orgaos'],
                                    'palavras_chave': alerta['palavras_chave']
                                })
                                resultado = bot.enviar_mensagem(alerta['chat_id'], msg)
                                if resultado and resultado.get('ok'):
                                    st.success("✓ Alerta de teste enviado!")
                                else:
                                    st.error("✗ Erro ao enviar teste")
                            except Exception as e:
                                st.error(f"✗ Erro: {str(e)[:100]}")
    else:
        st.info("ℹ Nenhum alerta configurado ainda")

with alert_tab2:
    st.markdown("### 📊 Histórico de Alertas Enviados")
    
    historico = db_alertas.listar_historico(limite=50)
    
    if historico:
        df_hist = pd.DataFrame(historico)
        df_hist = df_hist.sort_values('data_envio', ascending=False)
        
        # Resumo
        col_h1, col_h2, col_h3 = st.columns(3)
        with col_h1:
            st.metric("Total Enviados", len(historico))
        with col_h2:
            valor_total_hist = df_hist['valor'].sum()
            st.metric("Valor Total", f"R$ {valor_total_hist:,.0f}".replace(",", "X").replace(".", ",").replace("X", "."))
        with col_h3:
            alertas_unicos = df_hist['alerta_id'].nunique()
            st.metric("Alertas Ativos", alertas_unicos)
        
        # Tabela
        df_hist_display = df_hist[['numero_edital', 'orgao', 'valor', 'data_envio']].copy()
        df_hist_display.columns = ['Edital', 'Órgão', 'Valor', 'Data Envio']
        df_hist_display['Valor'] = df_hist_display['Valor'].apply(lambda x: f"R$ {x:,.0f}".replace(",", "X").replace(".", ",").replace("X", "."))
        
        st.dataframe(df_hist_display, use_container_width=True, hide_index=True)
    else:
        st.info("ℹ Nenhum histórico de alertas ainda")

# Info de monitoramento
status_monit = db_alertas.obter_status_monitoramento()
if status_monit:
    st.sidebar.divider()
    st.sidebar.markdown("### 🔍 Monitoramento")
    col_monit1, col_monit2 = st.sidebar.columns(2)
    with col_monit1:
        st.metric(
            "Status",
            "🟢 Ativo" if status_monit.get('ativo') else "🔴 Inativo",
            delta=None
        )
    with col_monit2:
        st.metric(
            "Alertas Enviados",
            status_monit.get('total_alertas_enviados', 0),
            delta=None
        )
    
    if status_monit.get('ultimo_check'):
        st.sidebar.caption(f"Última verificação: {status_monit['ultimo_check'][:16]}")

# ==================== RESUMO EXECUTIVO ====================

st.markdown("## 📈 RESUMO EXECUTIVO")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        "Total",
        formatar_numero(len(df_filtrado))
    )

with col2:
    orgaos_unicos = df_filtrado['orgao'].nunique() if 'orgao' in df_filtrado.columns else 0
    st.metric(
        "Órgãos",
        orgaos_unicos
    )

with col3:
    estados_unicos = df_filtrado['uf'].nunique() if 'uf' in df_filtrado.columns else 0
    st.metric(
        "Estados",
        estados_unicos
    )

with col4:
    valor_total = df_filtrado['valor_estimado'].sum()
    st.metric(
        "Valor Total",
        formatar_moeda(valor_total),
        delta=None
    )

with col5:
    valor_medio = df_filtrado['valor_estimado'].mean()
    st.metric(
        "Valor Médio",
        formatar_moeda(valor_medio)
    )

# ==================== GRÁFICOS ====================

st.markdown("## 📊 ANÁLISES")

# Abas para organizar visualizações
tab1, tab2, tab3, tab4, tab5, tab_fav, tab_mapa, tab_hist, tab6, tab_precos, tab_pdf, tab_metricas, tab_agenda, tab_crm = st.tabs([
    "🏛️ Órgãos",
    "🗺️ Estados",
    "💰 Valores",
    "📅 Timeline",
    "📋 Dados",
    "⭐ Favoritos",
    "🗺️ Mapa",
    "📜 Histórico",
    "🌐 Fontes Complementares",
    "📈 Preços",
    "🔍 Análise PDF",
    "📊 Métricas",
    "⏰ Agendador",
    "📊 CRM",
])

# ========== ABA 1: ÓRGÃOS ==========
with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Top 15 Órgãos (Quantidade)")
        
        top_orgaos = df_filtrado['orgao'].value_counts().head(15)
        
        fig = px.bar(
            x=top_orgaos.values,
            y=top_orgaos.index,
            orientation='h',
            title="Órgãos que Mais Licitem TI",
            labels={'x': 'Quantidade', 'y': 'Órgão'},
            color=top_orgaos.values,
            color_continuous_scale='Blues'
        )
        fig.update_layout(height=500, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### Top 15 Órgãos (Valor Total)")
        
        valor_por_orgao = df_filtrado.groupby('orgao')['valor_estimado'].sum().sort_values(ascending=False).head(15)
        
        fig = px.bar(
            x=valor_por_orgao.values,
            y=valor_por_orgao.index,
            orientation='h',
            title="Órgãos por Valor Total de Licitações",
            labels={'x': 'Valor (R$)', 'y': 'Órgão'},
            color=valor_por_orgao.values,
            color_continuous_scale='Reds'
        )
        fig.update_layout(height=500, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

# ========== ABA 2: ESTADOS ==========
with tab2:
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Distribuição por Estado (Quantidade)")
        
        mapa_estados = df_filtrado['uf'].value_counts()
        
        fig = px.pie(
            values=mapa_estados.values,
            names=mapa_estados.index,
            title="Licitações por Estado",
            hole=0.4
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### Ranking de Estados")
        
        rank_estados = df_filtrado['uf'].value_counts().reset_index()
        rank_estados.columns = ['UF', 'Quantidade']
        
        fig = px.bar(
            rank_estados.sort_values('Quantidade', ascending=True).tail(10),
            x='Quantidade',
            y='UF',
            orientation='h',
            title="Top 10 Estados",
            color='Quantidade',
            color_continuous_scale='Greens'
        )
        fig.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig, use_container_width=True)

# ========== ABA 3: VALORES ==========
with tab3:
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Distribuição de Valores")
        
        # Criar faixas de valores
        df_temp = df_filtrado.copy()
        faixas = [0, 10000, 50000, 100000, 500000, 1000000, float('inf')]
        labels = ['até 10k', '10k-50k', '50k-100k', '100k-500k', '500k-1M', '+1M']
        df_temp['faixa'] = pd.cut(df_temp['valor_estimado'], bins=faixas, labels=labels)
        
        faixa_count = df_temp['faixa'].value_counts().sort_index()
        
        fig = px.bar(
            x=faixa_count.index,
            y=faixa_count.values,
            title="Licitações por Faixa de Valor",
            labels={'x': 'Faixa de Valor', 'y': 'Quantidade'},
            color=faixa_count.values,
            color_continuous_scale='Purples'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### Top 10 Maiores Licitações")
        
        top_valor = df_filtrado.nlargest(10, 'valor_estimado')[['orgao', 'objeto', 'valor_estimado']]
        top_valor['valor_estimado'] = top_valor['valor_estimado'].apply(formatar_moeda)
        
        fig = px.bar(
            x=top_valor['valor_estimado'],
            y=range(len(top_valor)),
            orientation='h',
            title="Top 10 Maiores Licitações",
            text=top_valor['valor_estimado']
        )
        st.plotly_chart(fig, use_container_width=True)

# ========== ABA 4: TIMELINE ==========
with tab4:
    st.markdown("### Publicações ao Longo do Tempo")
    
    # Agrupar por data
    df_timeline = df_filtrado.copy()
    df_timeline['data'] = df_timeline['data_publicacao'].dt.date
    timeline = df_timeline.groupby('data').size().reset_index(name='quantidade')
    
    fig = px.line(
        timeline,
        x='data',
        y='quantidade',
        title="Publicações por Data",
        labels={'data': 'Data', 'quantidade': 'Quantidade'},
        markers=True
    )
    fig.update_layout(height=400, hovermode='x unified')
    st.plotly_chart(fig, use_container_width=True)
    
    # Estatísticas por dia da semana
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Publicações por Dia da Semana")
        df_DOW = df_filtrado.copy()
        df_DOW['dow'] = df_DOW['data_publicacao'].dt.day_name()
        dias_ordem = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        dias_pt = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sab', 'Dom']
        
        dow_count = df_DOW['dow'].value_counts().reindex(dias_ordem, fill_value=0)
        dow_df = pd.DataFrame({
            'Dia': dias_pt,
            'Quantidade': dow_count.values
        })
        
        fig = px.bar(
            dow_df,
            x='Dia',
            y='Quantidade',
            title="Distribuição por Dia da Semana",
            color='Quantidade',
            color_continuous_scale='Viridis'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### Modalidades de Licitação")
        modalidades = df_filtrado['modalidade'].value_counts().head(10)
        
        fig = px.pie(
            values=modalidades.values,
            names=modalidades.index,
            title="Distribuição por Modalidade",
        )
        st.plotly_chart(fig, use_container_width=True)

# ========== ABA 5: DADOS ==========
with tab5:
    # Sub-tab para tabela vs cards
    tab5_1, tab5_2 = st.tabs(["📊 Tabela", "🔗 Links de Editais"])
    
    with tab5_1:
        st.markdown("### 📋 TABELA COMPLETA DE LICITAÇÕES")
    
    # Opções de visualização
    col1, col2, col3 = st.columns(3)
    
    with col1:
        qtd_registros = st.selectbox(
            "Mostrar registros",
            [10, 25, 50, 100, 250, 500, len(df_filtrado)],
            index=2
        )
    
    with col2:
        ordenacao = st.selectbox(
            "Ordenar por",
            ['Valor (maior)', 'Valor (menor)', 'Data (mais recente)', 'Data (mais antigo)', 'Órgão']
        )
    
    with col3:
        if tem_perm("exportar") and st.button("📥 Baixar CSV completo"):
            csv = df_filtrado.to_csv(index=False, encoding='utf-8')
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"licitacoes_ti_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    # Aplicar ordenação
    df_exibir = df_filtrado.copy()
    
    if ordenacao == 'Valor (maior)':
        df_exibir = df_exibir.sort_values('valor_estimado', ascending=False)
    elif ordenacao == 'Valor (menor)':
        df_exibir = df_exibir.sort_values('valor_estimado', ascending=True)
    elif ordenacao == 'Data (mais recente)':
        df_exibir = df_exibir.sort_values('data_publicacao', ascending=False)
    elif ordenacao == 'Data (mais antigo)':
        df_exibir = df_exibir.sort_values('data_publicacao', ascending=True)
    else:
        df_exibir = df_exibir.sort_values('orgao')
    
    # Preparar dados para exibição
    df_display = df_exibir.head(qtd_registros).copy()
    
    # Formatar colunas
    df_display['data_publicacao'] = df_display['data_publicacao'].dt.strftime('%d/%m/%Y')
    df_display['valor_estimado'] = df_display['valor_estimado'].apply(formatar_moeda)
    
    # Usar link_edital direto se existir, senão gerar
    if 'link_edital' not in df_display.columns or df_display['link_edital'].isna().all():
        df_display['link_edital'] = df_display['numero_edital'].apply(gerar_link_edital)
    else:
        df_display['link_edital'] = df_display['link_edital'].fillna('').apply(
            lambda x: x if x else 'https://www.pncp.gov.br'
        )
    
    # Reordenar colunas
    colunas_ordem = ['data_publicacao', 'orgao', 'cnpj_orgao', 'objeto', 'valor_estimado', 'uf', 'municipio', 
                     'modalidade', 'status', 'criterio_julgamento', 'numero_edital', 'fonte', 'link_edital']
    colunas_existentes = [col for col in colunas_ordem if col in df_display.columns]
    df_display = df_display[colunas_existentes]
    
    # Renomear para português
    rename_cols = {
        'data_publicacao': 'Data',
        'orgao': 'Órgão',
        'cnpj_orgao': 'CNPJ',
        'objeto': 'Objeto',
        'valor_estimado': 'Valor Estimado',
        'uf': 'UF',
        'municipio': 'Município',
        'modalidade': 'Modalidade',
        'status': 'Status',
        'criterio_julgamento': 'Critério',
        'numero_edital': 'Número Edital',
        'fonte': 'Fonte',
        'link_edital': 'Link Edital'
    }
    df_display = df_display.rename(columns=rename_cols)
    
    st.dataframe(df_display, use_container_width=True, height=500)
    
    # Opção de busca
    st.markdown("### 🔎 BUSCA RÁPIDA")
    termo = st.text_input("Buscar por palavra-chave no objeto da licitação")
    
    if termo:
        resultado = df_filtrado[df_filtrado['objeto'].str.contains(termo, case=False, na=False)]
        
        if len(resultado) > 0:
            st.success(f"✓ {len(resultado)} resultado(s) encontrado(s)")
            
            resultado['data_publicacao'] = resultado['data_publicacao'].dt.strftime('%d/%m/%Y')
            resultado['valor_estimado'] = resultado['valor_estimado'].apply(formatar_moeda)
            
            # Gerar link para edital PNCP
            resultado['link_edital'] = resultado['numero_edital'].apply(gerar_link_edital)
            
            colunas_existentes = [col for col in colunas_ordem if col in resultado.columns]
            resultado = resultado[colunas_existentes]
            resultado = resultado.rename(columns=rename_cols)
            
            st.dataframe(resultado, use_container_width=True)
        else:
            st.warning("Nenhum resultado encontrado")
    
    with tab5_2:
        st.markdown("### 🔗 EDITAIS COM LINKS CLICÁVEIS")
        st.info("Clique em qualquer link para abrir o edital no portal PNCP")
        
        # Gerar links para os dados filtrados
        df_links = df_filtrado.copy()
        df_links['link_edital'] = df_links['numero_edital'].apply(gerar_link_edital)
        df_links = df_links.sort_values('data_publicacao', ascending=False)
        
        # Mostrar top N editais com links
        top_n = st.slider("Mostrar quantos editais?", 5, 50, 15)
        
        st.markdown(f"**Exibindo os {top_n} editais mais recentes:**")
        
        # Exibir cards com links clicáveis e botão de favoritar
        for idx, row in df_links.head(top_n).iterrows():
            edital_id = str(row['numero_edital'])
            eh_fav = db_auth.eh_favorito(usuario_logado['id'], edital_id) if edital_id != 'N/A' else False
            icone_fav = "⭐" if eh_fav else "☆"
            
            with st.expander(f"{icone_fav} 📄 {edital_id} - {row['orgao'][:40]}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Órgão:** {row['orgao']}")
                    st.write(f"**Objeto:** {row['objeto']}")
                    st.write(f"**Valor:** {formatar_moeda(row['valor_estimado'])}")
                    st.write(f"**UF:** {row['uf']} | **Município:** {row['municipio']}")
                    st.write(f"**Data:** {row['data_publicacao'].strftime('%d/%m/%Y')}")
                
                with col2:
                    link_ed = row.get('link_edital', '') or gerar_link_edital(edital_id)
                    st.markdown(f"[🔗 **Abrir Edital**]({link_ed})")
                    
                    link_pdf = gerar_link_pdf_edital(row.get('cnpj_orgao'), edital_id)
                    if link_pdf:
                        st.markdown(f"[📥 **Documentos/PDF**]({link_pdf})")
                    
                    if edital_id != 'N/A':
                        if eh_fav:
                            if st.button("⭐ Remover", key=f"unfav_{idx}"):
                                db_auth.remover_favorito(usuario_logado['id'], edital_id)
                                st.rerun()
                        else:
                            if st.button("☆ Favoritar", key=f"fav_{idx}"):
                                db_auth.adicionar_favorito(
                                    usuario_logado['id'], edital_id,
                                    orgao=str(row['orgao']),
                                    objeto=str(row['objeto'])[:500],
                                    valor_estimado=float(row['valor_estimado']),
                                    uf=str(row['uf'])
                                )
                                st.rerun()

# ==================== RODAPÉ ====================

st.divider()

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("🔄 Atualizar dados"):
        st.cache_data.clear()
        st.rerun()

with col2:
    # Download direto do Excel
    if os.path.exists(EXCEL_PATH):
        with open(EXCEL_PATH, 'rb') as f:
            excel_data = f.read()
        st.download_button(
            label="📊 Baixar Excel",
            data=excel_data,
            file_name=f"licitacoes_ti_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

with col3:
    # Export iCal - Aberturas
    if tem_perm("exportar"):
        ics_abertura = gerar_ics(df_filtrado.to_dict('records'), tipo_evento="abertura")
        st.download_button(
            "📅 Calendário Aberturas (.ics)",
            ics_abertura,
            f"aberturas_{datetime.now().strftime('%Y%m%d')}.ics",
            "text/calendar"
        )

with col4:
    # Export iCal - Encerramentos
    if tem_perm("exportar"):
        ics_encerramento = gerar_ics(df_filtrado.to_dict('records'), tipo_evento="encerramento")
        st.download_button(
            "📅 Calendário Encerramentos (.ics)",
            ics_encerramento,
            f"encerramentos_{datetime.now().strftime('%Y%m%d')}.ics",
            "text/calendar"
        )

st.markdown("""
**Radar de Licitações TI** © 2026 | Dados: PNCP | Atualização: Diária
""")

# ==================== ANÁLISES ADICIONAIS ====================

st.divider()

st.markdown("## 🔬 ANÁLISES AVANÇADAS")

expander_analises = st.expander("📊 Clique para expandir análises avançadas")

with expander_analises:
    col1, col2, col3 = st.columns(3)
    
    # Análise 1: Órgãos mais ativos
    with col1:
        if len(df_filtrado) > 0:
            st.markdown("### Órgão Mais Ativo")
            orgao_top = df_filtrado['orgao'].value_counts().index[0]
            qtd_top = df_filtrado['orgao'].value_counts().values[0]
            st.metric("Líder em quantidade", f"{orgao_top}", f"+{qtd_top} licitações")
    
    # Análise 2: Maior valor
    with col2:
        if len(df_filtrado) > 0:
            maior_lic = df_filtrado.loc[df_filtrado['valor_estimado'].idxmax()]
            st.markdown("### Maior Licitação")
            st.metric("Valor máximo", formatar_moeda(maior_lic['valor_estimado']), 
                     f"Órgão: {maior_lic['orgao'][:20]}...")
    
    # Análise 3: Média por órgão
    with col3:
        if len(df_filtrado) > 0:
            media_orgao = df_filtrado.groupby('orgao')['valor_estimado'].count().mean()
            st.metric("Média licitações/órgão", f"{media_orgao:.1f}", "licitações por órgão")
    
    # Gráfico de concentração
    st.markdown("### Concentração de Licitações (Top 10)")
    
    top_10_orgaos = df_filtrado['orgao'].value_counts().head(10)
    total_licitacoes = len(df_filtrado)
    percentual = (top_10_orgaos.sum() / total_licitacoes * 100)
    
    fig = go.Figure(data=[
        go.Bar(x=top_10_orgaos.index, y=top_10_orgaos.values, name='Top 10'),
        go.Bar(x=['Outros'], y=[total_licitacoes - top_10_orgaos.sum()], name='Outros')
    ])
    
    fig.update_layout(
        title=f"Top 10 Órgãos concentram {percentual:.1f}% das licitações",
        xaxis_title="Órgão",
        yaxis_title="Quantidade",
        barmode='stack',
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Tabela de estatísticas por órgão
    st.markdown("### Estatísticas por Órgão")
    
    stats_orgao = df_filtrado.groupby('orgao').agg({
        'valor_estimado': ['count', 'sum', 'mean', 'max']
    }).round(2)
    
    stats_orgao.columns = ['Quantidade', 'Valor Total', 'Valor Médio', 'Maior Valor']
    stats_orgao = stats_orgao.sort_values('Valor Total', ascending=False).head(15)
    
    # Formatar como moeda
    for col in ['Valor Total', 'Valor Médio', 'Maior Valor']:
        stats_orgao[col] = stats_orgao[col].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    
    st.dataframe(stats_orgao, use_container_width=True)

# ========== ABA FAVORITOS ==========
with tab_fav:
    st.markdown("### ⭐ SEUS FAVORITOS")
    if not tem_perm("favoritos"):
        st.info("🔒 Seu perfil não tem acesso a esta funcionalidade.")
    else:
        favoritos = db_auth.listar_favoritos(usuario_logado['id'])
        if favoritos:
            st.info(f"Você tem {len(favoritos)} licitação(ões) favoritada(s)")
            
            df_fav = pd.DataFrame(favoritos)
            df_fav_display = df_fav[['numero_edital', 'orgao', 'objeto', 'valor_estimado', 'uf', 'notas', 'criado_em']].copy()
            df_fav_display['valor_estimado'] = df_fav_display['valor_estimado'].apply(
                lambda x: formatar_moeda(x) if x > 0 else 'N/I'
            )
            df_fav_display.columns = ['Edital', 'Órgão', 'Objeto', 'Valor', 'UF', 'Notas', 'Data Favoritado']
            st.dataframe(df_fav_display, use_container_width=True, height=400)
            
            # Remover favoritos
            st.markdown("#### Remover favorito")
            editais_fav = [f['numero_edital'] for f in favoritos]
            edital_remover = st.selectbox("Selecione o edital", editais_fav, key="sel_remover_fav")
            if st.button("🗑️ Remover dos favoritos", key="btn_remover_fav"):
                db_auth.remover_favorito(usuario_logado['id'], edital_remover)
                st.success("Removido dos favoritos!")
                st.rerun()
            
            # Download
            csv_fav = df_fav[['numero_edital', 'orgao', 'objeto', 'valor_estimado', 'uf', 'notas']].to_csv(index=False)
            st.download_button("📥 Baixar favoritos (CSV)", csv_fav, "favoritos.csv", "text/csv")
        else:
            st.info("Nenhum favorito ainda. Use o botão ⭐ na aba Dados para adicionar.")
        
        # Adicionar favorito manualmente
        st.divider()
        st.markdown("#### Adicionar favorito manualmente")
        with st.form("form_add_fav"):
            fav_edital = st.text_input("Número do edital")
            fav_orgao = st.text_input("Órgão")
            fav_objeto = st.text_area("Objeto", max_chars=500)
            fav_valor = st.number_input("Valor estimado (R$)", min_value=0.0, step=1000.0)
            fav_uf = st.text_input("UF", max_chars=2)
            fav_notas = st.text_area("Notas pessoais", max_chars=500)
            
            if st.form_submit_button("⭐ Adicionar aos favoritos"):
                if fav_edital:
                    db_auth.adicionar_favorito(
                        usuario_logado['id'], fav_edital,
                        orgao=fav_orgao, objeto=fav_objeto,
                        valor_estimado=fav_valor, uf=fav_uf, notas=fav_notas
                    )
                    st.success("Adicionado aos favoritos!")
                    st.rerun()
                else:
                    st.warning("Número do edital é obrigatório")

# ========== ABA MAPA ==========
with tab_mapa:
    st.markdown("### 🗺️ MAPA GEOGRÁFICO DE LICITAÇÕES")
    
    # Coordenadas das capitais brasileiras por UF
    UF_COORDS = {
        'AC': (-9.97, -67.81), 'AL': (-9.67, -35.74), 'AM': (-3.12, -60.02),
        'AP': (0.03, -51.07), 'BA': (-12.97, -38.51), 'CE': (-3.72, -38.53),
        'DF': (-15.78, -47.93), 'ES': (-20.32, -40.34), 'GO': (-16.68, -49.26),
        'MA': (-2.53, -44.28), 'MG': (-19.92, -43.94), 'MS': (-20.44, -54.65),
        'MT': (-15.60, -56.10), 'PA': (-1.46, -48.50), 'PB': (-7.12, -34.86),
        'PE': (-8.05, -34.87), 'PI': (-5.09, -42.80), 'PR': (-25.43, -49.27),
        'RJ': (-22.91, -43.17), 'RN': (-5.79, -35.21), 'RO': (-8.76, -63.90),
        'RR': (2.82, -60.67), 'RS': (-30.03, -51.23), 'SC': (-27.60, -48.55),
        'SE': (-10.91, -37.07), 'SP': (-23.55, -46.63), 'TO': (-10.18, -48.33),
    }
    
    # Agregar dados por UF
    mapa_data = df_filtrado.groupby('uf').agg(
        quantidade=('uf', 'size'),
        valor_total=('valor_estimado', 'sum'),
        valor_medio=('valor_estimado', 'mean'),
    ).reset_index()
    
    # Adicionar coordenadas
    mapa_data['lat'] = mapa_data['uf'].map(lambda x: UF_COORDS.get(x, (0, 0))[0])
    mapa_data['lon'] = mapa_data['uf'].map(lambda x: UF_COORDS.get(x, (0, 0))[1])
    mapa_data = mapa_data[(mapa_data['lat'] != 0) & (mapa_data['lon'] != 0)]
    
    if not mapa_data.empty:
        col_mapa1, col_mapa2 = st.columns([1, 1])
        
        with col_mapa1:
            metrica_mapa = st.radio("Métrica do mapa", ["Quantidade", "Valor Total"], horizontal=True)
        
        with col_mapa2:
            st.metric("Estados no mapa", len(mapa_data))
        
        size_col = 'quantidade' if metrica_mapa == "Quantidade" else 'valor_total'
        
        mapa_data['texto'] = mapa_data.apply(
            lambda r: f"{r['uf']}: {int(r['quantidade'])} licitações | R$ {r['valor_total']:,.0f}".replace(",", "."),
            axis=1
        )
        
        fig_mapa = px.scatter_geo(
            mapa_data,
            lat='lat',
            lon='lon',
            size=size_col,
            color=size_col,
            hover_name='uf',
            hover_data={'quantidade': True, 'valor_total': ':,.0f', 'lat': False, 'lon': False},
            text='uf',
            title=f"Distribuição por Estado — {metrica_mapa}",
            color_continuous_scale='YlOrRd',
            size_max=40,
        )
        fig_mapa.update_geos(
            scope="south america",
            center=dict(lat=-14, lon=-52),
            projection_scale=3,
            showland=True, landcolor="rgb(243, 243, 243)",
            showocean=True, oceancolor="rgb(204, 229, 255)",
            showcountries=True,
            showcoastlines=True,
        )
        fig_mapa.update_layout(height=600, margin=dict(l=0, r=0, t=40, b=0))
        fig_mapa.update_traces(textposition='top center', textfont_size=9)
        st.plotly_chart(fig_mapa, use_container_width=True)
        
        # Ranking lado a lado
        st.markdown("#### Ranking por Estado")
        mapa_ranking = mapa_data.sort_values('valor_total', ascending=False).copy()
        mapa_ranking['valor_total'] = mapa_ranking['valor_total'].apply(formatar_moeda)
        mapa_ranking['valor_medio'] = mapa_ranking['valor_medio'].apply(formatar_moeda)
        mapa_ranking.columns = ['UF', 'Qtd', 'Valor Total', 'Valor Médio', 'lat', 'lon', 'texto']
        st.dataframe(mapa_ranking[['UF', 'Qtd', 'Valor Total', 'Valor Médio']], use_container_width=True, hide_index=True)
    else:
        st.warning("Sem dados geográficos para exibir")

# ========== ABA HISTÓRICO ==========
with tab_hist:
    st.markdown("### 📜 HISTÓRICO DE COLETAS E EVOLUÇÃO")

    hist_db = HistoricoDB()
    fases = FasesDB()

    hist_t1, hist_t2, hist_t3 = st.tabs(["📈 Evolução", "📋 Coletas", "🔄 Mudanças de Status"])

    with hist_t1:
        df_evo = hist_db.obter_evolucao_ti()
        if df_evo.empty:
            st.info("Nenhuma coleta registrada ainda. Execute `python pncp_radar_ti_plus.py` para gerar o primeiro registro.")
        else:
            fig_evo = px.line(
                df_evo, x='data_execucao', y='total_ti',
                title="Evolução de Licitações de TI Detectadas",
                labels={'data_execucao': 'Data da Coleta', 'total_ti': 'Total TI'},
                markers=True
            )
            fig_evo.update_layout(hovermode='x unified')
            st.plotly_chart(fig_evo, use_container_width=True)

            col_e1, col_e2 = st.columns(2)
            with col_e1:
                fig_val = px.area(
                    df_evo, x='data_execucao', y='valor_total',
                    title="Evolução do Valor Total (R$)",
                    labels={'data_execucao': 'Data', 'valor_total': 'Valor Total R$'}
                )
                st.plotly_chart(fig_val, use_container_width=True)
            with col_e2:
                fig_ufs = px.bar(
                    df_evo, x='data_execucao', y='total_ufs',
                    title="UFs com Licitações por Coleta",
                    labels={'data_execucao': 'Data', 'total_ufs': 'UFs'}
                )
                st.plotly_chart(fig_ufs, use_container_width=True)

            # Evolução por UF específica
            uf_hist = st.selectbox("Evolução por UF", [""] + sorted(df['uf'].dropna().unique().tolist()), key="uf_hist_sel")
            if uf_hist:
                df_uf_evo = hist_db.obter_evolucao_uf(uf_hist)
                if not df_uf_evo.empty:
                    fig_uf = px.line(
                        df_uf_evo, x='data_execucao', y='quantidade',
                        title=f"Evolução de Licitações TI — {uf_hist}",
                        markers=True
                    )
                    st.plotly_chart(fig_uf, use_container_width=True)
                else:
                    st.info(f"Sem dados históricos para {uf_hist}")

    with hist_t2:
        coletas = hist_db.listar_coletas(limite=30)
        if not coletas:
            st.info("Nenhuma coleta registrada.")
        else:
            df_coletas = pd.DataFrame(coletas)
            df_coletas['data_execucao'] = pd.to_datetime(df_coletas['data_execucao']).dt.strftime('%d/%m/%Y %H:%M')
            if 'valor_total' in df_coletas.columns:
                df_coletas['valor_total'] = df_coletas['valor_total'].apply(lambda v: f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            colunas_show = [c for c in ['data_execucao', 'fonte', 'total_verificadas', 'total_ti', 'valor_total', 'total_ufs'] if c in df_coletas.columns]
            df_coletas.columns = [c.replace('_', ' ').title() for c in df_coletas.columns]
            colunas_show_titles = [c.replace('_', ' ').title() for c in colunas_show]
            st.dataframe(df_coletas[colunas_show_titles], use_container_width=True, hide_index=True)

    with hist_t3:
        st.markdown("#### 🔄 Mudanças de Status Detectadas")
        stats_fases = fases.contar_mudancas()
        col_f1, col_f2, col_f3 = st.columns(3)
        col_f1.metric("Total de Mudanças", stats_fases.get('total_mudancas', 0))
        col_f2.metric("Editais Rastreados", stats_fases.get('editais_rastreados', 0))
        col_f3.metric("Status Distintos", stats_fases.get('status_distintos', 0))

        mudancas = fases.listar_mudancas(limite=50)
        if mudancas:
            df_mud = pd.DataFrame(mudancas)
            st.dataframe(df_mud, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma mudança de status detectada. Execute mais coletas para detectar transições.")

# ========== ABA 6: FONTES COMPLEMENTARES ==========
with tab6:
    st.markdown("### 🌐 FONTES COMPLEMENTARES DE LICITAÇÕES")
    st.markdown("""
    Dados de licitações de TI coletados de múltiplas fontes públicas gratuitas, 
    complementando o PNCP com cobertura de diários oficiais municipais, contratos federais e compras governamentais.
    """)

    # Sub-abas para cada fonte
    ft1, ft2, ft3, ft4 = st.tabs([
        "📊 Visão Consolidada",
        "📰 Querido Diário",
        "🏛️ Portal Transparência",
        "🛒 Compras.gov.br"
    ])

    # Carregar dados complementares
    @st.cache_data(ttl=300)
    def carregar_complementares():
        dfs = {}
        for nome, caminho in [
            ("consolidado", OUTPUT_COMPLEMENTAR),
            ("querido_diario", OUTPUT_QUERIDO_DIARIO),
            ("transparencia", OUTPUT_TRANSPARENCIA),
            ("compras_gov", OUTPUT_COMPRAS_GOV),
        ]:
            if os.path.exists(caminho):
                try:
                    df_tmp = pd.read_csv(caminho)
                    if 'valor_estimado' in df_tmp.columns:
                        df_tmp['valor_estimado'] = pd.to_numeric(df_tmp['valor_estimado'], errors='coerce').fillna(0)
                    if 'data_publicacao' in df_tmp.columns:
                        df_tmp['data_publicacao'] = pd.to_datetime(df_tmp['data_publicacao'], errors='coerce')
                    dfs[nome] = df_tmp
                except Exception:
                    dfs[nome] = pd.DataFrame()
            else:
                dfs[nome] = pd.DataFrame()
        return dfs

    dfs_comp = carregar_complementares()

    # Carregar estado complementar
    estado_comp = None
    if os.path.exists(STATE_FILE_COMPLEMENTAR):
        try:
            with open(STATE_FILE_COMPLEMENTAR, 'r', encoding='utf-8') as f:
                estado_comp = json.load(f)
        except Exception:
            pass

    with ft1:
        st.markdown("#### 📊 Dados Consolidados de Todas as Fontes")

        df_consolidado = dfs_comp.get("consolidado", pd.DataFrame())

        if df_consolidado.empty:
            st.warning("⚠ Nenhum dado complementar coletado ainda.")
            st.info("Execute no terminal: `python coletor_fontes_complementares.py`")
        else:
            # KPIs
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("Total Complementar", formatar_numero(len(df_consolidado)))
            with c2:
                n_fontes = df_consolidado['fonte'].nunique() if 'fonte' in df_consolidado.columns else 0
                st.metric("Fontes Ativas", n_fontes)
            with c3:
                val_total = df_consolidado['valor_estimado'].sum()
                st.metric("Valor Total", formatar_moeda(val_total))
            with c4:
                n_ufs = df_consolidado['uf'].nunique() if 'uf' in df_consolidado.columns else 0
                st.metric("Estados", n_ufs)

            # Gráfico por fonte
            if 'fonte' in df_consolidado.columns:
                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    fonte_count = df_consolidado['fonte'].value_counts()
                    fig = px.pie(
                        values=fonte_count.values,
                        names=fonte_count.index,
                        title="Distribuição por Fonte",
                        hole=0.4,
                        color_discrete_sequence=px.colors.qualitative.Set2
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with col_g2:
                    if 'uf' in df_consolidado.columns:
                        uf_count = df_consolidado['uf'].value_counts().head(10)
                        fig = px.bar(
                            x=uf_count.values,
                            y=uf_count.index,
                            orientation='h',
                            title="Top 10 UFs (Fontes Complementares)",
                            color=uf_count.values,
                            color_continuous_scale='Teal'
                        )
                        fig.update_layout(showlegend=False, height=400)
                        st.plotly_chart(fig, use_container_width=True)

            # Tabela
            st.markdown("#### Dados")
            df_show = df_consolidado.copy()
            if 'data_publicacao' in df_show.columns:
                df_show['data_publicacao'] = df_show['data_publicacao'].dt.strftime('%d/%m/%Y')
            if 'valor_estimado' in df_show.columns:
                df_show['valor_estimado'] = df_show['valor_estimado'].apply(
                    lambda x: formatar_moeda(x) if x > 0 else 'N/I'
                )
            colunas_exibir = [c for c in ['data_publicacao', 'orgao', 'objeto', 'valor_estimado', 'uf', 'fonte', 'url_fonte'] if c in df_show.columns]
            st.dataframe(df_show[colunas_exibir].head(100), use_container_width=True, height=400)

        # Info da última coleta
        if estado_comp:
            st.divider()
            st.caption(f"Última coleta complementar: {estado_comp.get('data_execucao', 'N/A')[:16]}")
            fontes_info = estado_comp.get('fontes', {})
            cols_info = st.columns(3)
            with cols_info[0]:
                st.caption(f"Querido Diário: {fontes_info.get('querido_diario', 0)} registros")
            with cols_info[1]:
                st.caption(f"Portal Transparência: {fontes_info.get('portal_transparencia', 0)} registros")
            with cols_info[2]:
                st.caption(f"Compras.gov.br: {fontes_info.get('compras_gov', 0)} registros")

    with ft2:
        st.markdown("#### 📰 Querido Diário — Diários Oficiais Municipais")
        st.markdown("Fonte: [Open Knowledge Brasil](https://queridodiario.ok.org.br) — Publicações de ~5000 municípios")

        df_qd = dfs_comp.get("querido_diario", pd.DataFrame())
        if df_qd.empty:
            st.info("Nenhum dado do Querido Diário. Execute a coleta complementar.")
        else:
            st.metric("Publicações de TI", len(df_qd))
            if 'municipio' in df_qd.columns:
                top_mun = df_qd['municipio'].value_counts().head(10)
                fig = px.bar(x=top_mun.values, y=top_mun.index, orientation='h',
                             title="Top 10 Municípios com Publicações de TI",
                             color=top_mun.values, color_continuous_scale='Blues')
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

            df_qd_show = df_qd.copy()
            if 'objeto' in df_qd_show.columns:
                df_qd_show['objeto'] = df_qd_show['objeto'].str[:200]
            st.dataframe(df_qd_show.head(50), use_container_width=True, height=400)

    with ft3:
        st.markdown("#### 🏛️ Portal da Transparência — Contratos Federais")
        st.markdown("Fonte: [CGU](https://portaldatransparencia.gov.br) — Contratos da administração federal")

        df_pt = dfs_comp.get("transparencia", pd.DataFrame())
        if df_pt.empty:
            st.info("Nenhum dado do Portal da Transparência.")
            st.markdown("""
            **Para ativar esta fonte:**
            1. Cadastre-se em [Portal da Transparência - API](https://portaldatransparencia.gov.br/api-de-dados/cadastrar-email)
            2. Receba a chave gratuita por email
            3. Configure abaixo na seção de configuração
            """)
        else:
            c1, c2 = st.columns(2)
            with c1:
                st.metric("Contratos de TI", len(df_pt))
            with c2:
                val = df_pt['valor_estimado'].sum() if 'valor_estimado' in df_pt.columns else 0
                st.metric("Valor Total", formatar_moeda(val))
            st.dataframe(df_pt.head(50), use_container_width=True, height=400)

    with ft4:
        st.markdown("#### 🛒 Compras.gov.br — Dados Abertos de Contratações")
        st.markdown("Fonte: [Compras Governamentais](https://compras.dados.gov.br) — Contratos do governo federal")

        df_cg = dfs_comp.get("compras_gov", pd.DataFrame())
        if df_cg.empty:
            st.info("Nenhum dado do Compras.gov.br. Execute a coleta complementar.")
        else:
            c1, c2 = st.columns(2)
            with c1:
                st.metric("Contratos de TI", len(df_cg))
            with c2:
                val = df_cg['valor_estimado'].sum() if 'valor_estimado' in df_cg.columns else 0
                st.metric("Valor Total", formatar_moeda(val))
            st.dataframe(df_cg.head(50), use_container_width=True, height=400)

    # Botão para executar coleta
    st.divider()
    col_acao1, col_acao2 = st.columns(2)
    with col_acao1:
        if st.button("🔄 Executar Coleta Complementar", use_container_width=True):
            with st.spinner("Coletando dados de fontes complementares..."):
                try:
                    chave_pt = carregar_chave_transparencia()
                    coletor = ColetorMultiFontes(chave_transparencia=chave_pt)
                    df_resultado = coletor.coletar_todas(dias_atras=7)
                    st.cache_data.clear()
                    if not df_resultado.empty:
                        st.success(f"✓ Coleta concluída! {len(df_resultado)} registros de {len(coletor.resumo.get('fontes', {}))} fontes")
                    else:
                        st.warning("Coleta concluída, mas nenhum registro encontrado.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro na coleta: {e}")

    with col_acao2:
        with st.expander("🔑 Configurar API Portal Transparência"):
            chave_atual = carregar_chave_transparencia()
            nova_chave = st.text_input(
                "Chave da API (gratuita)",
                value=chave_atual,
                type="password",
                help="Cadastre-se em portaldatransparencia.gov.br/api-de-dados/cadastrar-email"
            )
            if st.button("💾 Salvar Chave"):
                if nova_chave:
                    salvar_chave_transparencia(nova_chave)
                    st.success("✓ Chave salva!")
                else:
                    st.warning("Digite uma chave")

# ==================== PAINEL DE COMPLIANCE ====================

st.divider()
st.markdown("## 🛡️ VERIFICAÇÃO DE COMPLIANCE")
st.markdown("Consultas públicas de sanções e impedimentos de fornecedores.")

with st.expander("🔍 Consultar CNPJ em bases de sanções", expanded=False):
    cnpj_consulta = st.text_input(
        "CNPJ do fornecedor",
        placeholder="00.000.000/0000-00",
        help="Digite o CNPJ para verificar CEIS, CNEP e CEPIM",
        key="cnpj_compliance"
    )

    if st.button("🔎 Verificar Compliance", key="btn_compliance"):
        if cnpj_consulta and len(cnpj_consulta.replace('.', '').replace('/', '').replace('-', '').strip()) >= 11:
            cnpj_limpo = cnpj_consulta.replace('.', '').replace('/', '').replace('-', '').strip()
            st.markdown("**Fontes de consulta pública:**")
            col_c1, col_c2, col_c3 = st.columns(3)
            with col_c1:
                st.markdown("#### CEIS")
                st.caption("Cadastro de Empresas Inidôneas e Suspensas")
                st.markdown(f"[🔗 Consultar CEIS](https://portaldatransparencia.gov.br/sancoes/consulta?cpfCnpj={cnpj_limpo}&tipoPessoa=PJ&cadastro=CEIS)")
            with col_c2:
                st.markdown("#### CNEP")
                st.caption("Cadastro Nacional de Empresas Punidas")
                st.markdown(f"[🔗 Consultar CNEP](https://portaldatransparencia.gov.br/sancoes/consulta?cpfCnpj={cnpj_limpo}&tipoPessoa=PJ&cadastro=CNEP)")
            with col_c3:
                st.markdown("#### CEPIM")
                st.caption("Cadastro de Entidades Privadas sem fins lucrativos Impedidas")
                st.markdown(f"[🔗 Consultar CEPIM](https://portaldatransparencia.gov.br/sancoes/consulta?cpfCnpj={cnpj_limpo}&tipoPessoa=PJ&cadastro=CEPIM)")

            st.divider()
            st.markdown("**Outras verificações:**")
            col_o1, col_o2 = st.columns(2)
            with col_o1:
                st.markdown(f"[📋 Receita Federal — Situação Cadastral](https://solucoes.receita.fazenda.gov.br/servicos/cnpjreva/cnpjreva_solicitacao.asp)")
            with col_o2:
                st.markdown(f"[📋 Certidão de Débitos Federais](https://solucoes.receita.fazenda.gov.br/Servicos/certidaointernet/PJ/Emitir)")
        else:
            st.warning("Digite um CNPJ válido (11 ou 14 dígitos)")

# Se tem dados com CNPJ de órgãos, mostrar resumo rápido
if 'cnpj_orgao' in df_filtrado.columns:
    cnpjs_unicos = df_filtrado['cnpj_orgao'].dropna().unique()
    cnpjs_validos = [c for c in cnpjs_unicos if str(c) not in ('N/A', '', 'nan')]
    if cnpjs_validos:
        st.caption(f"ℹ️ {len(cnpjs_validos)} CNPJ(s) distintos encontrados nos dados filtrados")

# ========== ABA PREÇOS (APRIMORADA) ==========
with tab_precos:
    st.markdown("### 📈 Histórico de Preços por Categoria CATMAT/CATSER")
    try:
        _precos_db = PrecosDB()
        _stats_precos = _precos_db.estatisticas_gerais()

        if _stats_precos.get("total_registros", 0) > 0:
            cp1, cp2, cp3 = st.columns(3)
            cp1.metric("Total de Registros", f"{_stats_precos['total_registros']:,}")
            cp2.metric("Categorias", f"{_stats_precos['categorias_distintas']:,}")
            cp3.metric("Valor Médio", f"R$ {_stats_precos.get('preco_medio_geral', 0):,.2f}")

            preco_sub1, preco_sub2, preco_sub3, preco_sub4 = st.tabs([
                "📋 Top Categorias", "📈 Tendências", "🏢 Comparar Órgãos", "🗺️ Preços por UF"
            ])

            with preco_sub1:
                st.markdown("#### Top Categorias por Volume")
                _cats = _precos_db.resumo_categorias(limite=15)
                if not _cats.empty:
                    st.dataframe(_cats, use_container_width=True)

                    st.markdown("#### Evolução de Preço por Categoria")
                    _codigos = _cats["codigo"].tolist()[:10]
                    _sel_cod = st.selectbox("Selecione a categoria:", _codigos, key="sel_cat_evo")
                    if _sel_cod:
                        df_evo = _precos_db.evolucao_por_categoria(_sel_cod)
                        if not df_evo.empty:
                            fig_evo = px.line(
                                df_evo, x="data_publicacao", y="valor_estimado",
                                title=f"Evolução — Categoria {_sel_cod}",
                                labels={"data_publicacao": "Data", "valor_estimado": "Valor (R$)"},
                                hover_data=["orgao", "uf"],
                            )
                            st.plotly_chart(fig_evo, use_container_width=True)

                            # Outliers
                            outliers = _precos_db.detectar_outliers(_sel_cod)
                            if not outliers.empty:
                                st.markdown("##### ⚠️ Outliers Detectados")
                                st.dataframe(outliers[["data_publicacao", "orgao", "uf", "valor_estimado", "desvio_percentual"]], use_container_width=True)
                else:
                    st.info("Nenhuma categoria registrada ainda.")

            with preco_sub2:
                st.markdown("#### 📈 Ranking de Variação de Preços")
                st.caption("Categorias com maior variação (alta ou baixa) ao longo do tempo")
                _ranking = _precos_db.ranking_categorias_variacao(limite=15)
                if _ranking:
                    for t in _ranking:
                        direcao_icon = "🔴" if t["direcao"] == "alta" else "🟢" if t["direcao"] == "baixa" else "🟡"
                        st.markdown(
                            f"{direcao_icon} **{t['codigo']}** — "
                            f"Variação: **{t['variacao_percentual']:+.1f}%** | "
                            f"R$ {t['preco_primeiro']:,.2f} → R$ {t['preco_ultimo']:,.2f} | "
                            f"{t['registros']} registros"
                        )
                else:
                    st.info("Dados insuficientes para calcular tendências (mínimo 2 registros por categoria).")

            with preco_sub3:
                st.markdown("#### 🏢 Comparação entre Órgãos")
                _cats2 = _precos_db.resumo_categorias(limite=30)
                if not _cats2.empty:
                    _cod_comp = st.selectbox(
                        "Categoria para comparar:",
                        _cats2["codigo"].tolist()[:15],
                        key="sel_cat_comp",
                    )
                    if _cod_comp:
                        df_comp = _precos_db.comparar_orgaos_categoria(_cod_comp)
                        if not df_comp.empty:
                            fig_comp = px.bar(
                                df_comp.head(10), x="preco_medio", y="orgao",
                                orientation="h",
                                title=f"Preço Médio por Órgão — {_cod_comp}",
                                labels={"preco_medio": "Preço Médio (R$)", "orgao": "Órgão"},
                                color="preco_medio",
                                color_continuous_scale="RdYlGn_r",
                            )
                            st.plotly_chart(fig_comp, use_container_width=True)
                            st.dataframe(df_comp, use_container_width=True)
                        else:
                            st.info("Sem dados para esta categoria.")

            with preco_sub4:
                st.markdown("#### 🗺️ Preços por UF")
                _cats3 = _precos_db.resumo_categorias(limite=30)
                if not _cats3.empty:
                    _cod_uf = st.selectbox(
                        "Categoria para ver por UF:",
                        _cats3["codigo"].tolist()[:15],
                        key="sel_cat_uf",
                    )
                    if _cod_uf:
                        df_uf = _precos_db.evolucao_por_uf(_cod_uf)
                        if not df_uf.empty:
                            fig_uf = px.bar(
                                df_uf, x="uf", y="preco_medio",
                                title=f"Preço Médio por UF — {_cod_uf}",
                                labels={"uf": "UF", "preco_medio": "Preço Médio (R$)"},
                                color="preco_medio",
                                color_continuous_scale="Blues",
                            )
                            st.plotly_chart(fig_uf, use_container_width=True)
                            st.dataframe(df_uf, use_container_width=True)
                        else:
                            st.info("Sem dados por UF para esta categoria.")
        else:
            st.info("📭 Nenhum dado de preço registrado. Execute uma coleta para popular o histórico.")
    except Exception as e:
        st.warning(f"Erro ao carregar preços: {e}")

# ========== ABA ANÁLISE PDF ==========
with tab_pdf:
    st.markdown("### 🔍 Análise de Editais (PDF)")
    st.caption("Baixa PDFs da API PNCP, extrai texto, tabelas, itens e valores")

    try:
        _analises_db = AnalisesDB()
        _stats_an = _analises_db.estatisticas()

        an1, an2 = st.columns(2)
        an1.metric("Editais Analisados", _stats_an.get("total_analisados", 0))
        an2.metric("Com Itens Extraídos", _stats_an.get("com_itens_extraidos", 0))

        pdf_sub1, pdf_sub2 = st.tabs(["📄 Analisar Edital", "📋 Análises Anteriores"])

        with pdf_sub1:
            st.markdown("#### Selecione um edital para analisar")

            # Permitir seleção do dataframe filtrado
            _editais_disponiveis = df_filtrado[
                (df_filtrado["cnpj_orgao"].notna()) &
                (df_filtrado["cnpj_orgao"] != "N/A") &
                (df_filtrado["numero_edital"].notna()) &
                (df_filtrado["numero_edital"] != "N/A")
            ].head(50)

            if not _editais_disponiveis.empty:
                _opcoes = [
                    f"{row['numero_edital']} — {row['orgao'][:50]}"
                    for _, row in _editais_disponiveis.iterrows()
                ]
                _sel_edital_pdf = st.selectbox("Edital:", _opcoes, key="sel_edital_pdf")

                if _sel_edital_pdf:
                    _idx_sel = _opcoes.index(_sel_edital_pdf)
                    _row_sel = _editais_disponiveis.iloc[_idx_sel]
                    _num_edital = str(_row_sel["numero_edital"])
                    _cnpj_sel = str(_row_sel["cnpj_orgao"])

                    # Check cache
                    _cached = _analises_db.obter_analise(_num_edital)
                    if _cached:
                        st.success(f"✅ Análise cacheada (processado em {_cached['processado_em'][:10]})")

                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        _analisar = st.button("🔍 Analisar PDF", key="btn_analisar_pdf")
                    with col_btn2:
                        _forcar = st.button("🔄 Re-analisar", key="btn_reanalisar_pdf")

                    if _analisar or _forcar:
                        with st.spinner("Baixando e analisando PDF... (pode levar alguns segundos)"):
                            _resultado_pdf = processar_edital_com_cache(
                                _cnpj_sel, _num_edital, forcar=_forcar
                            )

                        if _resultado_pdf and not _resultado_pdf.get("erro"):
                            analise = _resultado_pdf.get("analise", _resultado_pdf)

                            st.markdown("##### 📊 Resultado da Análise")

                            # Métricas principais
                            r1, r2, r3, r4 = st.columns(4)
                            valores = analise.get("valores_encontrados", [])
                            datas = analise.get("datas_encontradas", [])
                            reqs = analise.get("requisitos_tecnicos", [])
                            itens_pdf = _resultado_pdf.get("itens", analise.get("itens", []))

                            r1.metric("Valores Monetários", len(valores))
                            r2.metric("Datas", len(datas))
                            r3.metric("Requisitos TI", len(reqs))
                            r4.metric("Itens/Lotes", len(itens_pdf))

                            # Requisitos técnicos
                            if reqs:
                                st.markdown("##### 🖥️ Requisitos Técnicos de TI Encontrados")
                                st.write(", ".join(f"**{r}**" for r in reqs))

                            # Itens extraídos
                            if itens_pdf:
                                st.markdown("##### 📦 Itens/Lotes Extraídos")
                                import pandas as _pd_temp
                                df_itens = _pd_temp.DataFrame(itens_pdf)
                                cols_mostrar = [c for c in ["numero", "descricao", "quantidade", "unidade", "valor_total"] if c in df_itens.columns]
                                if cols_mostrar:
                                    st.dataframe(df_itens[cols_mostrar], use_container_width=True)

                            # Valores monetários
                            if valores:
                                with st.expander(f"💰 Valores encontrados ({len(valores)})"):
                                    st.write(", ".join(valores[:30]))

                            # CNPJs e emails
                            cnpjs = analise.get("cnpjs_encontrados", [])
                            emails = analise.get("emails_encontrados", [])
                            if cnpjs or emails:
                                with st.expander("📋 Contatos e CNPJs"):
                                    if cnpjs:
                                        st.write("**CNPJs:**", ", ".join(cnpjs[:10]))
                                    if emails:
                                        st.write("**Emails:**", ", ".join(emails[:10]))

                        elif _resultado_pdf:
                            st.error(f"Erro: {_resultado_pdf.get('erro', 'Falha desconhecida')}")
                        else:
                            st.error("Não foi possível processar o edital.")
            else:
                st.info("Nenhum edital com CNPJ disponível nos dados filtrados.")

        with pdf_sub2:
            st.markdown("#### 📋 Editais já analisados")
            _lista_an = _analises_db.listar_analises(limite=30)
            if _lista_an:
                for an in _lista_an:
                    reqs_str = ", ".join(an.get("requisitos_tecnicos", [])[:5]) or "—"
                    st.markdown(
                        f"**{an['numero_edital']}** — "
                        f"{an['qtd_arquivos']} arquivo(s), "
                        f"{an['qtd_itens']} item(ns) | "
                        f"TI: {reqs_str} | "
                        f"_{an['processado_em'][:10]}_"
                    )
            else:
                st.info("Nenhum edital analisado ainda. Use a aba 'Analisar Edital'.")
    except Exception as e:
        st.warning(f"Erro na análise de editais: {e}")

# ========== ABA MÉTRICAS ==========
with tab_metricas:
    st.markdown("### 📊 Monitoramento e Métricas")
    try:
        _met_db = MetricasDB()
        _stats_met = _met_db.estatisticas()

        cm1, cm2, cm3, cm4 = st.columns(4)
        cm1.metric("Total Eventos", f"{_stats_met.get('total_eventos', 0):,}")
        cm2.metric("Coletas", f"{_stats_met.get('total_coletas', 0):,}")
        cm3.metric("Erros", f"{_stats_met.get('total_erros', 0):,}")
        cm4.metric("Último Evento", _stats_met.get("ultimo_evento", "N/A"))

        m_sub1, m_sub2 = st.tabs(["📋 Eventos Recentes", "📡 Prometheus"])

        with m_sub1:
            _eventos = _met_db.ultimos_eventos(limite=50)
            if _eventos:
                df_ev = pd.DataFrame(_eventos)
                st.dataframe(df_ev, use_container_width=True)
            else:
                st.info("Nenhum evento registrado.")

        with m_sub2:
            st.markdown("#### Endpoint Prometheus")
            st.code("GET /metrics", language="text")
            st.caption("Configure no Prometheus: `scrape_configs` apontando para a API REST (porta 8000)")
            if st.button("🔄 Exibir métricas Prometheus"):
                _prom = _met_db.exportar_prometheus()
                st.code(_prom, language="text")

    except Exception as e:
        st.warning(f"Erro ao carregar métricas: {e}")

# ========== ABA AGENDADOR ==========
with tab_agenda:
    st.markdown("### ⏰ Agendamento de Tarefas")

    if "agendador" not in st.session_state:
        st.session_state.agendador = AgendadorTarefas()

    _ag = st.session_state.agendador

    ca1, ca2 = st.columns(2)
    with ca1:
        if _ag.ativo:
            st.success("✅ Scheduler ativo")
            if st.button("⏹️ Parar Scheduler"):
                _ag.parar()
                st.rerun()
        else:
            st.warning("⏸️ Scheduler inativo")
            if st.button("▶️ Iniciar Scheduler"):
                ok = _ag.iniciar()
                if ok:
                    st.success("Scheduler iniciado!")
                else:
                    st.error("APScheduler não instalado. Execute: pip install apscheduler")
                st.rerun()

    with ca2:
        st.markdown("#### Configuração")
        _cfg = _ag.config
        for nome, params in _cfg.items():
            st.checkbox(
                f"{params.get('descricao', nome)}",
                value=params.get("habilitado", True),
                key=f"cfg_{nome}",
                disabled=True,
            )

    if _ag.ativo:
        st.markdown("#### Tarefas Agendadas")
        _jobs = _ag.listar_jobs()
        if _jobs:
            df_jobs = pd.DataFrame(_jobs)
            st.dataframe(df_jobs, use_container_width=True)

        st.markdown("#### Execução Manual")
        cj1, cj2, cj3, cj4 = st.columns(4)
        with cj1:
            if st.button("🔄 Coleta PNCP"):
                with st.spinner("Coletando..."):
                    _ag.executar_agora("coleta_pncp")
                st.success("Coleta PNCP concluída")
        with cj2:
            if st.button("🗺️ Portais Estaduais"):
                with st.spinner("Coletando portais..."):
                    _ag.executar_agora("coleta_estaduais")
                st.success("Coleta estadual concluída")
        with cj3:
            if st.button("📊 Exportar Métricas"):
                _ag.executar_agora("exportar_metricas")
                st.success("Métricas exportadas")
        with cj4:
            if st.button("🧹 Limpar Cache"):
                _ag.executar_agora("limpeza_cache")
                st.success("Cache limpo")

# ========== ABA 14: CRM ==========
with tab_crm:
    st.markdown("### 📊 Pipeline de Propostas (CRM)")

    if "db_crm" not in st.session_state:
        st.session_state.db_crm = CrmDB()
    _crm = st.session_state.db_crm

    crm_sub1, crm_sub2, crm_sub3 = st.tabs(["📋 Pipeline", "➕ Nova Proposta", "📈 Métricas"])

    with crm_sub1:
        resumo = _crm.pipeline_resumo()
        por_estagio = resumo.get("por_estagio", {})
        if por_estagio:
            cols_pipe = st.columns(min(len(por_estagio), 6))
            for i, (estagio_nome, qtd) in enumerate(por_estagio.items()):
                with cols_pipe[i % len(cols_pipe)]:
                    st.metric(estagio_nome.capitalize(), qtd)

        st.markdown("---")
        estagio_filtro = st.selectbox(
            "Filtrar por estágio",
            ["Todos", "prospeccao", "analise", "decisao", "elaborando",
             "enviada", "aguardando", "vencida", "perdida", "desistencia"],
            key="crm_filtro_estagio",
        )
        filtro = None if estagio_filtro == "Todos" else estagio_filtro
        propostas = _crm.listar_pipeline(estagio=filtro)
        if propostas:
            df_prop = pd.DataFrame(propostas)
            colunas_exibir = ["id", "licitacao_id", "orgao", "objeto", "estagio", "valor_estimado", "responsavel", "criado_em"]
            colunas_presentes = [c for c in colunas_exibir if c in df_prop.columns]
            st.dataframe(df_prop[colunas_presentes], use_container_width=True)

            st.markdown("#### Mover Proposta")
            mc1, mc2, mc3 = st.columns(3)
            with mc1:
                prop_id = st.number_input("ID da Proposta", min_value=1, step=1, key="crm_move_id")
            with mc2:
                novo_estagio = st.selectbox(
                    "Novo Estágio",
                    ["prospeccao", "analise", "decisao", "elaborando",
                     "enviada", "aguardando", "vencida", "perdida", "desistencia"],
                    key="crm_novo_estagio",
                )
            with mc3:
                obs_move = st.text_input("Observação", key="crm_obs_move")

            if st.button("🔄 Mover Estágio", key="crm_btn_move"):
                try:
                    ok = _crm.mover_estagio(int(prop_id), novo_estagio, observacao=obs_move or "")
                    if ok:
                        st.success(f"Proposta {prop_id} movida para {novo_estagio}")
                    else:
                        st.error("Não foi possível mover (proposta não encontrada ou estágio final)")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
        else:
            st.info("Nenhuma proposta cadastrada ainda.")

    with crm_sub2:
        st.markdown("#### Cadastrar Nova Proposta")
        with st.form("form_nova_proposta"):
            np_lic = st.text_input("ID da Licitação *")
            np_orgao = st.text_input("Órgão *")
            np_objeto = st.text_area("Objeto *")
            np_valor = st.number_input("Valor Estimado (R$)", min_value=0.0, format="%.2f")
            np_resp = st.text_input("Responsável")
            np_notas = st.text_area("Notas")
            submitted = st.form_submit_button("💾 Criar Proposta")
            if submitted:
                if not np_lic or not np_orgao or not np_objeto:
                    st.error("Preencha os campos obrigatórios (*)")
                else:
                    pid = _crm.criar_proposta(
                        numero_edital=np_lic,
                        orgao=np_orgao,
                        objeto=np_objeto,
                        valor_estimado=np_valor if np_valor > 0 else 0,
                        responsavel=np_resp or "",
                        notas=np_notas or "",
                    )
                    st.success(f"Proposta #{pid} criada!")
                    st.rerun()

    with crm_sub3:
        conversao = _crm.taxa_conversao()
        kc1, kc2, kc3 = st.columns(3)
        with kc1:
            st.metric("Total de Propostas", conversao.get("total_propostas", 0))
        with kc2:
            st.metric("Vencidas", conversao.get("vencidas", 0))
        with kc3:
            taxa = conversao.get("taxa_conversao", 0)
            st.metric("Taxa de Conversão", f"{taxa:.1f}%")

        pipeline_data = _crm.pipeline_resumo()
        por_estagio = pipeline_data.get("por_estagio", {})
        if por_estagio:
            df_pipe = pd.DataFrame([
                {"estagio": k, "quantidade": v} for k, v in por_estagio.items()
            ])
            fig_pipe = px.bar(
                df_pipe, x="estagio", y="quantidade",
                title="Propostas por Estágio",
                color="estagio",
            )
            st.plotly_chart(fig_pipe, use_container_width=True)

# ==================== RESUMO FINAL ====================

st.divider()

st.markdown("""
### 📌 Dicas de Uso

1. **Filtros:** Use a barra lateral para refinar por estado, órgão e valor
2. **Busca:** Na aba "Dados", use a busca rápida para encontrar termos específicos  
3. **Exportação:** Baixe dados em CSV ou Excel para análises adicionais
4. **Atualização:** Execute `python pncp_radar_ti_plus.py` para coletar novos dados
5. **Fontes Complementares:** Acesse a aba "Fontes Complementares" para dados de Diários Oficiais, Portal da Transparência e Compras.gov.br

### 🔗 Links Úteis

- [Portal PNCP Oficial](https://pncp.gov.br)
- [API PNCP Documentação](https://pncp.gov.br/api/consulta)
- [Querido Diário](https://queridodiario.ok.org.br)
- [Portal da Transparência](https://portaldatransparencia.gov.br)
- [Compras.gov.br](https://compras.dados.gov.br)
- [Streamlit Docs](https://docs.streamlit.io)

""")

