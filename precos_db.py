"""
Histórico de preços por categoria CATMAT/CATSER.
Armazena preços por código de classificação para análise de tendências.
"""

import sqlite3
import os
import logging
from contextlib import closing
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd

logger = logging.getLogger(__name__)

DB_PATH = os.path.join("dados", "precos.db")


class PrecosDB:
    """Gerencia o histórico de preços por categoria."""

    def __init__(self, db_path: str = DB_PATH):
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
                CREATE TABLE IF NOT EXISTS precos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero_edital TEXT NOT NULL,
                    codigo_catmat_catser TEXT NOT NULL,
                    categoria_item TEXT DEFAULT '',
                    objeto TEXT DEFAULT '',
                    valor_estimado REAL DEFAULT 0,
                    orgao TEXT DEFAULT '',
                    uf TEXT DEFAULT '',
                    data_publicacao TEXT DEFAULT '',
                    registrado_em TIMESTAMP NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_precos_codigo
                ON precos(codigo_catmat_catser)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_precos_edital
                ON precos(numero_edital)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_precos_data
                ON precos(data_publicacao)
            """)
            conn.commit()

    def registrar_precos(self, df: pd.DataFrame) -> int:
        """Registra preços a partir de um DataFrame de licitações."""
        if df.empty:
            return 0
        cols_necessarias = {"numero_edital", "valor_estimado"}
        if not cols_necessarias.issubset(set(df.columns)):
            return 0

        with closing(self._conn()) as conn:
            agora = datetime.now().isoformat()
            inseridos = 0

            for _, row in df.iterrows():
                codigo = str(row.get("codigo_catmat_catser", "N/A"))
                edital = str(row.get("numero_edital", ""))
                valor = float(row.get("valor_estimado", 0))
                if not edital or valor <= 0:
                    continue
                existe = conn.execute(
                    "SELECT 1 FROM precos WHERE numero_edital = ?", (edital,)
                ).fetchone()
                if existe:
                    continue

                conn.execute("""
                    INSERT INTO precos
                    (numero_edital, codigo_catmat_catser, categoria_item, objeto,
                     valor_estimado, orgao, uf, data_publicacao, registrado_em)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    edital,
                    codigo,
                    str(row.get("categoria_item", "")),
                    str(row.get("objeto", ""))[:500],
                    valor,
                    str(row.get("orgao", "")),
                    str(row.get("uf", "")),
                    str(row.get("data_publicacao", "")),
                    agora,
                ))
                inseridos += 1

            conn.commit()
        if inseridos:
            logger.info("Registrados %d preços no histórico", inseridos)
        return inseridos

    def evolucao_por_categoria(self, codigo: str) -> pd.DataFrame:
        """Retorna evolução de preços para uma categoria CATMAT/CATSER."""
        with closing(self._conn()) as conn:
            df = pd.read_sql_query("""
                SELECT data_publicacao, valor_estimado, orgao, uf, objeto, numero_edital
                FROM precos
                WHERE codigo_catmat_catser = ?
                ORDER BY data_publicacao
            """, conn, params=(codigo,))
        if not df.empty:
            df["data_publicacao"] = pd.to_datetime(df["data_publicacao"], errors="coerce")
        return df

    def resumo_categorias(self, limite: int = 30) -> pd.DataFrame:
        """Top categorias por quantidade de registros com estatísticas."""
        with closing(self._conn()) as conn:
            df = pd.read_sql_query("""
                SELECT
                    codigo_catmat_catser AS codigo,
                    categoria_item AS categoria,
                    COUNT(*) AS quantidade,
                    ROUND(AVG(valor_estimado), 2) AS preco_medio,
                    ROUND(MIN(valor_estimado), 2) AS preco_min,
                    ROUND(MAX(valor_estimado), 2) AS preco_max
                FROM precos
                WHERE valor_estimado > 0
                GROUP BY codigo_catmat_catser
                ORDER BY quantidade DESC
                LIMIT ?
            """, conn, params=(limite,))
        return df

    def estatisticas_gerais(self) -> Dict:
        """Retorna estatísticas gerais do histórico de preços."""
        with closing(self._conn()) as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM precos")
            total = cur.fetchone()[0]
            cur.execute("SELECT COUNT(DISTINCT codigo_catmat_catser) FROM precos WHERE codigo_catmat_catser != 'N/A'")
            categorias = cur.fetchone()[0]
            cur.execute("SELECT ROUND(AVG(valor_estimado), 2) FROM precos WHERE valor_estimado > 0")
            media = cur.fetchone()[0] or 0
        return {"total_registros": total, "categorias_distintas": categorias, "preco_medio_geral": media}

    def comparar_orgaos_categoria(self, codigo: str) -> pd.DataFrame:
        """Compara preços entre órgãos para uma mesma categoria CATMAT/CATSER."""
        with closing(self._conn()) as conn:
            df = pd.read_sql_query("""
                SELECT orgao,
                       COUNT(*) AS quantidade,
                       ROUND(AVG(valor_estimado), 2) AS preco_medio,
                       ROUND(MIN(valor_estimado), 2) AS preco_min,
                       ROUND(MAX(valor_estimado), 2) AS preco_max
                FROM precos
                WHERE codigo_catmat_catser = ? AND valor_estimado > 0
                GROUP BY orgao
                ORDER BY preco_medio DESC
            """, conn, params=(codigo,))
        return df

    def detectar_outliers(self, codigo: str, fator: float = 2.0) -> pd.DataFrame:
        """
        Detecta outliers de preço para uma categoria.
        Outlier = valor fora de (média ± fator * desvio padrão).
        """
        df = self.evolucao_por_categoria(codigo)
        if df.empty or len(df) < 3:
            return pd.DataFrame()
        media = df["valor_estimado"].mean()
        desvio = df["valor_estimado"].std()
        limite_inf = media - fator * desvio
        limite_sup = media + fator * desvio
        outliers = df[
            (df["valor_estimado"] < limite_inf) | (df["valor_estimado"] > limite_sup)
        ].copy()
        outliers["preco_medio_categoria"] = round(media, 2)
        outliers["desvio_percentual"] = round(
            ((outliers["valor_estimado"] - media) / media) * 100, 1
        )
        return outliers

    def tendencia_categoria(self, codigo: str) -> Optional[Dict]:
        """
        Calcula tendência de preço para uma categoria.
        Retorna variação percentual, direção e estatísticas.
        """
        df = self.evolucao_por_categoria(codigo)
        if df.empty or len(df) < 2:
            return None
        df = df.sort_values("data_publicacao")
        valores = df["valor_estimado"].dropna()
        if len(valores) < 2:
            return None
        primeiro = valores.iloc[0]
        ultimo = valores.iloc[-1]
        variacao = ((ultimo - primeiro) / primeiro * 100) if primeiro > 0 else 0
        return {
            "codigo": codigo,
            "registros": len(valores),
            "preco_primeiro": round(primeiro, 2),
            "preco_ultimo": round(ultimo, 2),
            "preco_medio": round(valores.mean(), 2),
            "preco_min": round(valores.min(), 2),
            "preco_max": round(valores.max(), 2),
            "variacao_percentual": round(variacao, 1),
            "direcao": "alta" if variacao > 5 else "baixa" if variacao < -5 else "estável",
        }

    def ranking_categorias_variacao(self, limite: int = 20) -> List[Dict]:
        """Retorna categorias com maior variação de preço (alta e baixa)."""
        resumo = self.resumo_categorias(limite=100)
        if resumo.empty:
            return []
        tendencias = []
        for _, row in resumo.iterrows():
            t = self.tendencia_categoria(row["codigo"])
            if t and t["registros"] >= 2:
                t["categoria"] = row.get("categoria", "")
                tendencias.append(t)
        tendencias.sort(key=lambda x: abs(x["variacao_percentual"]), reverse=True)
        return tendencias[:limite]

    def evolucao_por_uf(self, codigo: str) -> pd.DataFrame:
        """Evolução de preços por UF para uma categoria."""
        with closing(self._conn()) as conn:
            df = pd.read_sql_query("""
                SELECT uf,
                       COUNT(*) AS quantidade,
                       ROUND(AVG(valor_estimado), 2) AS preco_medio,
                       ROUND(MIN(valor_estimado), 2) AS preco_min,
                       ROUND(MAX(valor_estimado), 2) AS preco_max
                FROM precos
                WHERE codigo_catmat_catser = ? AND valor_estimado > 0 AND uf != ''
                GROUP BY uf
                ORDER BY preco_medio DESC
            """, conn, params=(codigo,))
        return df
