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
    headers = fields_schema["headers"]
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

const HEADERS = {js_pretty(headers)};
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
  const lastCol = Math.max(sh.getLastColumn(), HEADERS.length);
  const row1 = sh.getRange(1, 1, 1, lastCol).getValues()[0].slice(0, HEADERS.length);
  const row1Norm = row1.map(x => String(x || "").trim());

  const ok = HEADERS.every((h, i) => row1Norm[i] === h);

  if (!ok) {{
    const allEmpty = row1Norm.every(x => !x);
    if (allEmpty && sh.getLastRow() === 0) {{
      sh.getRange(1, 1, 1, HEADERS.length).setValues([HEADERS]);
      return;
    }}
    throw new Error("Header mismatch in sheet. Expected: " + HEADERS.join(", "));
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

    placeholder = label
    if field.type == "date":
        placeholder = constraints.get(field.name, {}).get("format", "dd/mm/yyyy")

    return f'''
    <label for="{dom_id}">{label} <span class="muted">({required_label})</span></label>
    <input id="{dom_id}" placeholder="{escape_html(placeholder)}" />'''.rstrip()


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


def generate_index_html(project_config: Dict[str, Any], fields_schema: Dict[str, Any]) -> str:
    fields = field_map_from_schema(fields_schema)
    constraints = constraints_from_schema(fields_schema)

    project_name = project_config["projectName"]
    entity_name = project_config["entityName"]
    sheet_name = project_config["sheetName"]

    form_html = _generate_form_html(fields, constraints)
    payload_js = _generate_payload_js(fields)
    fill_js = _generate_getbyid_fill_js(fields)

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

  <h1>{escape_html(project_name)} <span class="muted">— generated</span></h1>
  <p class="muted">
    Backend: Google Apps Script (JSONP) → tab <b>{escape_html(sheet_name)}</b>.
    <br>Read: pubblico. Write: protetto da <code>apiKey</code>.
  </p>

  <div class="card">
    <h3 style="margin:0 0 10px;">Config</h3>

    <label for="apiKey">apiKey (solo insert/update/delete/getById)</label>
    <input id="apiKey" type="password" autocomplete="off" spellcheck="false"
           placeholder="Inserisci la chiave admin" />

    <label for="webAppUrl">Web App URL</label>
    <input id="webAppUrl" type="text" autocomplete="off" spellcheck="false"
           placeholder="https://script.google.com/macros/s/.../exec" />

    <div class="actions">
      <button id="pingBtn" type="button">meta</button>
      <button id="schemaBtn" type="button" class="secondary">schema</button>
      <span id="cfgStatus" class="muted"></span>
    </div>

    <small>Tip: fai prima <b>schema</b>, poi inserisci 1 record, poi controlla nel viewer.</small>
  </div>

  <div class="card">
    <h3 style="margin:0 0 10px;">Insert ({escape_html(entity_name)})</h3>

{form_html}

    <div class="actions">
      <button id="insertBtn" type="button">Insert</button>
      <span id="insertStatus" class="muted"></span>
    </div>
  </div>

  <div class="card">
    <h3 style="margin:0 0 10px;">CRUD by id</h3>
    <div class="row">
      <div>
        <label for="crud_id">id</label>
        <input id="crud_id" type="number" min="1" step="1" placeholder="1" />
      </div>
      <div>
        <label>&nbsp;</label>
        <div class="actions" style="margin-top:0;">
          <button id="getBtn" type="button" class="secondary">getById</button>
          <button id="updateBtn" type="button">update</button>
          <button id="deleteBtn" type="button" class="secondary">delete</button>
        </div>
      </div>
    </div>

    <div class="actions">
      <span id="crudStatus" class="muted"></span>
    </div>
  </div>

  <div class="card">
    <h3 style="margin:0 0 10px;">Viewer (read-only)</h3>
    <iframe id="viewer" loading="lazy"></iframe>
    <div class="actions">
      <span class="muted">Il viewer si aggiorna automaticamente dopo insert/update/delete.</span>
    </div>
  </div>

  <div class="card">
    <div class="muted">Response</div>
    <pre id="out"></pre>
  </div>

<script>
  function setMsg(el, msg, cls) {{
    el.className = cls || "muted";
    el.textContent = msg;
  }}

  function makeCbName() {{
    return "cb_" + Date.now() + "_" + Math.floor(Math.random() * 1e6);
  }}

  function jsonp(url) {{
    return new Promise((resolve, reject) => {{
      const cbName = makeCbName();
      const script = document.createElement("script");

      const t = setTimeout(() => {{
        cleanup();
        reject(new Error("Timeout JSONP"));
      }}, 15000);

      function cleanup() {{
        clearTimeout(t);
        try {{ delete window[cbName]; }} catch (_) {{ window[cbName] = undefined; }}
        script.remove();
      }}

      window[cbName] = (data) => {{
        cleanup();
        resolve(data);
      }};

      const u = new URL(url);
      u.searchParams.set("cb", cbName);
      u.searchParams.set("_", Date.now().toString());

      script.src = u.toString();
      script.onerror = () => {{
        cleanup();
        reject(new Error("JSONP load error (check /exec + access)"));
      }};

      document.body.appendChild(script);
    }});
  }}

  function baseUrl_() {{
    return document.getElementById("webAppUrl").value.trim();
  }}

  function apiKey_() {{
    return document.getElementById("apiKey").value.trim();
  }}

  function viewerUrl_(cacheBust) {{
    const basePath = window.location.pathname.replace(/[^\\/]*$/, "");
    const u = new URL(basePath + "viewer.html", window.location.origin);
    u.searchParams.set("webApp", baseUrl_());
    u.searchParams.set("limit", "50");
    if (cacheBust) u.searchParams.set("_", Date.now().toString());
    return u.toString();
  }}

  const out = document.getElementById("out");
  const viewer = document.getElementById("viewer");

  async function call_(mode, params = {{}}, needsKey = false) {{
    const webApp = baseUrl_();
    if (!webApp) throw new Error("Missing Web App URL");

    const u = new URL(webApp);
    u.searchParams.set("mode", mode);
    if (needsKey) u.searchParams.set("apiKey", apiKey_());

    Object.entries(params).forEach(([k, v]) => {{
      u.searchParams.set(k, String(v ?? ""));
    }});

    const resp = await jsonp(u.toString());
    out.textContent = JSON.stringify(resp, null, 2);
    return resp;
  }}

  function loadViewer(cacheBust) {{
    const webApp = baseUrl_();
    if (!webApp) return;
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
    }}
  }});

  document.getElementById("getBtn").addEventListener("click", async () => {{
    const st = document.getElementById("crudStatus");
    try {{
      const id = document.getElementById("crud_id").value.trim();
      setMsg(st, "Loading…");

      const r = await call_("getById", {{ id }}, true);

      setMsg(
        st,
        r.ok ? `OK loaded id=${{id}}` : ("ERR: " + (r.error || "")),
        r.ok ? "ok" : "err"
      );

      if (r.ok && r.record) {{
{fill_js}
      }}
    }} catch (e) {{
      setMsg(st, "ERR: " + e.message, "err");
    }}
  }});

  document.getElementById("updateBtn").addEventListener("click", async () => {{
    const st = document.getElementById("crudStatus");
    try {{
      const id = document.getElementById("crud_id").value.trim();
      setMsg(st, "Updating…");

      const payload = {payload_js};
      payload.id = id;

      const r = await call_("update", payload, true);

      setMsg(
        st,
        r.ok ? `OK updated id=${{id}}` : ("ERR: " + (r.error || "")),
        r.ok ? "ok" : "err"
      );

      if (r.ok) {{
        refreshViewerSoon();
      }}

    }} catch (e) {{
      setMsg(st, "ERR: " + e.message, "err");
    }}
  }});

  document.getElementById("deleteBtn").addEventListener("click", async () => {{
    const st = document.getElementById("crudStatus");
    try {{
      const id = document.getElementById("crud_id").value.trim();
      if (!id) throw new Error("Missing id");
      if (!confirm(`Delete id=${{id}}?`)) return;

      setMsg(st, "Deleting…");

      const r = await call_("delete", {{ id }}, true);

      setMsg(
        st,
        r.ok ? `OK deleted id=${{id}}` : ("ERR: " + (r.error || "")),
        r.ok ? "ok" : "err"
      );

      if (r.ok) {{
        refreshViewerSoon();
      }}

    }} catch (e) {{
      setMsg(st, "ERR: " + e.message, "err");
    }}
  }});

  const apiKeyInput = document.getElementById("apiKey");
  const webAppInput = document.getElementById("webAppUrl");

  const savedKey = sessionStorage.getItem("BUILDER_API_KEY");
  const savedWebApp = sessionStorage.getItem("BUILDER_WEB_APP_URL");

  if (savedKey && !apiKeyInput.value) apiKeyInput.value = savedKey;
  if (savedWebApp && !webAppInput.value) {{
    webAppInput.value = savedWebApp;
    loadViewer(false);
  }}

  apiKeyInput.addEventListener("input", () => {{
    sessionStorage.setItem("BUILDER_API_KEY", apiKeyInput.value.trim());
  }});

  webAppInput.addEventListener("input", () => {{
    sessionStorage.setItem("BUILDER_WEB_APP_URL", webAppInput.value.trim());
    loadViewer(false);
  }});
