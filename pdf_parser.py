"""
Extração de texto de editais em PDF.
Baixa documentos da API PNCP e extrai conteúdo com pdfplumber.
Inclui extração de tabelas, itens/lotes e análise estruturada.
"""

import os
import re
import logging
import sqlite3
import json
from contextlib import closing
from datetime import datetime
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

PASTA_PDFS = os.path.join("dados", "editais_pdf")
DB_ANALISES = os.path.join("dados", "analises_editais.db")
TIMEOUT = 60


def _garantir_pasta():
    os.makedirs(PASTA_PDFS, exist_ok=True)


def listar_arquivos_edital(cnpj_orgao: str, numero_edital: str) -> List[Dict]:
    """Consulta a API PNCP para obter lista de arquivos de um edital."""
    if not cnpj_orgao or not numero_edital:
        return []
    cnpj = str(cnpj_orgao).replace(".", "").replace("/", "").replace("-", "").strip()
    seq = str(numero_edital).replace("/", "-").strip()
    url = f"https://pncp.gov.br/api/pncp/v1/orgaos/{cnpj}/compras/{seq}/arquivos"
    try:
        resp = requests.get(url, timeout=TIMEOUT, headers={"Accept": "application/json"})
        if resp.status_code == 200:
            dados = resp.json()
            if isinstance(dados, list):
                return dados
            return dados.get("data", dados.get("arquivos", []))
        logger.warning("API retornou %d para %s", resp.status_code, url)
    except Exception as e:
        logger.warning("Erro ao listar arquivos: %s", e)
    return []


def baixar_pdf(url_download: str, nome_arquivo: str = "") -> Optional[str]:
    """Baixa um PDF e retorna o caminho local."""
    _garantir_pasta()
    if not nome_arquivo:
        nome_arquivo = url_download.split("/")[-1].split("?")[0] or "edital.pdf"
    nome_arquivo = re.sub(r'[^\w.\-]', '_', nome_arquivo)
    caminho = os.path.join(PASTA_PDFS, nome_arquivo)
    if os.path.exists(caminho):
        return caminho
    try:
        resp = requests.get(url_download, timeout=TIMEOUT, stream=True)
        if resp.status_code == 200:
            with open(caminho, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            logger.info("PDF baixado: %s", caminho)
            return caminho
        logger.warning("Download retornou %d", resp.status_code)
    except Exception as e:
        logger.warning("Erro ao baixar PDF: %s", e)
    return None


def extrair_texto_pdf(caminho_pdf: str) -> str:
    """Extrai texto de um arquivo PDF usando pdfplumber."""
    try:
        import pdfplumber
    except ImportError:
        logger.error("pdfplumber não instalado. Execute: pip install pdfplumber")
        return ""
    if not os.path.exists(caminho_pdf):
        return ""
    texto_paginas = []
    try:
        with pdfplumber.open(caminho_pdf) as pdf:
            for pagina in pdf.pages:
                texto = pagina.extract_text()
                if texto:
                    texto_paginas.append(texto)
        return "\n\n".join(texto_paginas)
    except Exception as e:
        logger.warning("Erro ao extrair texto de %s: %s", caminho_pdf, e)
        return ""


def extrair_valores_do_texto(texto: str) -> Dict:
    """Extrai informações estruturadas do texto de um edital."""
    resultado = {
        "valores_encontrados": [],
        "datas_encontradas": [],
        "cnpjs_encontrados": [],
        "emails_encontrados": [],
        "requisitos_tecnicos": [],
    }
    if not texto:
        return resultado

    # Valores monetários (R$ X.XXX,XX)
    padrao_valor = r'R\$\s*[\d.,]+(?:\.\d{3})*(?:,\d{2})?'
    resultado["valores_encontrados"] = list(set(re.findall(padrao_valor, texto)))

    # Datas DD/MM/YYYY
    padrao_data = r'\d{2}/\d{2}/\d{4}'
    resultado["datas_encontradas"] = list(set(re.findall(padrao_data, texto)))

    # CNPJs
    padrao_cnpj = r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}'
    resultado["cnpjs_encontrados"] = list(set(re.findall(padrao_cnpj, texto)))

    # Emails
    padrao_email = r'[\w.+-]+@[\w-]+\.[\w.-]+'
    resultado["emails_encontrados"] = list(set(re.findall(padrao_email, texto)))

    # Termos técnicos de TI
    termos_ti = [
        "SLA", "LGPD", "uptime", "disponibilidade", "backup",
        "cloud", "nuvem", "data center", "firewall", "antivírus",
        "certificação", "ITIL", "DevOps", "ágil", "scrum",
        "microsserviço", "API", "REST", "integração",
    ]
    texto_lower = texto.lower()
    for termo in termos_ti:
        if termo.lower() in texto_lower:
            resultado["requisitos_tecnicos"].append(termo)

    return resultado


