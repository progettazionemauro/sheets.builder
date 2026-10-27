from __future__ import annotations

import json
import html
import re
from dataclasses import dataclass
from typing import Any, Dict, List


# ============================================================
# DATA MODEL
# ============================================================

@dataclass
class FieldDef:
    name: str
    label: str
    original_header: str
    type: str
    required: bool
    computed: bool
    visible_in_form: bool
    visible_in_viewer: bool
    enum_values: List[str]
    locked: bool = False
    enum_styles: Dict[str, Dict[str, str]] | None = None
    formula_source: str | None = None
    formula_anchor_row: int | None = None
    formula_mode: str | None = None
    sort_type: str = "auto"
    display_type: str = "text"


# ============================================================
# HELPERS
# ============================================================

def js_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def js_pretty(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


def slugify_for_dom(name: str) -> str:
    s = name.strip().lower()
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE)
    s = re.sub(r"[\s\-]+", "_", s)
    if not s:
        s = "field"
    if s[0].isdigit():
        s = f"f_{s}"
    return s


def escape_html(s: str) -> str:
    return html.escape(s, quote=True)


def field_map_from_schema(fields_schema: Dict[str, Any]) -> List[FieldDef]:
    out: List[FieldDef] = []
    for raw in fields_schema.get("fields", []):
        out.append(
            FieldDef(
                name=raw["name"],
                label=raw.get("label", raw["name"]),
                type=raw.get("type", "string"),
                original_header=raw.get("originalHeader", raw["name"]),
                required=bool(raw.get("required", False)),
                computed=bool(raw.get("computed", False)),
                visible_in_form=bool(raw.get("visibleInForm", False)),
                visible_in_viewer=bool(raw.get("visibleInViewer", False)),
                enum_values=list(raw.get("enumValues", []) or []),
                locked=bool(raw.get("locked", False)),
                enum_styles=dict(raw.get("enumStyles", {}) or {}),
                formula_source=raw.get("formulaSource"),
                formula_anchor_row=raw.get("formulaAnchorRow"),
                formula_mode=raw.get("formulaMode"),
                sort_type=raw.get("sortType", "auto")
                    if raw.get("sortType") in
                    ("auto", "string", "number", "date_it", "datetime_it")
                    else "auto",
                display_type=raw.get("displayType", "text")
                    if raw.get("displayType") in ("text", "link", "image")
                    else "text",
            )
        )
    return out


def non_computed_fields(fields: List[FieldDef]) -> List[FieldDef]:
    return [f for f in fields if not f.computed]


def form_fields(fields: List[FieldDef]) -> List[FieldDef]:
    return [f for f in fields if f.visible_in_form and not f.computed]


def viewer_fields(fields: List[FieldDef]) -> List[FieldDef]:
    return [f for f in fields if f.visible_in_viewer]


def required_on_insert(fields: List[FieldDef]) -> List[str]:
    return [f.name for f in fields if f.required and not f.computed]


def optional_on_insert(fields: List[FieldDef]) -> List[str]:
    return [f.name for f in fields if not f.required and not f.computed]


def computed_fields(fields: List[FieldDef]) -> List[str]:
    return [f.name for f in fields if f.computed]


def enum_map(fields: List[FieldDef]) -> Dict[str, List[str]]:
    return {f.name: f.enum_values for f in fields if f.enum_values}


def enum_styles_map(fields: List[FieldDef]) -> Dict[str, Dict[str, Dict[str, str]]]:
    out: Dict[str, Dict[str, Dict[str, str]]] = {}
    for f in fields:
        if f.enum_styles:
            out[f.name] = f.enum_styles
    return out


def constraints_from_schema(fields_schema: Dict[str, Any]) -> Dict[str, Any]:
    return dict(fields_schema.get("constraints", {}))


def _normalize_formula_for_gs_template(formula: str, target_row_var: str = "rowNumber") -> str:
    """
    Rimpiazza i riferimenti di riga non assoluti con ${rowNumber} o ${row}.
    Esempi:
      C2     -> C${rowNumber}
      $C2    -> $C${rowNumber}
      C$2    -> C$2
      $C$2   -> $C$2
      D2:D99 -> D${rowNumber}:D${rowNumber}   (comportamento base)
    """
    if not formula:
        return ""

    pattern = re.compile(r'(?<![A-Z0-9_])(\$?[A-Z]{1,3})(\$?)(\d+)')

    def repl(match: re.Match[str]) -> str:
        col = match.group(1)
        dollar_row = match.group(2)
        row_num = match.group(3)

        if dollar_row == "$":
            return f"{col}${row_num}"

        return f"{col}${{{target_row_var}}}"

    return pattern.sub(repl, formula)


def _js_template_literal_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("`", "\\`")


# ============================================================
# BACKEND GENERATOR (codice.gs)
# ============================================================

def _generate_backend_insert_extract(fields: List[FieldDef]) -> str:
    lines = []
    for f in non_computed_fields(fields):
        var_name = slugify_for_dom(f.name)
        if f.type == "int":
            lines.append(
                f'  const {var_name} = clampInt_(p[{js_string(f.name)}], -999999999, 999999999, 0);'
            )
        else:
            lines.append(
                f'  const {var_name} = norm_(p[{js_string(f.name)}]);'
            )
    return "\n".join(lines)


def _generate_backend_insert_missing(fields: List[FieldDef]) -> str:
    lines = ['  const missing = [];']
    for f in non_computed_fields(fields):
        if not f.required:
            continue

        var_name = slugify_for_dom(f.name)
        if f.type == "int":
            lines.append(
                f'  if (!{var_name} && {var_name} !== 0) missing.push({js_string(f.name)});'
            )
        else:
            lines.append(
                f'  if (!{var_name}) missing.push({js_string(f.name)});'
            )

    lines.append('  if (missing.length) return { ok: false, error: "Missing required fields", missing };')
    return "\n".join(lines)


def _generate_backend_insert_validations(fields: List[FieldDef], constraints: Dict[str, Any]) -> str:
    lines: List[str] = []

    for f in non_computed_fields(fields):
        c = constraints.get(f.name, {})
        var_name = slugify_for_dom(f.name)

        if f.type == "string":
            max_len = c.get("maxLen")
            if max_len:
                lines.append(
                    f'  if ({var_name} && {var_name}.length > {int(max_len)}) return {{ ok: false, error: {js_string(f"{f.name} too long (max {max_len})")} }};'
                )

        if f.type == "int":
            min_v = c.get("min")
            max_v = c.get("max")
            if min_v is not None:
                lines.append(
                    f'  if ({var_name} && {var_name} < {int(min_v)}) return {{ ok: false, error: {js_string(f"{f.name} below min {min_v}")} }};'
                )
            if max_v is not None:
                lines.append(
                    f'  if ({var_name} && {var_name} > {int(max_v)}) return {{ ok: false, error: {js_string(f"{f.name} above max {max_v}")} }};'
                )

        if f.type == "enum" and f.enum_values:
            allowed_name = f"ENUM_{slugify_for_dom(f.name).upper()}"
            lines.append(
                f'  if ({var_name} && {allowed_name}.indexOf({var_name}) === -1) return {{ ok: false, error: {js_string(f"{f.name} not allowed")}, allowed: {allowed_name} }};'
            )

    return "\n".join(lines)


