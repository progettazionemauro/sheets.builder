from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List


def _merge_unique(*lists: List[str]) -> List[str]:
    out: List[str] = []
    for seq in lists:
        for v in seq:
            if v and v not in out:
                out.append(v)
    return out


def merge_schema_with_visuals(
    sheet_schema: Dict[str, Any],
    html_visuals: Dict[str, Any],
) -> Dict[str, Any]:
    merged = deepcopy(sheet_schema)

    merged.setdefault("enums", {})
    merged.setdefault("enumStyles", {})

    html_enums = html_visuals.get("enumValuesFromHtml", {})
    html_styles = html_visuals.get("enumStyles", {})

    field_names = set(list(html_enums.keys()) + list(html_styles.keys()))

    for field_name in field_names:
        xlsx_values = list(merged.get("enums", {}).get(field_name, []))
        html_values = list(html_enums.get(field_name, []))
        style_values = list(html_styles.get(field_name, {}).keys())

        final_values = _merge_unique(xlsx_values, html_values, style_values)

        if final_values:
            merged["enums"][field_name] = final_values

            for f in merged.get("fields", []):
                if f.get("name") == field_name:
                    f["type"] = "enum"
                    f["enumValues"] = final_values

            if field_name in merged.get("constraints", {}):
                merged["constraints"][field_name]["type"] = "enum"

        if field_name in html_styles:
            merged["enumStyles"][field_name] = html_styles[field_name]

    return merged