import requests
import pandas as pd
from datetime import datetime, timedelta

BASE_URL = "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao"

MAX_ITENS = 1000
TAMANHO_PAGINA = 50

DATA_FINAL = datetime.now()
DATA_INICIAL = DATA_FINAL - timedelta(days=7)

DATA_FINAL_STR = DATA_FINAL.strftime("%Y%m%d")
DATA_INICIAL_STR = DATA_INICIAL.strftime("%Y%m%d")

KEYWORDS_TI = [
    "software","sistema","aplicativo","app","desenvolvimento",
    "tecnologia da informação","ti","api","cloud","servidor",
    "infraestrutura","rede","banco de dados","sql","erp",
    "dashboard","bi","data","segurança da informação",
    "cibersegurança","help desk","service desk","lgpd"
]


def is_ti(texto):
    if not texto:
        return False
    texto = texto.lower()
    return any(k in texto for k in KEYWORDS_TI)


def get_lista(payload):

    if isinstance(payload, list):
        return payload

    if isinstance(payload, dict):

        if "data" in payload:
            return payload["data"]

        for v in payload.values():
            if isinstance(v, list):
                return v

    return []


def buscar_licitacoes():

    resultados = []

    pagina = 1

    while len(resultados) < MAX_ITENS:

        params = {
            "dataInicial": DATA_INICIAL_STR,
            "dataFinal": DATA_FINAL_STR,
            "pagina": pagina,
            "tamanhoPagina": TAMANHO_PAGINA
        }

        r = requests.get(BASE_URL, params=params)

        if r.status_code == 204:
            print("Fim da paginação")
            break

        if r.status_code != 200:
            print("Erro API:", r.status_code)
            break

        itens = get_lista(r.json())

        if not itens:
            break

        for it in itens:

            objeto = (
                it.get("objeto")
                or it.get("descricaoObjeto")
                or it.get("objetoCompra")
                or ""
            )

            if not is_ti(objeto):
                continue

            orgao = it.get("orgaoEntidade", {}).get("razaoSocial", "")

            valor = (
                it.get("valorTotalEstimado")
                or it.get("valorEstimado")
                or ""
            )

            numero = (
                it.get("numeroControlePNCP")
                or it.get("numeroControlePncp")
                or ""
            )

            link = f"https://pncp.gov.br/app/editais?q={numero}"

            resultados.append({
                "orgao": orgao,
                "objeto": objeto,
                "valor_estimado": valor,
                "numero_controle": numero,
                "link": link
            })

            if len(resultados) >= MAX_ITENS:
                break

        pagina += 1

    return resultados


def gerar_excel(dados):

    df = pd.DataFrame(dados)

    df = df.drop_duplicates(subset=["numero_controle"])

    nome = "radar_licitacoes_TI.xlsx"

    df.to_excel(nome, index=False)

    print("Excel gerado:", nome)
    print("Total licitações TI:", len(df))


def main():

    print("Buscando licitações de TI...")

    dados = buscar_licitacoes()

    gerar_excel(dados)


if __name__ == "__main__":
    main()