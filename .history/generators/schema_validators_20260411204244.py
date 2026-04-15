from __future__ import annotations

from typing import Any, Dict, List


def validate_schema_for_product(fields_schema: Dict[str, Any]) -> List[str]:
    errors: List[str] = []

    headers = fields_schema.get("headers", [])
    fields = fields_schema.get("fields", [])
    visible_in_form = fields_schema.get("visibleInForm", [])
    visible_in_viewer = fields_schema.get("visibleInViewer", [])
    required_on_insert = fields_schema.get("requiredOnInsert", [])
    optional_on_insert = fields_schema.get("optionalOnInsert", [])
    computed = fields_schema.get("computed", [])
    constraints = fields_schema.get("constraints", {})

    if not isinstance(headers, list) or not headers:
        errors.append("Missing or invalid 'headers'.")
        return errors

    if not isinstance(fields, list) or not fields:
        errors.append("Missing or invalid 'fields'.")
        return errors

    if not isinstance(visible_in_form, list):
        errors.append("'visibleInForm' must be a list.")

    if not isinstance(visible_in_viewer, list):
        errors.append("'visibleInViewer' must be a list.")

    if not isinstance(required_on_insert, list):
        errors.append("'requiredOnInsert' must be a list.")

    if not isinstance(optional_on_insert, list):
        errors.append("'optionalOnInsert' must be a list.")

    if not isinstance(computed, list):
        errors.append("'computed' must be a list.")

    if not isinstance(constraints, dict):
        errors.append("'constraints' must be an object/dict.")

    if "id" not in headers:
        errors.append("Missing mandatory header: 'id'.")

    seen_headers = set()
    for h in headers:
        if not isinstance(h, str) or not h.strip():
            errors.append(f"Invalid header value: {h!r}")
            continue
        if h in seen_headers:
            errors.append(f"Duplicate header: '{h}'.")
        seen_headers.add(h)

    field_names = []
    field_by_name: Dict[str, Dict[str, Any]] = {}

        for i, f in enumerate(fields):
        if not isinstance(f, dict):
            errors.append(f"Field at index {i} is not an object.")
            continue

        name = f.get("name")
        if not isinstance(name, str) or not name.strip():
            errors.append(f"Field at index {i} has invalid or missing 'name'.")
            continue

        if name in field_by_name:
            errors.append(f"Duplicate field definition: '{name}'.")
        field_names.append(name)
        field_by_name[name] = f

        field_type = f.get("type")
        if field_type not in {"string", "int", "date", "enum", "computed"}:
            errors.append(
                f"Field '{name}' has invalid type '{field_type}'. "
                "Allowed: string, int, date, enum, computed."
            )

        for bool_key in ("required", "computed", "visibleInForm", "visibleInViewer", "locked"):
            if bool_key in f and not isinstance(f.get(bool_key), bool):
                errors.append(f"Field '{name}' has non-boolean '{bool_key}'.")

        enum_values = f.get("enumValues", [])
        if enum_values is None:
            enum_values = []

        if not isinstance(enum_values, list):
            errors.append(f"Field '{name}' has invalid 'enumValues' (must be a list).")
        else:
            if field_type == "enum" and not enum_values:
                errors.append(f"Enum field '{name}' has no enumValues.")
            if field_type != "enum" and enum_values:
                errors.append(
                    f"Field '{name}' is not enum but has non-empty enumValues."
                )

        enum_styles = f.get("enumStyles", {})
        if enum_styles is not None and not isinstance(enum_styles, dict):
            errors.append(f"Field '{name}' has invalid 'enumStyles' (must be a dict).")
        elif isinstance(enum_styles, dict):
            for enum_key, style_def in enum_styles.items():
                if not isinstance(enum_key, str):
                    errors.append(f"Field '{name}' has non-string enumStyles key.")
                    continue
                if not isinstance(style_def, dict):
                    errors.append(f"Field '{name}' enumStyles['{enum_key}'] must be a dict.")
                    continue
                bg = style_def.get("bg")
                fg = style_def.get("fg")
                if bg is not None and not isinstance(bg, str):
                    errors.append(f"Field '{name}' enumStyles['{enum_key}'].bg must be string.")
                if fg is not None and not isinstance(fg, str):
                    errors.append(f"Field '{name}' enumStyles['{enum_key}'].fg must be string.")

        formula_source = f.get("formulaSource")
        formula_anchor_row = f.get("formulaAnchorRow")
        formula_mode = f.get("formulaMode")

        if formula_source is not None and not isinstance(formula_source, str):
            errors.append(f"Field '{name}' has invalid 'formulaSource' (must be string or null).")

        if formula_anchor_row is not None and not isinstance(formula_anchor_row, int):
            errors.append(f"Field '{name}' has invalid 'formulaAnchorRow' (must be int or null).")

        if formula_mode is not None and not isinstance(formula_mode, str):
            errors.append(f"Field '{name}' has invalid 'formulaMode' (must be string or null).")

        if field_type == "computed" and formula_source is not None:
            if not formula_source.startswith("="):
                errors.append(f"Field '{name}' formulaSource must start with '='.")

    for h in headers:
        if h not in field_by_name:
            errors.append(f"Header '{h}' has no matching field definition.")

    for fname in field_names:
        if fname not in headers:
            errors.append(f"Field '{fname}' is defined but missing from headers.")

    if "id" in field_by_name:
        id_field = field_by_name["id"]

        if id_field.get("type") != "int":
            errors.append("Field 'id' must have type 'int'.")

        if id_field.get("computed") is not True:
            errors.append("Field 'id' must have computed=true.")

        if id_field.get("visibleInForm") is not False:
            errors.append("Field 'id' must have visibleInForm=false.")

        if id_field.get("locked") is not True:
            errors.append("Field 'id' must have locked=true.")

    non_computed_non_id = []
    visible_form_fields = []
    visible_viewer_fields = []

    

    for name in headers:
        if name not in constraints:
            errors.append(f"Missing constraint definition for field '{name}'.")

    for cname, cdef in constraints.items():
        if cname not in field_by_name:
            errors.append(f"Constraint defined for unknown field '{cname}'.")
            continue

        if not isinstance(cdef, dict):
            errors.append(f"Constraint for field '{cname}' must be an object/dict.")
            continue

        field_type = field_by_name[cname].get("type")
        ctype = cdef.get("type")

        if ctype != field_type:
            errors.append(
                f"Constraint type mismatch for field '{cname}': "
                f"field type is '{field_type}', constraint type is '{ctype}'."
            )

        if field_type == "int":
            if "min" in cdef and not isinstance(cdef["min"], int):
                errors.append(f"Constraint 'min' for int field '{cname}' must be int.")
            if "max" in cdef and not isinstance(cdef["max"], int):
                errors.append(f"Constraint 'max' for int field '{cname}' must be int.")

        if field_type == "string":
            if "maxLen" in cdef and not isinstance(cdef["maxLen"], int):
                errors.append(f"Constraint 'maxLen' for string field '{cname}' must be int.")

        if field_type == "date":
            if "format" in cdef and not isinstance(cdef["format"], str):
                errors.append(f"Constraint 'format' for date field '{cname}' must be string.")

    return errors