def _generate_backend_enum_constants(fields: List[FieldDef]) -> str:
    lines = []
    for f in fields:
        if f.type == "enum" and f.enum_values:
            const_name = f"ENUM_{slugify_for_dom(f.name).upper()}"
            lines.append(f"const {const_name} = {js_pretty(f.enum_values)};")
    return "\n".join(lines)


def _generate_backend_row_write(fields: List[FieldDef]) -> str:
    row_values = []
    for f in fields:
        if f.computed and f.name == "id":
            row_values.append("id")
        elif f.computed:
            row_values.append('""')
        else:
            row_values.append(slugify_for_dom(f.name))
    return ",\n    ".join(row_values)


def _generate_backend_computed_formula_write(fields: List[FieldDef], mode: str) -> str:
    target_var = "rowNumber" if mode == "insert" else "row"
    lines: List[str] = []

    for idx, f in enumerate(fields, start=1):
        if not f.computed or f.name == "id":
            continue

        if f.formula_source and f.formula_mode == "incremental_copy":
            normalized = _normalize_formula_for_gs_template(
                f.formula_source,
                target_row_var=target_var,
            )
            js_formula = _js_template_literal_escape(normalized)
            lines.append(
                f'  sh.getRange({target_var}, {idx}).setFormula(`{js_formula}`);'
            )

    return "\n".join(lines)