def processar_edital_completo(cnpj_orgao: str, numero_edital: str) -> Dict:
    """
    Pipeline completo: lista arquivos → baixa PDFs → extrai texto → analisa.

    Returns:
        Dicionário com texto e análise do edital.
    """
    resultado = {
        "numero_edital": numero_edital,
        "arquivos": [],
        "texto_completo": "",
        "analise": {},
        "erro": None,
    }

    arquivos = listar_arquivos_edital(cnpj_orgao, numero_edital)
    if not arquivos:
        resultado["erro"] = "Nenhum arquivo encontrado na API"
        return resultado

    textos = []
    for arq in arquivos:
        url = arq.get("url", arq.get("uri", ""))
        titulo = arq.get("titulo", arq.get("nomeArquivo", ""))
        tipo = arq.get("tipoDocumento", "")
        resultado["arquivos"].append({"titulo": titulo, "tipo": tipo, "url": url})

        if not url:
            continue
        # Baixar apenas PDFs
        if url.lower().endswith(".pdf") or "pdf" in tipo.lower():
            nome = f"{numero_edital}_{titulo}".replace("/", "_")[:80] + ".pdf"
            caminho = baixar_pdf(url, nome)
            if caminho:
                texto = extrair_texto_pdf(caminho)
                if texto:
                    textos.append(texto)
                tabelas = extrair_tabelas_pdf(caminho)
                if tabelas:
                    resultado.setdefault("tabelas", []).extend(tabelas)

    resultado["texto_completo"] = "\n\n---\n\n".join(textos)
    resultado["analise"] = extrair_valores_do_texto(resultado["texto_completo"])
    resultado["itens"] = extrair_itens_licitacao(resultado["texto_completo"])
    return resultado


# ========== EXTRAÇÃO DE TABELAS ==========

def extrair_tabelas_pdf(caminho_pdf: str) -> List[List[List[str]]]:
    """Extrai tabelas de um PDF usando pdfplumber."""
    try:
        import pdfplumber
    except ImportError:
        return []
    if not os.path.exists(caminho_pdf):
        return []
    tabelas = []
    try:
        with pdfplumber.open(caminho_pdf) as pdf:
            for pagina in pdf.pages:
                for tabela in (pagina.extract_tables() or []):
                    if tabela and len(tabela) > 1:
                        tabelas.append(tabela)
    except Exception as e:
        logger.warning("Erro ao extrair tabelas de %s: %s", caminho_pdf, e)
    return tabelas


def extrair_itens_licitacao(texto: str) -> List[Dict]:
    """
    Extrai itens/lotes do texto do edital usando padrões comuns.
    Retorna lista de dicts com item, descricao, quantidade, unidade, valor_unitario, valor_total.
    """
    itens = []
    if not texto:
        return itens

    # Padrão: "Item N" ou "Lote N" seguido de descrição e valores
    padrao_item = re.compile(
        r'(?:item|lote|grupo)\s*(?:n[°ºo.]?\s*)?(\d+)'
        r'[:\s\-–]+(.+?)(?=(?:item|lote|grupo)\s*(?:n[°ºo.]?\s*)?\d+|$)',
        re.IGNORECASE | re.DOTALL,
    )

    # Padrão de valor monetário
    padrao_valor = re.compile(r'R\$\s*([\d.,]+)')
    # Padrão de quantidade
    padrao_qtd = re.compile(
        r'(?:qtd|quant|quantidade)[.:\s]*(\d+[\d.]*)',
        re.IGNORECASE,
    )
    # Padrão de unidade
    padrao_unid = re.compile(
        r'(?:un|unid|unidade|licen[çc]a|servi[çc]o|m[eê]s|hora|diária|pç)',
        re.IGNORECASE,
    )

    for m in padrao_item.finditer(texto):
        num_item = m.group(1)
        desc_bloco = m.group(2).strip()
        # Limitar descrição a 500 chars
        desc = desc_bloco[:500]

        valores = padrao_valor.findall(desc_bloco)
        qtd_match = padrao_qtd.search(desc_bloco)
        unid_match = padrao_unid.search(desc_bloco)

        item = {
            "numero": int(num_item),
            "descricao": re.sub(r'\s+', ' ', desc).strip()[:300],
            "quantidade": int(qtd_match.group(1).replace(".", "")) if qtd_match else None,
            "unidade": unid_match.group(0) if unid_match else None,
            "valores_encontrados": valores[:5],
        }

        # Tentar identificar valor unitário e total
        if len(valores) >= 2:
            try:
                v1 = float(valores[-2].replace(".", "").replace(",", "."))
                v2 = float(valores[-1].replace(".", "").replace(",", "."))
                if v2 > v1:
                    item["valor_unitario"] = v1
                    item["valor_total"] = v2
                else:
                    item["valor_unitario"] = v2
                    item["valor_total"] = v1
            except ValueError:
                pass
        elif len(valores) == 1:
            try:
                item["valor_total"] = float(valores[0].replace(".", "").replace(",", "."))
            except ValueError:
                pass

        itens.append(item)

    return itens


# ========== CACHE DE ANÁLISES (SQLite) ==========

