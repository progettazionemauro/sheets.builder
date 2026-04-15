from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List


def _merge_enum_values(
    xlsx_values: List[str],
    html_values: List[str],
    html_style_values: List[str],
) -> List[str]:
    out: List[str] = []

    for source in (xlsx_values, html_values, html_style_values):
        for v in source:
            if v and v not in out:
                out.append(v)

    return out


def merge_schema_with_visuals(
    sheet_schema: Dict[str, Any],
    html_visuals: Dict[str, Any],
) -> Dict[str, Any]:
    merged = deepcopy(sheet_schema)

    html_enum_styles = html_visuals.get("enumStyles", {})
    html_enum_values = html_visuals.get("enumValuesFromHtml", {})

    merged.setdefault("enumStyles", {})
    merged.setdefault("enums", {})

    for field_name, styles_map in html_enum_styles.items():
        xlsx_enum_values = list(merged.get("enums", {}).get(field_name, []))
        html_list_values = list(html_enum_values.get(field_name, []))
        html_style_values = list(styles_map.keys())

        final_enum_values = _merge_enum_values(
            xlsx_values=xlsx_enum_values,
            html_values=html_list_values,
            html_style_values=html_style_values,
        )

        if final_enum_values:
            merged["enums"][field_name] = final_enum_values

            for f in merged.get("fields", []):
                if f.get("name") == field_name:
                    f["type"] = "enum"
                    f["enumValues"] = final_enum_values

            if field_name in merged.get("constraints", {}):
                merged["constraints"][field_name]["type"] = "enum"

        merged["enumStyles"][field_name] = styles_map

    return merged