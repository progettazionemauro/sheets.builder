from __future__ import annotations

import io
import re
import zipfile
from urllib.parse import urlsplit, parse_qs

import requests


MAX_XLSX_BYTES = 25 * 1024 * 1024


def parse_google_sheet_url(url: str) -> tuple[str, str | None]:
    parts = urlsplit(url.strip())

    if parts.scheme != "https" or parts.hostname != "docs.google.com":
        raise ValueError("URL Google Sheets non valido")

    match = re.fullmatch(
        r"/spreadsheets/d/([A-Za-z0-9_-]{20,})(?:/.*)?",
        parts.path,
    )

    if not match:
        raise ValueError("Impossibile identificare lo spreadsheet")

    params = parse_qs(parts.query)
    fragments = parse_qs(parts.fragment)
    gid = (params.get("gid") or fragments.get("gid") or [None])[0]

    if gid is not None and not gid.isdigit():
        raise ValueError("Identificativo del foglio non valido")

    return match.group(1), gid



def list_google_sheet_tabs(url: str) -> list[dict]:
    import json

    spreadsheet_id, _ = parse_google_sheet_url(url)
    page_url = (
        f"https://docs.google.com/spreadsheets/d/"
        f"{spreadsheet_id}/edit"
    )

    response = requests.get(page_url, timeout=(5, 30))
    response.raise_for_status()

    pattern = r'\[21350203,("(?:\\.|[^"\\])*")\]'
    matches = list(re.finditer(pattern, response.text))

    if not matches:
        raise ValueError(
            "Impossibile leggere l'elenco dei fogli Google"
        )

    tabs = []

    for match in matches:
        payload = json.loads(json.loads(match.group(1)))

        index = int(payload[0])
        gid = str(payload[2])
        name = payload[3][0]["1"][0][2]

        if not gid.isdigit() or not isinstance(name, str):
            raise ValueError("Metadati dei fogli non validi")

        tabs.append({
            "index": index,
            "sheetId": gid,
            "sheetName": name,
        })

    tabs.sort(key=lambda x: x["index"])

    if (
        len({t["sheetId"] for t in tabs}) != len(tabs)
        or len({t["sheetName"] for t in tabs}) != len(tabs)
        or [t["index"] for t in tabs] != list(range(len(tabs)))
    ):
        raise ValueError("Elenco dei fogli ambiguo o incompleto")

    return tabs


def download_google_sheet_xlsx(
    url: str,
) -> tuple[bytes, str, str | None]:
    spreadsheet_id, gid = parse_google_sheet_url(url)

    export_url = (
        f"https://docs.google.com/spreadsheets/d/"
        f"{spreadsheet_id}/export?format=xlsx"
    )

    response = requests.get(export_url, timeout=(5, 60))
    response.raise_for_status()

    content = response.content

    if len(content) > MAX_XLSX_BYTES:
        raise ValueError("Spreadsheet troppo grande")

    if not zipfile.is_zipfile(io.BytesIO(content)):
        raise ValueError(
            "Google non ha restituito un file XLSX valido"
        )

    return content, spreadsheet_id, gid