def generate_gas_backend(project_config: Dict[str, Any], fields_schema: Dict[str, Any]) -> str:
    fields = field_map_from_schema(fields_schema)
    api_headers = [f.name for f in fields]
    sheet_headers = [f.original_header or f.name for f in fields]
    constraints = constraints_from_schema(fields_schema)

    backend_name = project_config["backendName"]
    sheet_name = project_config["sheetName"]
    api_key = project_config["adminPassword"]
    build_marker = project_config["buildMarker"]
    entity_name = project_config["entityName"]

    required = required_on_insert(fields)
    optional = optional_on_insert(fields)
    computed = computed_fields(fields)
    enums = enum_map(fields)

    enum_consts = _generate_backend_enum_constants(fields)
    insert_extract = _generate_backend_insert_extract(fields)
    insert_missing = _generate_backend_insert_missing(fields)
    insert_validations = _generate_backend_insert_validations(fields, constraints)
    row_write = _generate_backend_row_write(fields)
    insert_formula_write = _generate_backend_computed_formula_write(fields, mode="insert")
    update_formula_write = _generate_backend_computed_formula_write(fields, mode="update")

    insert_formula_block = f"\n{insert_formula_write}\n" if insert_formula_write else "\n"
    update_formula_block = f"\n{update_formula_write}\n" if update_formula_write else "\n"

    return f'''/***************
 * AUTO-GENERATED BY SHEETS BUILDER
 * Backend: {backend_name}
 *
 * Modes:
 * - meta
 * - schema
 * - view        (public read)
 * - insert      (write, requires apiKey)
 * - getById     (write-key protected)
 * - update      (write-key protected)
 * - delete      (write-key protected)
 ***************/

// ===== CONFIG =====
const BACKEND_NAME = {js_string(backend_name)};
const SHEET_NAME = {js_string(sheet_name)};
const SPREADSHEET_ID = "";
const API_KEY = {js_string(api_key)};
const BUILD_MARKER = {js_string(build_marker)};
const BUILD_TIME = new Date().toISOString();

const SHEET_HEADERS = {js_pretty(sheet_headers)};
const HEADERS = {js_pretty(api_headers)};
const REQUIRED_ON_INSERT = {js_pretty(required)};
const OPTIONAL_ON_INSERT = {js_pretty(optional)};
const COMPUTED = {js_pretty(computed)};
const ENUMS = {js_pretty(enums)};
const CONSTRAINTS = {js_pretty(constraints)};

{enum_consts}

/***************
 * ENTRY POINT
 ***************/
function doGet(e) {{
  const p = (e && e.parameter) ? e.parameter : {{}};
  const cb = String(p.cb || "").trim();

  if (!cb) return ContentService.createTextOutput("Missing cb (JSONP)");

  try {{
    const mode = String(p.mode || "meta").trim();
    const debug = String(p.debug || "") === "1";

    if (mode === "meta")   return jsonp_(cb, meta_());
    if (mode === "schema") return jsonp_(cb, schema_());
    if (mode === "view") {{
      const limit = clampInt_(p.limit, 1, 500, 50);
      return jsonp_(cb, view_(limit));
    }}

    const apiKey = String(p.apiKey || "");
    if (apiKey !== API_KEY) {{
      const out = {{ ok: false, error: "Invalid apiKey" }};
      if (debug) out.debug = {{ receivedApiKey: apiKey ? "(provided)" : "(missing)" }};
      return jsonp_(cb, out);
    }}

    if (mode === "insert") return jsonp_(cb, insert_(p, debug));

    if (mode === "getById") {{
      const id = clampInt_(p.id, 1, 999999999, 0);
      if (!id) return jsonp_(cb, {{ ok: false, error: "Missing/invalid id" }});
      return jsonp_(cb, getById_(id));
    }}

    if (mode === "update") {{
      const id = clampInt_(p.id, 1, 999999999, 0);
      if (!id) return jsonp_(cb, {{ ok: false, error: "Missing/invalid id" }});
      return jsonp_(cb, update_(id, p, debug));
    }}

    if (mode === "delete") {{
      const id = clampInt_(p.id, 1, 999999999, 0);
      if (!id) return jsonp_(cb, {{ ok: false, error: "Missing/invalid id" }});
      return jsonp_(cb, del_(id));
    }}

    return jsonp_(cb, {{ ok: false, error: "Unknown mode", mode }});

  }} catch (err) {{
    return jsonp_(cb, {{
      ok: false,
      error: String(err && err.message ? err.message : err)
    }});
  }}
}}

/***************
 * META + SCHEMA
 ***************/
function meta_() {{
  return {{
    ok: true,
    backend: BACKEND_NAME,
    sheet: SHEET_NAME,
    marker: BUILD_MARKER,
    build: BUILD_TIME,
    publicModes: ["meta", "schema", "view"],
    protectedModes: ["insert", "getById", "update", "delete"]
  }};
}}

function schema_() {{
  return {{
    ok: true,
    entity: {js_string(entity_name)},
    headers: HEADERS,
    requiredOnInsert: REQUIRED_ON_INSERT,
    optionalOnInsert: OPTIONAL_ON_INSERT,
    computed: COMPUTED,
    enums: ENUMS,
    constraints: CONSTRAINTS
  }};
}}

/***************
 * VIEW
 ***************/
function view_(limit) {{
  const sh = getSheet_();
  ensureHeaders_(sh);

  const lastRow = sh.getLastRow();
  const lastCol = sh.getLastColumn();

  if (lastRow < 2 || lastCol < 1) {{
    return {{ ok: true, headers: HEADERS, rows: [] }};
  }}

  const numCols = Math.min(lastCol, HEADERS.length);
  const dataRows = lastRow - 1;
  const take = Math.min(limit, dataRows);
  const start = lastRow - take + 1;

  const rows = sh.getRange(start, 1, take, numCols).getValues();
  return {{ ok: true, headers: HEADERS.slice(0, numCols), rows }};
}}

/***************
 * INSERT
 ***************/
function insert_(p, debug) {{
  const sh = getSheet_();
  ensureHeaders_(sh);

{insert_extract}

{insert_missing}

{insert_validations}

  const id = computeNextId_(sh);
  const rowNumber = sh.getLastRow() + 1;

  sh.getRange(rowNumber, 1, 1, HEADERS.length).setValues([[{row_write}]]);
{insert_formula_block}  const out = {{ ok: true, id, insertedRow: rowNumber }};
  if (debug) out.debug = {{ keys: Object.keys(p).sort() }};
  return out;
}}

/***************
 * GET BY ID
 ***************/
function getById_(id) {{
  const sh = getSheet_();
  ensureHeaders_(sh);

  const row = findRowById_(sh, id);
  if (!row) return {{ ok: false, error: "ID not found", id }};

  const values = sh.getRange(row, 1, 1, HEADERS.length).getValues()[0];
  const rec = {{}};
  HEADERS.forEach((h, i) => rec[h] = values[i]);

  return {{ ok: true, id, record: rec, row }};
}}

/***************
 * UPDATE
 ***************/
function update_(id, p, debug) {{
  const sh = getSheet_();
  ensureHeaders_(sh);

  const row = findRowById_(sh, id);
  if (!row) return {{ ok: false, error: "ID not found", id }};

{insert_extract}

{insert_missing}

{insert_validations}

  sh.getRange(row, 1, 1, HEADERS.length).setValues([[{row_write}]]);
{update_formula_block}  const out = {{ ok: true, id, updatedRow: row }};
  if (debug) out.debug = {{ keys: Object.keys(p).sort() }};
  return out;
}}

/***************
 * DELETE
 ***************/
function del_(id) {{
  const sh = getSheet_();
  ensureHeaders_(sh);

  const row = findRowById_(sh, id);
  if (!row) return {{ ok: false, error: "ID not found", id }};

  sh.deleteRow(row);
  return {{ ok: true, id, deletedRow: row }};
}}

/***************
 * INTERNALS
 ***************/
function getSheet_() {{
  const ss = SPREADSHEET_ID
    ? SpreadsheetApp.openById(SPREADSHEET_ID)
    : SpreadsheetApp.getActiveSpreadsheet();

  const sh = ss.getSheetByName(SHEET_NAME);
  if (!sh) throw new Error("Sheet not found: " + SHEET_NAME);
  return sh;
}}

function ensureHeaders_(sh) {{
  const lastCol = Math.max(sh.getLastColumn(), SHEET_HEADERS.length);
  const row1 = sh.getRange(1, 1, 1, lastCol).getValues()[0].slice(0, SHEET_HEADERS.length);
  const row1Norm = row1.map(x => String(x || "").trim());

  const ok = SHEET_HEADERS.every((h, i) => row1Norm[i] === h);

  if (!ok) {{
    const allEmpty = row1Norm.every(x => !x);
    if (allEmpty && sh.getLastRow() === 0) {{
      sh.getRange(1, 1, 1, SHEET_HEADERS.length).setValues([SHEET_HEADERS]);
      return;
    }}
    throw new Error("Header mismatch in sheet. Expected: " + SHEET_HEADERS.join(", "));
  }}
}}

function findRowById_(sh, id) {{
  const lastRow = sh.getLastRow();
  if (lastRow < 2) return 0;

  const tf = sh.getRange(2, 1, lastRow - 1, 1)
    .createTextFinder(String(id))
    .matchEntireCell(true);

  const cell = tf.findNext();
  return cell ? cell.getRow() : 0;
}}

function computeNextId_(sh) {{
  const lastRow = sh.getLastRow();
  if (lastRow < 2) return 1;

  const ids = sh.getRange(2, 1, lastRow - 1, 1).getValues().flat()
    .map(Number)
    .filter(x => !isNaN(x));

  const maxId = ids.length ? Math.max.apply(null, ids) : 0;
  return maxId + 1;
}}

function clampInt_(v, min, max, defVal) {{
  const n = parseInt(String(v || ""), 10);
  if (isNaN(n)) return defVal;
  return Math.max(min, Math.min(max, n));
}}

function norm_(v) {{
  return String(v ?? "").trim();
}}

function jsonp_(cb, obj) {{
  const out = cb + "(" + JSON.stringify(obj) + ");";
  return ContentService
    .createTextOutput(out)
    .setMimeType(ContentService.MimeType.JAVASCRIPT);
}}
'''


# ============================================================
# INDEX.HTML GENERATOR
# ============================================================

def _html_input_for_field(field: FieldDef, constraints: Dict[str, Any]) -> str:
    dom_id = slugify_for_dom(field.name)
    required_label = "required" if field.required else "optional"
    label = escape_html(field.label or field.name)

    if field.type == "enum":
        options = ['<option value="" selected>—</option>']
        options.extend(f'<option>{escape_html(v)}</option>' for v in field.enum_values)
        return f'''
    <label for="{dom_id}">{label} <span class="muted">({required_label})</span></label>
    <select id="{dom_id}">
      {"".join(options)}
    </select>'''.rstrip()

    if field.type == "int":
        c = constraints.get(field.name, {})
        min_v = f' min="{c["min"]}"' if "min" in c else ""
        max_v = f' max="{c["max"]}"' if "max" in c else ""
        return f'''
    <label for="{dom_id}">{label} <span class="muted">({required_label})</span></label>
    <input id="{dom_id}" type="number"{min_v}{max_v} placeholder="{label}" />'''.rstrip()

    preview = ""
    if field.type in ("string", "text"):
        preview = (
            f'<div class="dj-image-preview" data-preview-for="{dom_id}" hidden>'
            f'<a target="_blank" rel="noopener noreferrer">'
            f'<img alt="Anteprima: {label}" loading="lazy"></a>'
            f'</div>'
        )

    placeholder = label
    if field.type == "date":
        placeholder = constraints.get(field.name, {}).get("format", "dd/mm/yyyy")

    return f'''
    <label for="{dom_id}">{label} <span class="muted">({required_label})</span></label>
    <input id="{dom_id}" placeholder="{escape_html(placeholder)}" />
    {preview}'''.rstrip()


