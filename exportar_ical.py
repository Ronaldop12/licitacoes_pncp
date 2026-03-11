"""
Exportação de licitações para formato iCalendar (.ics).
Permite importar datas de abertura/encerramento em Google Calendar, Outlook, etc.
"""

from datetime import datetime, timedelta
from typing import List, Dict
import re


def _sanitizar_texto(texto: str, max_len: int = 200) -> str:
    """Remove caracteres problemáticos para iCal."""
    if not texto:
        return ""
    texto = str(texto).replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,")
    texto = re.sub(r"\r?\n", "\\n", texto)
    return texto[:max_len]


def _formatar_data_ical(dt) -> str:
    """Formata datetime para o padrão iCal (YYYYMMDDTHHMMSS)."""
    if isinstance(dt, str):
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
            try:
                dt = datetime.strptime(dt.split(".")[0][:19], fmt)
                break
            except ValueError:
                continue
        else:
            return ""
    if not isinstance(dt, datetime):
        return ""
    return dt.strftime("%Y%m%dT%H%M%S")


def gerar_ics(licitacoes: List[Dict], tipo_evento: str = "abertura") -> str:
    """
    Gera conteúdo .ics a partir de uma lista de licitações.

    Args:
        licitacoes: Lista de dicts com campos padrão do radar.
        tipo_evento: 'abertura' para data_abertura ou 'encerramento' para data_encerramento.

    Returns:
        String com conteúdo .ics pronto para download.
    """
    campo_data = "data_abertura" if tipo_evento == "abertura" else "data_encerramento"
    label = "Abertura" if tipo_evento == "abertura" else "Encerramento"

    linhas = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//RadarLicitacoesTI//BR",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:Licitações TI - {label}",
    ]

    agora = datetime.now().strftime("%Y%m%dT%H%M%S")

    for lic in licitacoes:
        data_str = lic.get(campo_data, "")
        dtstart = _formatar_data_ical(data_str)
        if not dtstart:
            continue

        # Evento de 1 hora por padrão
        try:
            dt_obj = datetime.strptime(dtstart, "%Y%m%dT%H%M%S")
            dtend = (dt_obj + timedelta(hours=1)).strftime("%Y%m%dT%H%M%S")
        except ValueError:
            continue

        orgao = _sanitizar_texto(lic.get("orgao", ""))
        objeto = _sanitizar_texto(lic.get("objeto", ""), 500)
        edital = str(lic.get("numero_edital", ""))
        uf = str(lic.get("uf", ""))
        valor = lic.get("valor_estimado", 0)
        link = str(lic.get("link_edital", ""))

        summary = f"[{label}] {orgao[:60]} - {uf}"
        description = (
            f"Edital: {edital}\\n"
            f"Objeto: {objeto}\\n"
            f"Valor: R$ {valor:,.2f}\\n"
            f"Link: {link}"
        )

        uid = f"{edital}-{tipo_evento}@radar-licitacoes-ti"

        linhas.extend([
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{agora}",
            f"DTSTART:{dtstart}",
            f"DTEND:{dtend}",
            f"SUMMARY:{_sanitizar_texto(summary)}",
            f"DESCRIPTION:{description}",
            f"LOCATION:{uf}",
            "STATUS:CONFIRMED",
            "BEGIN:VALARM",
            "TRIGGER:-PT30M",
            "ACTION:DISPLAY",
            f"DESCRIPTION:Licitação {label} em 30 min",
            "END:VALARM",
            "END:VEVENT",
        ])

    linhas.append("END:VCALENDAR")
    return "\r\n".join(linhas)
