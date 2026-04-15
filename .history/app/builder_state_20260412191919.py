from __future__ import annotations

from typing import Any, Dict


def build_builder_state(
    parsed_schema: Dict[str, Any],
    project_config: Dict[str, Any],
) -> Dict[str, Any]:
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
        "fields": parsed_schema.get("fields", []),
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