def _generate_form_html(fields: List[FieldDef], constraints: Dict[str, Any]) -> str:
    parts = []
    for f in form_fields(fields):
        parts.append(_html_input_for_field(f, constraints))
    return "\n\n".join(parts)


def _generate_payload_js(fields: List[FieldDef]) -> str:
    lines = []
    for f in form_fields(fields):
        dom_id = slugify_for_dom(f.name)
        if f.type == "enum":
            lines.append(f'        {js_string(f.name)}: document.getElementById({js_string(dom_id)}).value')
        else:
            lines.append(f'        {js_string(f.name)}: document.getElementById({js_string(dom_id)}).value.trim()')
    return "{\n" + ",\n".join(lines) + "\n      }"


def _generate_getbyid_fill_js(fields: List[FieldDef]) -> str:
    lines = []
    for f in form_fields(fields):
        dom_id = slugify_for_dom(f.name)
        lines.append(
            f'        document.getElementById({js_string(dom_id)}).value = r.record[{js_string(f.name)}] || "";'
        )
    return "\n".join(lines)



def _generate_record_fill_js(fields: List[FieldDef]) -> str:
    lines = []
    for f in form_fields(fields):
        dom_id = slugify_for_dom(f.name)
        field_key = js_string(f.name)
        element_id = js_string(dom_id)
        lines.append(
            f'    if (Object.prototype.hasOwnProperty.call(record, {field_key})) '
            f'document.getElementById({element_id}).value = '
            f'String(record[{field_key}] ?? "");'
        )
    return "\n".join(lines)



