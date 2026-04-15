from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup


def _extract_css_property(style: str, prop: str) -> Optional[str]:
    pattern = rf"{re.escape(prop)}\s*:\s*([^;]+)"
    m = re.search(pattern, style, flags=re.IGNORECASE)
    return m.group(1).strip() if m else None


def _cell_text(td) -> str:
    return td.get_text(separator=" ", strip=True)


def _find_main_table(soup: BeautifulSoup):
    return soup.find("table", class_="waffle") or soup.find("table")


def _extract_headers_from_first_row(table) -> List[str]:
    body_rows = table.find("tbody").find_all("tr")
    if not body_rows:
        return []

    first_row = body_rows[0]
    tds = first_row.find_all("td")
    headers = [_cell_text(td) for td in tds]
    return [h for h in headers if h]


def _build_column_letter_map(headers: List[str]) -> Dict[str, int]:
    return {name: idx for idx, name in enumerate(headers, start=1)}


def _extract_enum_styles_for_column(table, headers: List[str], enum_field_name: str) -> Dict[str, Dict[str, str]]:
    result: Dict[str, Dict[str, str]] = {}

    if enum_field_name not in headers:
        return result

    col_idx_zero_based = headers.index(enum_field_name)
    body_rows = table.find("tbody").find_all("tr")

    for tr in body_rows[1:]:
        tds = tr.find_all("td")
        if len(tds) <= col_idx_zero_based:
            continue

        td = tds[col_idx_zero_based]
        span = td.find("span")

        if not span:
            continue

        value = span.get_text(strip=True)
        style = span.get("style", "")

        if not value:
            continue

        bg = _extract_css_property(style, "background-color")
        fg = _extract_css_property(style, "color")

        if bg or fg:
            result[value] = {
                "bg": bg or "",
                "fg": fg or "",
            }

    return result


def _extract_side_list_values(table, headers: List[str], enum_field_name: str) -> List[str]:
    """
    Heuristica per leggere eventuali liste di supporto visibili nel foglio HTML.
    Nel tuo caso la lista enum è materializzata nella colonna O.
    Qui cerchiamo i valori unici nell'ultima colonna non-header se plausibili.
    """
    body_rows = table.find("tbody").find_all("tr")
    if not body_rows:
        return []

    seen: List[str] = []

    for tr in body_rows[1:]:
        tds = tr.find_all("td")
        if not tds:
            continue

        last_td = tds[-1]
        value = _cell_text(last_td)

        if value and value not in headers and value not in seen:
            seen.append(value)

    return seen


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

    headers = _extract_headers_from_first_row(table)
    enum_styles = _extract_enum_styles_for_column(table, headers, enum_field_name)
    enum_values_from_html = _extract_side_list_values(table, headers, enum_field_name)

    if debug:
        print("HTML headers:", headers)
        print("HTML enum_styles:", enum_styles)
        print("HTML enum_values_from_html:", enum_values_from_html)

    return {
        "headers": headers,
        "enumStyles": {
            enum_field_name: enum_styles
        },
        "enumValuesFromHtml": {
            enum_field_name: enum_values_from_html
        },
    }