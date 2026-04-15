from __future__ import annotations

from typing import Any, Dict, List


def _derive_label(name: str) -> str:
    parts = str(name or "").strip().replace("-", "_").split("_")
    parts = [p for p in parts if p]
    if not parts:
        return ""
    return " ".join(part[:1].upper() + part[1:] for part in parts)


def _normalize_fields_with_labels(fields: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []

    for raw in fields:
        field = dict(raw)
        if not field.get("label"):
            field["label"] = _derive_label(field.get("name", ""))
        out.append(field)

    return out


def build_builder_state(
    parsed_schema: Dict[str, Any],
    project_config: Dict[str, Any],
) -> Dict[str, Any]:
    normalized_fields = _normalize_fields_with_labels(parsed_schema.get("fields", []))

    return {
        "project": {
            "projectName": project_config.get("projectName", ""),
            "projectSlug": project_config.get("projectSlug", ""),
            "backendName": project_config.get("backendName", ""),
            "entityName": project_config.get("entityName", ""),
            "entityLabelLower": project_config.get("entityLabelLower", ""),
            "sheetName": project_config.get("sheetName", ""),
            "outputDirectory": project_config.get("outputDirectory", ""),
            "buildMarker": project_config.get("buildMarker", ""),
            "adminPassword": project_config.get("adminPassword", ""),
        },
        "fields": normalized_fields,
        "constraints": parsed_schema.get("constraints", {}),
        "enums": parsed_schema.get("enums", {}),
        "enumStyles": parsed_schema.get("enumStyles", {}),
        "lists": {
            "headers": parsed_schema.get("headers", []),
            "requiredOnInsert": parsed_schema.get("requiredOnInsert", []),
            "optionalOnInsert": parsed_schema.get("optionalOnInsert", []),
            "computed": parsed_schema.get("computed", []),
            "visibleInForm": parsed_schema.get("visibleInForm", []),
            "visibleInViewer": parsed_schema.get("visibleInViewer", []),
        },
        "options": {
            "generateViewer": True,
            "generateBackend": True,
            "publishDir": "docs",
        },
    }