def generate_index_html(project_config: Dict[str, Any], fields_schema: Dict[str, Any]) -> str:
    fields = field_map_from_schema(fields_schema)
    constraints = constraints_from_schema(fields_schema)

    project_name = project_config["projectName"]
    entity_name = project_config["entityName"]
    sheet_name = project_config["sheetName"]
    project_slug = project_config.get("projectSlug", "horror-movie")

    form_html = _generate_form_html(fields, constraints)
    payload_js = _generate_payload_js(fields)
    fill_js = _generate_getbyid_fill_js(fields)
    record_fill_js = _generate_record_fill_js(fields)

    return f'''<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{escape_html(project_name)}</title>
  <style>
    body {{ font-family: Arial, sans-serif; max-width: 1100px; margin: 28px auto; padding: 0 16px; }}
    h1 {{ margin: 0 0 6px; }}
    .muted {{ color:#666; }}
    .card {{ border:1px solid #e5e5e5; border-radius:10px; padding:14px; background:#fafafa; margin:12px 0; }}
    label {{ display:block; margin:10px 0 6px; font-weight:700; }}
    input, select {{ width:100%; padding:9px; border:1px solid #ccc; border-radius:8px; box-sizing:border-box; background:#fff; }}
    button {{ padding:9px 12px; border:0; border-radius:8px; background:#111; color:#fff; cursor:pointer; font-weight:800; }}
    button.secondary {{ background:#666; }}
    button:disabled {{ opacity:.6; cursor:not-allowed; }}
    .dj-image-preview {{
      width: 100%;
      max-width: 600px;
      height: 300px;
      box-sizing: border-box;
      margin: 12px 0;
      padding: 12px;
      border: 1px solid #d1d5db;
      border-radius: 10px;
      background: #f1f5f9;
    }}
    .dj-image-preview[hidden] {{ display: none; }}
    .dj-image-preview a {{
      display: flex;
      width: 100%;
      height: 100%;
      align-items: center;
      justify-content: center;
    }}
    .dj-image-preview img {{
      max-width: 100%;
      max-height: 100%;
      object-fit: contain;
    }}
    .row {{ display:grid; grid-template-columns: 1fr 1fr; gap:12px; }}
    .actions {{ display:flex; gap:10px; align-items:center; flex-wrap:wrap; margin-top:12px; }}
    .ok {{ color:#0a6; font-weight:800; }}
    .err {{ color:#b00; font-weight:800; }}
    iframe {{ width:100%; height:560px; border:1px solid #ddd; border-radius:10px; background:#fff; }}
    small {{ display:block; margin-top:8px; color:#666; }}
    pre {{ background:#0b0b0b; color:#d6ffd6; border-radius:10px; padding:12px; overflow:auto; }}
  </style>
</head>
<body>

  <h1>{escape_html(project_name)} database</h1>

<p class="muted">
  Manage records, update data and browse the current spreadsheet table.
</p>

    <div id="debugPanel" class="card" style="display:none;">
    <h3 style="margin:0 0 10px;">Developer tools</h3>

    <p class="muted">
      Technical checks for backend connection and schema validation.
    </p>

    <div class="actions">
      <button id="pingBtn" type="button">meta</button>
      <button id="schemaBtn" type="button" class="secondary">schema</button>
      <span id="cfgStatus" class="muted"></span>
    </div>

    <small>Slug app: <code>{escape_html(project_slug)}</code></small>
  </div>

  <div class="card">
    <h3 style="margin:0 0 10px;">Insert ({escape_html(entity_name)})</h3>

{form_html}

    <div style="margin:12px 0;">
      <label for="crud_id">Record ID</label>
      <input id="crud_id" type="text" readonly
             placeholder="Assigned automatically"
             style="max-width:180px; background:#f1f5f9; cursor:default;" />
      <small class="muted">Identificativo del record, non modificabile.</small>
    </div>

    <div class="actions">
      <button id="insertBtn" type="button">Insert</button>
      <button id="saveChangesBtn" type="button" hidden>Save changes</button>
      <button id="deleteBtn" type="button" class="secondary" hidden>Delete</button>
      <button id="cancelEditBtn" type="button" class="secondary" hidden>Annulla modifica</button>
      <span id="insertStatus" class="muted"></span>
      <span id="crudStatus" class="muted"></span>
    </div>
  </div>

  <div class="card">
 <h3 style="margin:0 0 10px;">Data viewer</h3>
<p class="muted">
  Browse the current records stored in the connected spreadsheet.
</p>



<iframe id="viewer" loading="lazy"></iframe>
    <div class="actions">
      <span class="muted">Il viewer si aggiorna automaticamente dopo insert/update/delete.</span>
    </div>
  </div>
  
<div class="card">
  <h3 style="margin:0 0 10px;">Configuration</h3>

  <p class="muted">
    Need to change labels, visible columns or colors?
  </p>

  <div class="actions">
    <button id="customizeConfigBtn" type="button" class="secondary">
      Customize app configuration
    </button>
  </div>
</div>

<div id="responsePanel" class="card" style="display:none;">
  <div class="muted">Developer response</div>
  <pre id="out"></pre>
</div>

<script>
  
  const qs = new URLSearchParams(window.location.search);
  const DEBUG_MODE = qs.get("debug") === "1";
  const APP_SLUG = qs.get("app") || {js_string(project_slug)};

  function setMsg(el, msg, cls) {{
    el.className = cls || "muted";
    el.textContent = msg;
  }}


    async function apiCall_(mode, params = {{}}) {{
    let url = `/api/apps/${{APP_SLUG}}/${{mode}}`;

    const qs = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {{
      qs.set(k, String(v ?? ""));
    }});

    const query = qs.toString();
    if (query) url += "?" + query;

    const resp = await fetch(url);
    const data = await resp.json();

    if (!resp.ok) {{
      throw new Error(data.error || `HTTP ${{resp.status}}`);
    }}

    return data;
  }}

    function apiUrl_(mode) {{
    return `/api/apps/${{APP_SLUG}}/${{mode}}`;
  }}

  async function apiCall_(mode, params = {{}}, method = "GET") {{
    let url = apiUrl_(mode);

    const options = {{
      method,
      headers: {{}}
    }};

    if (method === "GET") {{
      const qs = new URLSearchParams();
      Object.entries(params).forEach(([k, v]) => {{
        qs.set(k, String(v ?? ""));
      }});

      const query = qs.toString();
      if (query) url += "?" + query;
    }} else {{
      options.headers["Content-Type"] = "application/json";
      options.body = JSON.stringify(params);
    }}

    const resp = await fetch(url, options);
    const data = await resp.json();

    out.textContent = JSON.stringify(data, null, 2);

    if (!resp.ok) {{
      throw new Error(data.error || `HTTP ${{resp.status}}`);
    }}

    return data;
  }}

  function viewerUrl_(cacheBust) {{
  const basePath = window.location.pathname.replace(/[^\\/]*$/, "");
  const u = new URL(basePath + "viewer.html", window.location.origin);
  u.searchParams.set("app", APP_SLUG);
  u.searchParams.set("limit", "50");
  u.searchParams.set("embedded", "1");
  if (cacheBust) u.searchParams.set("_", Date.now().toString());
  return u.toString();
}}

  const out = document.getElementById("out");
const viewer = document.getElementById("viewer");

const actionButtons = [
  "insertBtn",
  "saveChangesBtn",
  "deleteBtn",
  "cancelEditBtn",
  "pingBtn",
  "schemaBtn"
]
  .map(id => document.getElementById(id))
  .filter(Boolean);

const formControls = Array.from(document.querySelectorAll("input, select, button"));

let IS_BUSY = false;

function setBusy(isBusy, message = "") {{
  IS_BUSY = Boolean(isBusy);

  formControls.forEach(el => {{
    el.disabled = IS_BUSY;
  }});

  if (message) {{
    const insertStatus = document.getElementById("insertStatus");
    const crudStatus = document.getElementById("crudStatus");

    if (insertStatus) setMsg(insertStatus, message, "muted");
    if (crudStatus) setMsg(crudStatus, message, "muted");
  }}
}}

async function call_(mode, params = {{}}, needsKey = false) {{
  const method = needsKey ? "POST" : "GET";
  return await apiCall_(mode, params, method);
}}

    function loadViewer(cacheBust) {{
    viewer.src = viewerUrl_(cacheBust);
  }}

  function refreshViewerSoon(delayMs = 700) {{
    setTimeout(() => loadViewer(true), delayMs);
  }}

  document.getElementById("pingBtn").addEventListener("click", async () => {{
    try {{
      setMsg(document.getElementById("cfgStatus"), "Calling meta…");
      const r = await call_("meta", {{}}, false);
      setMsg(
        document.getElementById("cfgStatus"),
        r.ok ? "OK meta" : ("ERR: " + (r.error || "")),
        r.ok ? "ok" : "err"
      );
      loadViewer(false);
    }} catch (e) {{
      setMsg(document.getElementById("cfgStatus"), "ERR: " + e.message, "err");
    }}
  }});

  document.getElementById("schemaBtn").addEventListener("click", async () => {{
    try {{
      setMsg(document.getElementById("cfgStatus"), "Calling schema…");
      const r = await call_("schema", {{}}, false);
      setMsg(
        document.getElementById("cfgStatus"),
        r.ok ? "OK schema" : ("ERR: " + (r.error || "")),
        r.ok ? "ok" : "err"
      );
    }} catch (e) {{
      setMsg(document.getElementById("cfgStatus"), "ERR: " + e.message, "err");
    }}
  }});

  document.getElementById("insertBtn").addEventListener("click", async () => {{
  const st = document.getElementById("insertStatus");
  try {{
    setBusy(true, "Operation in progress. Please wait…");
    setMsg(st, "Inserting…");

    const payload = {payload_js};

    const r = await call_("insert", payload, true);

    if (r.ok) {{
      setMsg(st, `OK inserted id=${{r.id}}`, "ok");
      refreshViewerSoon();
    }} else {{
      setMsg(st, "ERR: " + (r.error || "Unknown error"), "err");
    }}

  }} catch (e) {{
    setMsg(st, "ERR: " + e.message, "err");
  }} finally {{
    setTimeout(() => setBusy(false), 900);
  }}
}});

  document.getElementById("saveChangesBtn").addEventListener("click", async () => {{
    const st = document.getElementById("crudStatus");
    try {{
      if (FORM_MODE !== "edit") return;

      const id = document.getElementById("crud_id").value.trim();
      if (!/^[1-9][0-9]*$/.test(id)) throw new Error("Invalid record ID");

      setBusy(true, "Operation in progress. Please wait…");
      setMsg(st, "Updating record…");

      const payload = {payload_js};
      payload.id = id;

      const r = await call_("update", payload, true);

      if (!r.ok) throw new Error(r.error || "Unknown error");

      clearEditForm();
      setMsg(st, `OK updated id=${{id}}`, "ok");
      refreshViewerSoon();

    }} catch (e) {{
      setMsg(st, "ERR: " + e.message, "err");
    }} finally {{
      setTimeout(() => setBusy(false), 900);
    }}
  }});

  document.getElementById("cancelEditBtn").addEventListener("click", () => {{
    clearEditForm();
    setMsg(document.getElementById("crudStatus"), "");
    setMsg(document.getElementById("insertStatus"), "");
  }});

  document.getElementById("customizeConfigBtn").addEventListener("click", () => {{
  window.location.href =
    `review.html?autoload=1&returnApp=${{encodeURIComponent(APP_SLUG)}}`;
}});

  document.getElementById("deleteBtn").addEventListener("click", async () => {{
    const st = document.getElementById("crudStatus");

    try {{
      if (FORM_MODE !== "edit") return;

      const id = document.getElementById("crud_id").value.trim();
      if (!/^[1-9][0-9]*$/.test(id)) {{
        throw new Error("Invalid record ID");
      }}

      if (!confirm(`Delete record id=${{id}}?`)) return;

      setBusy(true, "Operation in progress. Please wait…");
      setMsg(st, "Deleting record…");

      const r = await call_("delete", {{ id }}, true);
      if (!r.ok) throw new Error(r.error || "Unknown error");

      clearEditForm();
      setMsg(st, `OK deleted id=${{id}}`, "ok");
      refreshViewerSoon();

    }} catch (e) {{
      setMsg(st, "ERR: " + e.message, "err");
    }} finally {{
      setTimeout(() => setBusy(false), 900);
    }}
  }});

  if (DEBUG_MODE) {{
  const debugPanel = document.getElementById("debugPanel");
  const responsePanel = document.getElementById("responsePanel");

  if (debugPanel) debugPanel.style.display = "block";
  if (responsePanel) responsePanel.style.display = "block";
}}

let FORM_MODE = "insert";

function setFormMode(mode) {{
  FORM_MODE = mode === "edit" ? "edit" : "insert";
  const editing = FORM_MODE === "edit";

  document.getElementById("insertBtn").hidden = editing;
  document.getElementById("saveChangesBtn").hidden = !editing;
  document.getElementById("deleteBtn").hidden = !editing;
  document.getElementById("cancelEditBtn").hidden = !editing;
}}

function imageUrlFromValue(value) {{
  try {{
    const url = new URL(String(value ?? "").trim());
    if (!["http:", "https:"].includes(url.protocol)) return null;
    return /\\.(png|jpe?g|gif|webp|avif|svg)$/i.test(url.pathname)
      ? url.href : null;
  }} catch {{
    return null;
  }}
}}

function refreshImagePreviews() {{
  document.querySelectorAll(".dj-image-preview").forEach(preview => {{
    const field = document.getElementById(preview.dataset.previewFor);
    const url = imageUrlFromValue(field?.value);
    const img = preview.querySelector("img");
    const link = preview.querySelector("a");

    if (!img || !link) return;

    preview.hidden = !url;

    if (url) {{
      if (img.getAttribute("src") !== url) img.src = url;
      link.href = url;
    }} else {{
      img.removeAttribute("src");
      link.removeAttribute("href");
    }}
  }});
}}

document.querySelectorAll(".dj-image-preview").forEach(preview => {{
  const field = document.getElementById(preview.dataset.previewFor);
  field?.addEventListener("input", refreshImagePreviews);
}});

function clearEditForm() {{
  document.getElementById("crud_id").value = "";

  document.getElementById("insertBtn")
    .closest(".card")
    .querySelectorAll("input, select, textarea")
    .forEach(field => {{
      field.value = "";
    }});

  setFormMode("insert");
  refreshImagePreviews();
}}

function populateForm(record) {{
  if (!record || typeof record !== "object" || Array.isArray(record)) return false;

  clearEditForm();
{record_fill_js}
  refreshImagePreviews();
  return true;
}}

window.addEventListener("message", event => {{
  if (event.origin !== window.location.origin) return;
  if (event.source !== viewer.contentWindow) return;
  if (IS_BUSY) return;

  if (event.data?.type !== "DJUNGO_EDIT_RECORD") return;

  const id = String(event.data.id ?? "").trim();
  if (!/^[1-9][0-9]*$/.test(id)) return;

  if (!populateForm(event.data.record)) return;

  document.getElementById("crud_id").value = id;
  setFormMode("edit");

  setMsg(document.getElementById("crudStatus"), "");
  setMsg(document.getElementById("insertStatus"), "");

  const formCard = document.getElementById("insertBtn").closest(".card");
  formCard?.scrollIntoView({{ behavior: "smooth", block: "start" }});
}});

loadViewer(false);
</script>

</body>
</html>
'''
# ============================================================
# VIEWER.HTML GENERATOR
# ============================================================

