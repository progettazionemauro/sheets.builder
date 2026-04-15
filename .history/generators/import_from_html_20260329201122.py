from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup


def _extract_css_property(style: str, prop: str) -> Optional[str]:
    parts = [p.strip() for p in style.split(";") if p.strip()]
    for part in parts:
        if ":" not in part:
            continue
        key, value = part.split(":", 1)
        if key.strip().lower() == prop.strip().lower():
            return value.strip()
    return None


def _cell_text(td) -> str:
    return td.get_text(separator=" ", strip=True)


def _find_main_table(soup: BeautifulSoup):
    return soup.find("table", class_="waffle") or soup.find("table")


def _extract_headers_and_rows(table) -> tuple[list[str], list[list[str]], list]:
    body = table.find("tbody")
    if body is None:
        return [], [], []

    trs = body.find_all("tr")
    if not trs:
        return [], [], []

    first_row_tds = trs[0].find_all("td")
    headers = [_cell_text(td) for td in first_row_tds]

    data_rows: List[List[str]] = []
    raw_rows = []

    for tr in trs[1:]:
        tds = tr.find_all("td")
        values = [_cell_text(td) for td in tds]
        data_rows.append(values)
        raw_rows.append(tds)

    return headers, data_rows, raw_rows


def _extract_enum_styles_for_column(
    raw_rows: List,
    headers: List[str],
    enum_field_name: str,
) -> Dict[str, Dict[str, str]]:
    result: Dict[str, Dict[str, str]] = {}

    if enum_field_name not in headers:
        return result

    idx = headers.index(enum_field_name)

    for row_tds in raw_rows:
        if len(row_tds) <= idx:
            continue

        td = row_tds[idx]
        span = td.find("span")
        if not span:
            continue

        

        style = span.get("style", "")
        bg = _extract_css_property(style, "background-color")
        fg = _extract_css_property(style, "color")

        if bg or fg:
            result[value] = {
                "bg": bg or "",
                "fg": fg or "",
            }

    return result


def _extract_side_column_enum_candidates(
    headers: List[str],
    data_rows: List[List[str]],
) -> List[str]:
    """
    Heuristica semplice:
    cerca una colonna oltre gli header principali con pochi valori testuali unici.
    """
    if not data_rows:
        return []

    max_cols = max(len(r) for r in data_rows)
    header_len = len(headers)

    for col_idx in range(header_len, max_cols):
        seen: List[str] = []

        for row in data_rows:
            if len(row) <= col_idx:
                continue

            v = row[col_idx].strip()
            if not v:
                continue

            if v not in seen:
                seen.append(v)

        if 2 <= len(seen) <= 20:
            return seen

    return []


def import_visuals_from_html(
    html_path: str | Path,
    enum_field_name: str = "rating",
    debug: bool = False,
) -> Dict[str, Any]:
    html_path = Path(html_path)
    html_text = html_path.read_text(encoding="utf-8", errors="ignore")

    soup = BeautifulSoup(html_text, "html.parser")
    table = _find_main_table(soup)
    if table is None:
        raise ValueError("No HTML table found")

    headers, data_rows, raw_rows = _extract_headers_and_rows(table)
    if not headers:
        raise ValueError("No headers found in HTML table")

    enum_styles = _extract_enum_styles_for_column(raw_rows, headers, enum_field_name)
    enum_values_from_html = _extract_side_column_enum_candidates(headers, data_rows)

    if debug:
        print("HTML headers:", headers)
        print("HTML enum styles:", enum_styles)
        print("HTML enum values from side column:", enum_values_from_html)

    return {
        "headers": headers,
        "enumStyles": {
            enum_field_name: enum_styles
        } if enum_styles else {},
        "enumValuesFromHtml": {
            enum_field_name: enum_values_from_html
        } if enum_values_from_html else {},
    }