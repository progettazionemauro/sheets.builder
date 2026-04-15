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

    for name, f in field_by_name.items():
        is_computed = bool(f.get("computed", False))
        is_locked = bool(f.get("locked", False))
        is_visible_form = bool(f.get("visibleInForm", False))
        is_visible_viewer = bool(f.get("visibleInViewer", False))
        field_type = f.get("type")

        if is_visible_form:
            visible_form_fields.append(name)

        if is_visible_viewer:
            visible_viewer_fields.append(name)

        if name != "id" and not is_computed:
            non_computed_non_id.append(name)

        if is_computed:
            if is_visible_form:
                errors.append(f"Computed field '{name}' cannot have visibleInForm=true.")
            if bool(f.get("required", False)):
                errors.append(f"Computed field '{name}' cannot have required=true.")

        if field_type == "computed" and not is_computed:
            errors.append(f"Field '{name}' has type='computed' but computed=false.")

        if field_type != "computed" and is_computed and name != "id":
            errors.append(
                f"Field '{name}' has computed=true but type is '{field_type}'. "
                "Use type='computed' or make it non-computed."
            )

        if (
            name != "id"
            and not is_computed
            and not is_locked
            and not is_visible_form
        ):
            errors.append(
                f"Field '{name}' is a normal editable field but visibleInForm=false."
            )

    if not visible_viewer_fields:
        errors.append("At least one field must be visible in viewer.")

    if non_computed_non_id and not visible_form_fields:
        errors.append("At least one non-computed field must be visible in form.")

    expected_visible_in_form = [
        name for name, f in field_by_name.items()
        if bool(f.get("visibleInForm", False))
    ]
    expected_visible_in_viewer = [
        name for name, f in field_by_name.items()
        if bool(f.get("visibleInViewer", False))
    ]
    expected_computed = [
        name for name, f in field_by_name.items()
        if bool(f.get("computed", False))
    ]
    expected_required_on_insert = [
        name for name, f in field_by_name.items()
        if bool(f.get("required", False)) and not bool(f.get("computed", False))
    ]
    expected_optional_on_insert = [
        name for name, f in field_by_name.items()
        if not bool(f.get("required", False)) and not bool(f.get("computed", False))
    ]

    if visible_in_form != expected_visible_in_form:
        errors.append(
            f"'visibleInForm' mismatch. Expected {expected_visible_in_form}, got {visible_in_form}."
        )

    if visible_in_viewer != expected_visible_in_viewer:
        errors.append(
            f"'visibleInViewer' mismatch. Expected {expected_visible_in_viewer}, got {visible_in_viewer}."
        )

    if computed != expected_computed:
        errors.append(
            f"'computed' mismatch. Expected {expected_computed}, got {computed}."
        )

    if required_on_insert != expected_required_on_insert:
        errors.append(
            f"'requiredOnInsert' mismatch. Expected {expected_required_on_insert}, got {required_on_insert}."
        )

    if optional_on_insert != expected_optional_on_insert:
        errors.append(
            f"'optionalOnInsert' mismatch. Expected {expected_optional_on_insert}, got {optional_on_insert}."
        )

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