def _generate_viewer_visible_columns_js(fields: List[FieldDef]) -> str:
    return js_pretty([f.name for f in viewer_fields(fields)])


def _generate_viewer_enum_map_js(fields: List[FieldDef]) -> str:
    return js_pretty(enum_map(fields))


def _generate_viewer_label_map_js(fields: List[FieldDef]) -> str:
    return js_pretty({f.name: (f.label or f.name) for f in viewer_fields(fields)})


def _generate_viewer_enum_styles_js(fields: List[FieldDef]) -> str:
    return js_pretty(enum_styles_map(fields))


def generate_viewer_html(project_config: Dict[str, Any], fields_schema: Dict[str, Any]) -> str:
    fields = field_map_from_schema(fields_schema)
    visible_cols_js = _generate_viewer_visible_columns_js(fields)
    sort_config_js = js_pretty({
        f.name: {
            "sortType": f.sort_type,
            "fieldType": f.type
        }
        for f in viewer_fields(fields)
    })
    display_config_js = js_pretty({
        f.name: f.display_type
        for f in viewer_fields(fields)
    })
    enum_map_js = _generate_viewer_enum_map_js(fields)
    label_map_js = _generate_viewer_label_map_js(fields)
    header_aliases_js = js_pretty({
        f.original_header or f.name: f.name
        for f in fields
    })
    enum_styles_js = _generate_viewer_enum_styles_js(fields)

    has_record_id = any(f.name == "id" and f.type == "int" for f in fields)
    has_record_id_js = js_pretty(has_record_id)

    entity_name = project_config["entityName"]
    sheet_name = project_config["sheetName"]
    project_slug = project_config.get("projectSlug", "horror-movie")

    return f'''<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{escape_html(entity_name)} Viewer</title>
  <link href="https://cdn.jsdelivr.net/npm/tabulator-tables@6.4.0/dist/css/tabulator.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/tabulator-tables@6.4.0/dist/js/tabulator.min.js"></script>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 12px; }}
    .muted {{ color:#666; }}
    .toolbar {{ display:flex; gap:10px; align-items:end; flex-wrap:wrap; margin: 8px 0 12px; }}
    .toolbar label {{ display:block; font-size:12px; font-weight:700; color:#444; margin-bottom:4px; }}
    .toolbar input, .toolbar select {{
      padding:8px;
      border:1px solid #ccc;
      border-radius:8px;
      background:#fff;
      min-width:180px;
    }}

    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{
      border:1px solid #e5e5e5;
      padding:8px;
      font-size: 13px;
      vertical-align: top;
      overflow-wrap:anywhere;
      white-space: pre-wrap;
    }}

    thead th {{
      position: sticky;
      top: 0;
      z-index: 2;
      background: #2f3b52;
      color: #fff;
      font-weight: 800;
    }}

    tbody tr:nth-child(even){{ background:#f6f8fb; }}
    tbody tr:nth-child(odd){{ background:#ffffff; }}

    tbody tr.first-row {{
      background: #fff3cd !important;
      outline: 2px solid #ffe69c;
      outline-offset: -2px;
    }}
    /* B34-03: pannello laterale di dettaglio */
    .detail-panel {{
      position: fixed;
      top: 0;
      right: 0;
      width: min(420px, 100%);
      height: 100%;
      box-sizing: border-box;
      background: #fff;
      box-shadow: -6px 0 24px rgba(0,0,0,.18);
      z-index: 1000;
      display: flex;
      flex-direction: column;
    }}
    .detail-panel[hidden] {{ display: none; }}
    .detail-header, .detail-actions {{
      padding: 14px;
      border-bottom: 1px solid #ddd;
    }}
    .detail-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .detail-content {{
      padding: 14px;
      overflow-y: auto;
      flex: 1;
    }}
    .detail-actions {{
      display: flex;
      gap: 8px;
      border-top: 1px solid #ddd;
      border-bottom: 0;
    }}
    .detail-actions button {{ padding: 9px 12px; cursor: pointer; }}
    .detail-actions button[hidden] {{ display: none; }}
    .detail-field {{ margin-bottom: 14px; }}
    .detail-field-label {{ font-size: 12px; font-weight: bold; color: #555; }}
    .detail-field-value {{ margin-top: 4px; overflow-wrap: anywhere; white-space: pre-wrap; }}
  </style>
</head>
<body>

  <div class="muted">Viewer read-only — tab <b>{escape_html(sheet_name)}</b></div>

  <div class="toolbar">
    <div>
      <label for="searchBox">Filtro testo</label>
      <input id="searchBox" type="text" placeholder="Cerca..." />
    </div>
    <div>
      <label for="limitBox">Limite righe</label>
      <select id="limitBox">
        <option>20</option>
        <option selected>50</option>
        <option>100</option>
        <option>200</option>
      </select>
    </div>
  </div>

  <div id="status" class="muted" style="margin:6px 0;">Caricamento…</div>
  <div id="dataTable"></div>

<script>
  const qs = new URLSearchParams(location.search);
  const APP_SLUG = qs.get("app") || {js_string(project_slug)};
  const URL_LIMIT = qs.get("limit") || "50";
  const EMBEDDED_MODE = qs.get("embedded") === "1";

  const HAS_RECORD_ID = {has_record_id_js};
  const VISIBLE_HEADERS = {visible_cols_js};
  const ENUMS = {enum_map_js};
  const LABELS = {label_map_js};
  const HEADER_ALIASES = {header_aliases_js};
  const ENUM_STYLES = {enum_styles_js};
  const DISPLAY_CONFIG = {display_config_js};

    async function apiCall_(mode, params = {{}}) {{
    let url = `/api/apps/${{APP_SLUG}}/${{mode}}`;

    const qs = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {{
      qs.set(k, String(v ?? ""));
    }});

    const query = qs.toString();
    if (query) url += "?" + query;

    const resp = await fetch(url);
    const data = await resp.json();

    if (!resp.ok) {{
      throw new Error(data.error || `HTTP ${{resp.status}}`);
    }}

    return data;
  }}

  function esc(s) {{
    return String(s ?? "").replace(/[&<>"']/g, c => (
      {{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]
    ));
  }}

  function safeHttpUrl(value) {{
    const raw = String(value ?? "").trim();
    if (!raw) return null;
    try {{
      const url = new URL(raw);
      return ["http:", "https:"].includes(url.protocol) ? url.href : null;
    }} catch {{
      return null;
    }}
  }}

  function renderDisplayValue(header, rawValue) {{
    const value = String(rawValue ?? "");
    const url = safeHttpUrl(value);

    if (url) {{
      const parsed = new URL(url);
      const isImage = /\\.(png|jpe?g|gif|webp|avif|svg)$/i.test(parsed.pathname);

      if (isImage) {{
        const img = document.createElement("img");
        img.src = url;
        img.alt = "Immagine: " + header;
        img.loading = "lazy";
        img.style.maxWidth = "120px";
        img.style.maxHeight = "80px";
        img.style.objectFit = "contain";
        return img;
      }}

      const link = document.createElement("a");
      link.href = url;
      link.textContent = "LINK";
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      return link;
    }}

    const span = document.createElement("span");
    span.textContent = value;
    return span;
  }}

  function styleAttrForEnum(headerName, value) {{
    const fieldStyles = ENUM_STYLES[resolveFieldKey(headerName)];
    if (!fieldStyles) return "";
    const styleDef = fieldStyles[String(value ?? "").trim()];
    if (!styleDef) return "";

    const parts = [];
    if (styleDef.bg) parts.push(`background:${{styleDef.bg}}`);
    if (styleDef.fg) parts.push(`color:${{styleDef.fg}}`);
    if (!parts.length) return "";

    parts.push("font-weight:700");
    parts.push("text-align:center");
    return parts.join("; ");
  }}

  let LAST_HEADERS = [];
  let LAST_ROWS = [];

    let DATA_TABLE = null;

  function rowsToObjects(headers, rows) {{
    return rows.map(row => {{
      const obj = {{}};

      headers.forEach((h, i) => {{
        obj[h] = row[i];
      }});

      return obj;
    }});
  }}

  function normalizeHeader(h) {{
    return String(h ?? "").trim().toLowerCase();
  }}

  function resolveFieldKey(header) {{
    const normalized = normalizeHeader(header);
    const alias = Object.keys(HEADER_ALIASES).find(
      key => normalizeHeader(key) === normalized
    );
    if (alias) return HEADER_ALIASES[alias];

    return Object.keys(LABELS).find(
      key => normalizeHeader(key) === normalized
    ) || header;
  }}

  function normalizeRecord(record) {{
    const normalized = {{}};
    Object.entries(record).forEach(([header, value]) => {{
      const key = resolveFieldKey(header);
      normalized[key] = value;
    }});
    return normalized;
  }}

  function isVisibleHeader(h) {{
    return VISIBLE_HEADERS.includes(resolveFieldKey(h));
  }}

  const COLUMN_SORT_CONFIG = {sort_config_js};

  function numericSortValue(value) {{
    if (value === null || value === undefined || String(value).trim() === "") return null;
    let s = String(value).trim().replace(/\\s/g, "");
    if (s.includes(",") && s.includes(".")) {{
      s = s.lastIndexOf(",") > s.lastIndexOf(".")
        ? s.replace(/\\./g, "").replace(",", ".")
        : s.replace(/,/g, "");
    }} else if (s.includes(",")) {{
      s = s.replace(",", ".");
    }}
    const n = Number(s);
    return Number.isFinite(n) ? n : null;
  }}

  function italianDateValue(value) {{
    const s = String(value ?? "").trim();
    const match = s.match(/^(\\d{{1,2}})\\/(\\d{{1,2}})\\/(\\d{{4}})(?:[ T](\\d{{1,2}}):(\\d{{2}})(?::(\\d{{2}}))?)?$/);
    if (!match) return null;
    const [, day, month, year, hour = "0", minute = "0", second = "0"] = match;
    const d = new Date(Number(year), Number(month) - 1, Number(day), Number(hour), Number(minute), Number(second));
    if (d.getFullYear() !== Number(year) || d.getMonth() !== Number(month) - 1 ||
        d.getDate() !== Number(day) || d.getHours() !== Number(hour) ||
        d.getMinutes() !== Number(minute) || d.getSeconds() !== Number(second)) return null;
    return d.getTime();
  }}

  function compareNullable(a, b, parser) {{
    const x = parser(a);
    const y = parser(b);
    if (x === null && y === null) return 0;
    if (x === null) return -1;
    if (y === null) return 1;
    return x - y;
  }}

  function getColumnSorter(header) {{
    const config = COLUMN_SORT_CONFIG[resolveFieldKey(header)] || {{}};
    let type = config.sortType || "auto";
    if (type === "auto") {{
      const fieldType = String(config.fieldType || "").toLowerCase();
      type = ["int", "integer", "float", "number", "decimal"].includes(fieldType)
        ? "number"
        : ["date", "datetime", "timestamp"].includes(fieldType)
          ? "date_it"
          : "string";
    }}
    if (type === "number") {{
      return (a, b) => compareNullable(a, b, numericSortValue);
    }}
    if (type === "date_it" || type === "datetime_it") {{
      return (a, b) => compareNullable(a, b, italianDateValue);
    }}
    return "string";
  }}

  function buildColumns(headers) {{
    return headers
      .filter(h => isVisibleHeader(h))
      .map(h => {{
        return {{
          title: LABELS[resolveFieldKey(h)] || h,
          field: h,
          headerFilter: "input",
          sorter: getColumnSorter(h),
          resizable: true,
          formatter: function(cell) {{
            const value = cell.getValue();
            const style = styleAttrForEnum(h, value);

            if (style) {{
              const el = cell.getElement();

              style.split(";").forEach(rule => {{
                const parts = rule.split(":");

                if (parts.length === 2) {{
                  el.style[parts[0].trim()] = parts[1].trim();
                }}
              }});
            }}

            return renderDisplayValue(h, value);
          }}
        }};
      }});
  }}

  function renderTable() {{
    const status = document.getElementById("status");
    const search = document.getElementById("searchBox").value.trim().toLowerCase();

    if (!LAST_HEADERS.length) {{
      status.textContent = "No data loaded";
      return;
    }}

    const visibleHeaders = LAST_HEADERS.filter(h => isVisibleHeader(h));

    const visibleIndexes = LAST_HEADERS
      .map((h, i) => (visibleHeaders.includes(h) ? i : -1))
      .filter(i => i >= 0);

    let rows = LAST_ROWS.slice();

    if (search) {{
      rows = rows.filter(r =>
        visibleIndexes.some(i =>
          String(r[i] ?? "").toLowerCase().includes(search)
        )
      );
    }}

    const tableData = rowsToObjects(LAST_HEADERS, rows);
    const columns = buildColumns(LAST_HEADERS);

    if (DATA_TABLE) {{
      DATA_TABLE.setColumns(columns);
      DATA_TABLE.setData(tableData);
    }} else {{
      DATA_TABLE = new Tabulator("#dataTable", {{
        data: tableData,
        columns: columns,
        layout: "fitDataStretch",
        height: "520px",
        movableColumns: true,
        pagination: "local",
        paginationSize: 25,
        paginationSizeSelector: [10, 25, 50, 100],
        placeholder: "No records found"
      }});
      DATA_TABLE.on("rowClick", function(event, row) {{
        if (event.target.closest("a")) return;

        const record = normalizeRecord(row.getData());
        const id = String(record.id ?? "").trim();

        if (!/^[1-9][0-9]*$/.test(id)) return;

        window.parent.postMessage(
          {{ type: "DJUNGO_EDIT_RECORD", id, record }},
          window.location.origin
        );
      }});

    }}

    status.textContent = `${{rows.length}} records loaded`;
  }}


    async function load() {{
    const status = document.getElementById("status");

    try {{
      const limit = document.getElementById("limitBox").value || URL_LIMIT;
      const resp = await apiCall_("view", {{ limit }});

      if (!resp || resp.ok !== true) {{
        status.textContent = "Errore: " + (resp?.error || "risposta non valida");
        return;
      }}

      LAST_HEADERS = resp.headers || [];
      LAST_ROWS = (resp.rows || []).slice().reverse();

      renderTable();

    }} catch (e) {{
      status.textContent = "Errore: " + e.message;
    }}
  }}
  
  if (EMBEDDED_MODE) {{
  const toolbar = document.querySelector(".toolbar");
  if (toolbar) toolbar.style.display = "none";

  const topLabel = document.querySelector(".muted");
  if (topLabel) topLabel.style.display = "none";
}}

  document.getElementById("searchBox").addEventListener("input", renderTable);
  document.getElementById("limitBox").value = URL_LIMIT;
  document.getElementById("limitBox").addEventListener("change", load);

  load();
</script>

</body>
</html>
'''

# ============================================================
# PUBLIC API
# ============================================================

def generate_all(
    project_config: Dict[str, Any],
    fields_schema: Dict[str, Any],
    include_gas: bool = True,
) -> Dict[str, str]:
    generated = {
        "docs/index.html": generate_index_html(project_config, fields_schema),
        "docs/viewer.html": generate_viewer_html(project_config, fields_schema),
    }

    if include_gas:
        generated["codice.gs"] = generate_gas_backend(
            project_config, fields_schema
        )

    return generated