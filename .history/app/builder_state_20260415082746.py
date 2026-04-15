from __future__ import annotations

from typing import Any


def _default_project_from_schema(parsed_schema: dict[str, Any]) -> dict[str, Any]:
    sheet_name = "Sheet1"
    headers = parsed_schema.get("headers", [])

    if parsed_schema.get("sourceMeta", {}).get("sheetName"):
        sheet_name = parsed_schema["sourceMeta"]["sheetName"]

    project_name = "Generated App"
    project_slug = "generated-app"

    return {
        "projectName": project_name,
        "projectSlug": project_slug,
        "backendName": f"{project_slug}-backend",
        "entityName": "Item",
        "entityLabelLower": "item",
        "sheetName": sheet_name,
        "buildMarker": "GENERATED_APP_BACKEND_V1",
        "adminPassword": "CHANGE_ME_WRITE_KEY_2026",
    }


def build_builder_state(parsed_schema: dict[str, Any]) -> dict[str, Any]:
    fields = []
    constraints = dict(parsed_schema.get("constraints", {}) or {})
    enums = dict(parsed_schema.get("enums", {}) or {})
    enum_styles = dict(parsed_schema.get("enumStyles", {}) or {})

    for raw in parsed_schema.get("fields", []):
        name = raw.get("name", "")
        field = {
            "name": name,
            "label": name,
            "type": raw.get("type", "string"),
            "required": bool(raw.get("required", False)),
            "computed": bool(raw.get("computed", False)),
            "visibleInForm": bool(raw.get("visibleInForm", False)),
            "visibleInViewer": bool(raw.get("visibleInViewer", False)),
            "locked": bool(raw.get("locked", False)),
            "enumValues": list(raw.get("enumValues", []) or []),
        }

        if name in enum_styles:
            field["enumStyles"] = enum_styles[name]

        if raw.get("formulaSource"):
            field["formulaSource"] = raw.get("formulaSource")
        if raw.get("formulaAnchorRow") is not None:
            field["formulaAnchorRow"] = raw.get("formulaAnchorRow")
        if raw.get("formulaMode"):
            field["formulaMode"] = raw.get("formulaMode")

        fields.append(field)

    return {
        "project": _default_project_from_schema(parsed_schema),
        "fields": fields,
        "constraints": constraints,
        "enums": enums,
        "enumStyles": enum_styles,
        "lists": {
            "headers": list(parsed_schema.get("headers", []) or []),
            "requiredOnInsert": list(parsed_schema.get("requiredOnInsert", []) or []),
            "optionalOnInsert": list(parsed_schema.get("optionalOnInsert", []) or []),
            "computed": list(parsed_schema.get("computed", []) or []),
            "visibleInForm": list(parsed_schema.get("visibleInForm", []) or []),
            "visibleInViewer": list(parsed_schema.get("visibleInViewer", []) or []),
        },
        "options": {},
    }