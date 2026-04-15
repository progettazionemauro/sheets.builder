from __future__ import annotations

from typing import Any, Dict, List


def builder_state_to_legacy_schema(builder_state: Dict[str, Any]) -> Dict[str, Any]:
    fields: List[Dict[str, Any]] = list(builder_state.get("fields", []))
    constraints: Dict[str, Any] = dict(builder_state.get("constraints", {}))
    enums: Dict[str, Any] = dict(builder_state.get("enums", {}))
    enum_styles: Dict[str, Any] = dict(builder_state.get("enumStyles", {}))
    lists: Dict[str, Any] = dict(builder_state.get("lists", {}))

    # Riallinea enumStyles anche dentro i field, se serve
    normalized_fields: List[Dict[str, Any]] = []
    for f in fields:
        field = dict(f)
        name = field.get("name")
        if name and name in enum_styles and not field.get("enumStyles"):
            field["enumStyles"] = enum_styles[name]
        normalized_fields.append(field)

    return {
        "headers": list(lists.get("headers", [])),
        "requiredOnInsert": list(lists.get("requiredOnInsert", [])),
        "optionalOnInsert": list(lists.get("optionalOnInsert", [])),
        "computed": list(lists.get("computed", [])),
        "visibleInForm": list(lists.get("visibleInForm", [])),
        "visibleInViewer": list(lists.get("visibleInViewer", [])),
        "enums": enums,
        "constraints": constraints,
        "fields": normalized_fields,
        "enumStyles": enum_styles,
    }


def project_section_to_project_config(builder_state: Dict[str, Any]) -> Dict[str, Any]:
    project = dict(builder_state.get("project", {}))
    return {
        "projectName": project.get("projectName", ""),
        "projectSlug": project.get("projectSlug", ""),
        "backendName": project.get("backendName", ""),
        "entityName": project.get("entityName", ""),
        "entityLabelLower": project.get("entityLabelLower", ""),
        "sheetName": project.get("sheetName", ""),
        "outputDirectory": project.get("outputDirectory", ""),
        "buildMarker": project.get("buildMarker", ""),
        "adminPassword": project.get("adminPassword", ""),
    }