from __future__ import annotations

from typing import Any, Dict, List


def validate_schema_for_product(fields_schema: Dict[str, Any]) -> List[str]:
    errors: List[str] = []

    headers = fields_schema.get("headers", [])
    fields = fields_schema.get("fields", [])
    visible_in_form = fields_schema.get("visibleInForm", [])
    visible_in_viewer = fields_schema.get("visibleInViewer", [])

    if not headers:
        errors.append("Missing headers.")
        return errors

    if "id" not in headers:
        errors.append("Missing mandatory header: id")

    seen = set()
    for h in headers:
        if h in seen:
            errors.append(f"Duplicate header: {h}")
        seen.add(h)

    if not fields:
        errors.append("Missing fields definitions.")

    field_names = {f.get("name") for f in fields if f.get("name")}
    for h in headers:
        if h not in field_names:
            errors.append(f"Header '{h}' has no matching field definition.")

    non_computed = [
        f for f in fields
        if not bool(f.get("computed", False))
    ]

    if non_computed and not visible_in_form:
        errors.append("At least one non-computed field should be visible in form.")

    if not visible_in_viewer:
        errors.append("visibleInViewer cannot be empty.")

    for f in fields:
        if f.get("type") == "enum":
            enum_values = f.get("enumValues", []) or []
            if not enum_values:
                errors.append(f"Enum field '{f.get('name')}' has no enumValues.")

    return errors