</script>

</body>
</html>
'''


# ============================================================
# VIEWER.HTML GENERATOR
# ============================================================

def _generate_viewer_visible_columns_js(fields: List[FieldDef]) -> str:
    return js_pretty([f.name for f in viewer_fields(fields)])


def _generate_viewer_label_map_js(fields: List[FieldDef]) -> str:
    return js_pretty({f.name: (f.label or f.name) for f in viewer_fields(fields)})


def _generate_viewer_enum_styles_js(fields: List[FieldDef]) -> str:
    return js_pretty(enum_styles_map(fields))


def generate_viewer_html(project_config: Dict[str, Any], fields_schema: Dict[str, Any]) -> str:
    fields = field_map_from_schema(fields_schema)
    visible_cols_js = _generate_viewer_visible_columns_js(fields)
    enum_map_js = _generate_viewer_enum_map_js(fields)
    label_map_js = _generate_viewer_label_map_js(fields)
    enum_styles_js = _generate_viewer_enum_styles_js(fields)

    entity_name = project_config["entityName"]
    sheet_name = project_config["sheetName"]

    return f'''<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{escape_html(entity_name)} Viewer</title>
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
  <div id="tbl"></div>

<script>
  const qs = new URLSearchParams(location.search);
  const WEB_APP_URL = qs.get("webApp");
  const URL_LIMIT = qs.get("limit") || "50";

    const VISIBLE_HEADERS = {visible_cols_js};
  const ENUMS = {enum_map_js};
  const LABELS = {label_map_js};
  const ENUM_STYLES = {enum_styles_js};

  function jsonp(url) {{
    return new Promise((resolve, reject) => {{
      const cbName = "cb_" + Math.random().toString(36).slice(2);
      const script = document.createElement("script");

      const t = setTimeout(() => {{
        cleanup();
        reject(new Error("Timeout JSONP"));
      }}, 15000);

      function cleanup() {{
        clearTimeout(t);
        try {{ delete window[cbName]; }} catch (_) {{ window[cbName] = undefined; }}
        script.remove();
      }}

      window[cbName] = (data) => {{
        cleanup();
        resolve(data);
      }};

      const u = new URL(url);
      u.searchParams.set("cb", cbName);
      u.searchParams.set("_", Date.now().toString());

      script.src = u.toString();
      script.onerror = () => {{
        cleanup();
        reject(new Error("JSONP load error"));
      }};

      document.body.appendChild(script);
    }});
  }}

  function esc(s) {{
    return String(s ?? "").replace(/[&<>"']/g, c => (
      {{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]
    ));
  }}

  let LAST_HEADERS = [];
  let LAST_ROWS = [];

  function renderTable() {{
    const status = document.getElementById("status");
    const tbl = document.getElementById("tbl");
    const search = document.getElementById("searchBox").value.trim().toLowerCase();

    if (!LAST_HEADERS.length) {{
      tbl.innerHTML = "";
      status.textContent = "Nessun dato";
      return;
    }}

    const visibleIndexes = LAST_HEADERS
      .map((h, i) => (VISIBLE_HEADERS.includes(h) ? i : -1))
      .filter(i => i >= 0);

    let rows = LAST_ROWS.slice();

    if (search) {{
      rows = rows.filter(r =>
        visibleIndexes.some(i => String(r[i] ?? "").toLowerCase().includes(search))
      );
    }}

    let html = "<table><thead><tr>";
    for (const i of visibleIndexes) {{
      html += `<th>${{esc(LAST_HEADERS[i])}}</th>`;
    }}
    html += "</tr></thead><tbody>";

    for (let rI = 0; rI < rows.length; rI++) {{
      const r = rows[rI];
      const trClass = (rI === 0) ? "first-row" : "";
      html += `<tr class="${{trClass}}">`;

      for (const i of visibleIndexes) {{
        const header = LAST_HEADERS[i];
        const cellVal = r[i];

        let style = "";
        const stylesForField = ENUM_STYLES[header] || {{}};
        const styleDef = stylesForField[String(cellVal ?? "").trim()] || null;

        if (styleDef) {{
          const bg = styleDef.bg ? `background:${{styleDef.bg}};` : "";
          const fg = styleDef.fg ? `color:${{styleDef.fg}};` : "";
          style = `${{bg}}${{fg}}font-weight:700;text-align:center;`;
        }}

        html += `<td style="${{style}}">${{esc(cellVal)}}</td>`;
      }}

      html += "</tr>";
    }}

    html += "</tbody></table>";
    tbl.innerHTML = html;
    status.textContent = `OK | headers=${{LAST_HEADERS.length}} | rows=${{rows.length}}`;
  }}

  async function load() {{
    const status = document.getElementById("status");

    if (!WEB_APP_URL) {{
      status.textContent = "Errore: manca parametro 'webApp' nell'URL.";
      return;
    }}

    try {{
      const limit = document.getElementById("limitBox").value || URL_LIMIT;
      const u = new URL(WEB_APP_URL);
      u.searchParams.set("mode", "view");
      u.searchParams.set("limit", limit);

      const resp = await jsonp(u.toString());
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

def generate_all(project_config: Dict[str, Any], fields_schema: Dict[str, Any]) -> Dict[str, str]:
    return {
        "codice.gs": generate_gas_backend(project_config, fields_schema),
        "docs/index.html": generate_index_html(project_config, fields_schema),
        "docs/viewer.html": generate_viewer_html(project_config, fields_schema),
    }