class AnalisesDB:
    """Cache de análises de editais processados."""

    def __init__(self, db_path: str = DB_ANALISES):
        self.db_path = db_path
        d = os.path.dirname(db_path)
        if d and not os.path.exists(d):
            os.makedirs(d)
        self._criar_tabelas()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _criar_tabelas(self):
        with closing(self._conn()) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS analises (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero_edital TEXT NOT NULL UNIQUE,
                    cnpj_orgao TEXT DEFAULT '',
                    qtd_arquivos INTEGER DEFAULT 0,
                    qtd_itens INTEGER DEFAULT 0,
                    valores_encontrados TEXT DEFAULT '[]',
                    datas_encontradas TEXT DEFAULT '[]',
                    cnpjs_encontrados TEXT DEFAULT '[]',
                    emails_encontrados TEXT DEFAULT '[]',
                    requisitos_tecnicos TEXT DEFAULT '[]',
                    itens_json TEXT DEFAULT '[]',
                    texto_resumo TEXT DEFAULT '',
                    processado_em TIMESTAMP NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_analises_edital
                ON analises(numero_edital)
            """)
            conn.commit()

    def salvar_analise(self, numero_edital: str, cnpj_orgao: str, resultado: Dict) -> bool:
        """Salva resultado de análise no cache."""
        analise = resultado.get("analise", {})
        itens = resultado.get("itens", [])
        with closing(self._conn()) as conn:
            try:
                conn.execute("""
                    INSERT OR REPLACE INTO analises
                    (numero_edital, cnpj_orgao, qtd_arquivos, qtd_itens,
                     valores_encontrados, datas_encontradas, cnpjs_encontrados,
                     emails_encontrados, requisitos_tecnicos, itens_json,
                     texto_resumo, processado_em)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    numero_edital,
                    cnpj_orgao,
                    len(resultado.get("arquivos", [])),
                    len(itens),
                    json.dumps(analise.get("valores_encontrados", [])[:50]),
                    json.dumps(analise.get("datas_encontradas", [])[:30]),
                    json.dumps(analise.get("cnpjs_encontrados", [])[:20]),
                    json.dumps(analise.get("emails_encontrados", [])[:20]),
                    json.dumps(analise.get("requisitos_tecnicos", [])[:30]),
                    json.dumps(itens[:50]),
                    resultado.get("texto_completo", "")[:2000],
                    datetime.now().isoformat(),
                ))
                conn.commit()
                return True
            except Exception as e:
                logger.warning("Erro ao salvar análise: %s", e)
                return False

    def obter_analise(self, numero_edital: str) -> Optional[Dict]:
        """Retorna análise cacheada se disponível."""
        with closing(self._conn()) as conn:
            row = conn.execute(
                "SELECT * FROM analises WHERE numero_edital = ?", (numero_edital,)
            ).fetchone()
        if not row:
            return None
        return {
            "numero_edital": row["numero_edital"],
            "cnpj_orgao": row["cnpj_orgao"],
            "qtd_arquivos": row["qtd_arquivos"],
            "qtd_itens": row["qtd_itens"],
            "valores_encontrados": json.loads(row["valores_encontrados"]),
            "datas_encontradas": json.loads(row["datas_encontradas"]),
            "cnpjs_encontrados": json.loads(row["cnpjs_encontrados"]),
            "emails_encontrados": json.loads(row["emails_encontrados"]),
            "requisitos_tecnicos": json.loads(row["requisitos_tecnicos"]),
            "itens": json.loads(row["itens_json"]),
            "texto_resumo": row["texto_resumo"],
            "processado_em": row["processado_em"],
        }

    def listar_analises(self, limite: int = 50) -> List[Dict]:
        """Lista análises recentes."""
        with closing(self._conn()) as conn:
            rows = conn.execute("""
                SELECT numero_edital, cnpj_orgao, qtd_arquivos, qtd_itens,
                       requisitos_tecnicos, processado_em
                FROM analises ORDER BY processado_em DESC LIMIT ?
            """, (limite,)).fetchall()
        return [
            {
                "numero_edital": r["numero_edital"],
                "cnpj_orgao": r["cnpj_orgao"],
                "qtd_arquivos": r["qtd_arquivos"],
                "qtd_itens": r["qtd_itens"],
                "requisitos_tecnicos": json.loads(r["requisitos_tecnicos"]),
                "processado_em": r["processado_em"],
            }
            for r in rows
        ]

    def estatisticas(self) -> Dict:
        """Retorna estatísticas de análises."""
        with closing(self._conn()) as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM analises")
            total = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM analises WHERE qtd_itens > 0")
            com_itens = cur.fetchone()[0]
        return {"total_analisados": total, "com_itens_extraidos": com_itens}


def processar_edital_com_cache(
    cnpj_orgao: str, numero_edital: str, forcar: bool = False
) -> Dict:
    """
    Processa edital com cache: se já analisado, retorna do DB.
    Se forcar=True, reprocessa mesmo existindo cache.
    """
    db = AnalisesDB()
    if not forcar:
        cached = db.obter_analise(numero_edital)
        if cached:
            cached["_cache"] = True
            return cached

    resultado = processar_edital_completo(cnpj_orgao, numero_edital)
    if resultado and not resultado.get("erro"):
        db.salvar_analise(numero_edital, cnpj_orgao, resultado)
    return resultado
