# PROJECT STATE DUMP
Generated: 2026-05-25T21:00:12
Root: `/home/mauro/Scrivania/sheet-builder`

## 1. Project tree

```text
- .gitignore
- PROJECT_DUMP_CORE.txt
- README.md
+ app
  - app/__init__.py
  - app/builder_state.py
  - app/contracts.py
+ backup_layout_before_cleanup
  - backup_layout_before_cleanup/build_from_config.py
  + backup_layout_before_cleanup/docs
    - backup_layout_before_cleanup/docs/codice.gs
    - backup_layout_before_cleanup/docs/index.html
    - backup_layout_before_cleanup/docs/viewer.html
  + backup_layout_before_cleanup/generators
    - backup_layout_before_cleanup/generators/__init__.py
    - backup_layout_before_cleanup/generators/builder_generators.py
    - backup_layout_before_cleanup/generators/import_from_html.py
    - backup_layout_before_cleanup/generators/import_from_sheet.py
    - backup_layout_before_cleanup/generators/merge_schema.py
    - backup_layout_before_cleanup/generators/schema_validators.py
  + backup_layout_before_cleanup/output_gas
    - backup_layout_before_cleanup/output_gas/codice.gs
    - backup_layout_before_cleanup/output_gas/deploy.manifest.json
    - backup_layout_before_cleanup/output_gas/fields.schema.json
    - backup_layout_before_cleanup/output_gas/google_setup.md
    - backup_layout_before_cleanup/output_gas/project.config.json
    - backup_layout_before_cleanup/output_gas/sample_rows.csv
    - backup_layout_before_cleanup/output_gas/sample_rows.json
  + backup_layout_before_cleanup/output_project
    - backup_layout_before_cleanup/output_project/codice.gs
    - backup_layout_before_cleanup/output_project/deploy.manifest.json
    + backup_layout_before_cleanup/output_project/docs
      - backup_layout_before_cleanup/output_project/docs/index.html
      - backup_layout_before_cleanup/output_project/docs/viewer.html
    - backup_layout_before_cleanup/output_project/fields.schema.json
    - backup_layout_before_cleanup/output_project/project.config.json
  + backup_layout_before_cleanup/pipeline
    - backup_layout_before_cleanup/pipeline/__init__.py
    - backup_layout_before_cleanup/pipeline/build_all_from_input.py
    - backup_layout_before_cleanup/pipeline/build_schema_from_input.py
- build_from_config.py
- codice.gs
+ data
  - data/apps_registry.json
+ docs
  - docs/app_ready.html
  - docs/builder.html
  - docs/codice.gs
  - docs/generate.html
  - docs/index.html
  - docs/review.html
  - docs/viewer.html
+ examples
  + examples/case_001
    - examples/case_001/HorrorMovie.html
    - examples/case_001/movie_db.xlsx
    - examples/case_001/sheet.css
+ generators
  - generators/__init__.py
  - generators/builder_generators.py
  - generators/import_from_html.py
  - generators/import_from_sheet.py
  - generators/merge_schema.py
  - generators/rollback_to_commit.sh
  - generators/schema_validators.py
- index.html
+ output
  + output/current
    - output/current/builder_state.json
    - output/current/codice.gs
    - output/current/deploy.manifest.json
    + output/current/docs
      - output/current/docs/index.html
      - output/current/docs/viewer.html
    - output/current/fields.schema.json
    - output/current/parsed.schema.json
    - output/current/project.config.json
  + output/gas_manual
    - output/gas_manual/codice.gs
    - output/gas_manual/deploy.manifest.json
    - output/gas_manual/fields.schema.json
    - output/gas_manual/google_setup.md
    - output/gas_manual/project.config.json
    - output/gas_manual/sample_rows.csv
    - output/gas_manual/sample_rows.json
+ output_project
  - output_project/fields.schema.json
+ pipeline
  - pipeline/__init__.py
  - pipeline/apply_builder_state.py
  - pipeline/apply_review_state.py
  - pipeline/build_all_from_input.py
  - pipeline/build_schema_from_input.py
  - pipeline/generate_final_app.py
  - pipeline/prepare_review_from_input.py
- publish.sh
- requirements.txt
- server.py
+ tools
  - tools/deploy_frontend_rest.py
  - tools/prepare_google_manual.py
  - tools/project_state_dump.py
  - tools/publish_to_docs.py
- viewer.html
- wsgi.py
```

## 2. Key file contents

## File: `PROJECT_DUMP_CORE.txt`
```text


===== FILE: build_from_config.py =====
from __future__ import annotations

import json
from pathlib import Path

from generators.builder_generators import generate_all
from generators.schema_validators import validate_schema_for_product


ROOT = Path(__file__).resolve().parent
OUTPUT_PROJECT_DIR = ROOT / "output_project"

project_config_path = OUTPUT_PROJECT_DIR / "project.config.json"
fields_schema_path = OUTPUT_PROJECT_DIR / "fields.schema.json"


def main() -> None:
    if not project_config_path.exists():
        raise FileNotFoundError(f"Missing file: {project_config_path}")

    if not fields_schema_path.exists():
        raise FileNotFoundError(f"Missing file: {fields_schema_path}")

    project_config = json.loads(project_config_path.read_text(encoding="utf-8"))
    fields_schema = json.loads(fields_schema_path.read_text(encoding="utf-8"))

    errors = validate_schema_for_product(fields_schema)
    if errors:
        joined = "\n- ".join(errors)
        raise ValueError(f"Schema validation failed:\n- {joined}")

    generated = generate_all(project_config, fields_schema)

    for relative_path, content in generated.items():
        target = OUTPUT_PROJECT_DIR / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    deploy_manifest_path = OUTPUT_PROJECT_DIR / "deploy.manifest.json"
    if not deploy_manifest_path.exists():
        deploy_manifest = {
            "projectName": project_config.get("projectName", ""),
            "projectSlug": project_config.get("projectSlug", ""),
            "backendName": project_config.get("backendName", ""),
            "sheetName": project_config.get("sheetName", ""),
            "generatedFiles": list(generated.keys()),
        }
        deploy_manifest_path.write_text(
            json.dumps(deploy_manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    print("Build completed successfully.")
    print(f"Output directory: {OUTPUT_PROJECT_DIR}")


if __name__ == "__main__":
    main()

===== FILE: docs/index.html =====
<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Sheets Builder — Step 6</title>

  <style>
    body {
      font-family: Arial, sans-serif;
      max-width: 1260px;
      margin: 24px auto;
      padding: 0 16px;
      background: #f7f7f7;
      color: #111;
    }

    h1, h2 {
      margin-bottom: 8px;
    }

    .muted {
      color: #666;
    }

    .card {
      background: #fff;
      border: 1px solid #ddd;
      border-radius: 10px;
      padding: 16px;
      margin: 16px 0;
    }

    label {
      display: block;
      margin: 10px 0 6px;
      font-weight: bold;
    }

    input, textarea, select {
      width: 100%;
      box-sizing: border-box;
      padding: 10px;
      border: 1px solid #bbb;
      border-radius: 8px;
      background: #fff;
    }

    button {
      margin-top: 14px;
      padding: 10px 14px;
      border: 0;
      border-radius: 8px;
      background: #111;
      color: #fff;
      font-weight: bold;
      cursor: pointer;
    }

    button.secondary {
      background: #666;
    }

    button.warn {
      background: #a00;
    }

    button:disabled {
      opacity: .6;
      cursor: not-allowed;
    }

    .grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
    }

    .actions {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin-top: 12px;
      align-items: center;
    }

    pre {
      background: #111;
      color: #d8ffd8;
      padding: 14px;
      border-radius: 10px;
      overflow: auto;
      white-space: pre-wrap;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 10px;
      background: #fff;
    }

    th, td {
      border: 1px solid #ddd;
      padding: 8px;
      font-size: 14px;
      text-align: left;
      vertical-align: top;
    }

    th {
      background: #efefef;
    }

    .badge {
      display: inline-block;
      padding: 3px 8px;
      border-radius: 999px;
      background: #eee;
      font-size: 12px;
      margin-left: 6px;
    }

    .field-row input,
    .field-row select,
    .field-row textarea {
      font-size: 13px;
      padding: 8px;
    }

    .tiny {
      font-size: 12px;
      color: #666;
      line-height: 1.45;
    }

    .tooltip-wrap {
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }

    .tooltip-icon {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 18px;
      height: 18px;
      border-radius: 50%;
      background: #ddd;
      color: #111;
      font-size: 12px;
      cursor: help;
      position: relative;
      user-select: none;
      flex: 0 0 auto;
    }

    .tooltip-icon:hover::after {
      content: attr(data-tip);
      position: absolute;
      left: 24px;
      top: 0;
      width: 290px;
      background: #111;
      color: #fff;
      padding: 10px;
      border-radius: 8px;
      font-weight: normal;
      line-height: 1.4;
      z-index: 20;
      white-space: normal;
      text-transform: none;
    }

    .system-row {
      background: #f9fbff;
    }

    .readonly-cell {
      background: #f3f3f3;
      color: #666;
    }

    .enum-box {
      min-width: 240px;
    }

    .ok {
      color: #0a6;
      font-weight: bold;
    }
  </style>
</head>
<body>

  <h1>Sheets Builder <span class="badge">Step 6</span></h1>
  <p class="muted">
    In questo step il builder genera uno ZIP completo del progetto, inclusi i JSON di configurazione e il manifest di deploy.
  </p>

  <div class="card">
    <h2>1. Project identity</h2>

    <label for="projectName">Project name</label>
    <input id="projectName" value="HorrorAtlas" />

    <div class="actions">
      <button id="deriveBtn" type="button">Derive names</button>
    </div>
  </div>

  <div class="card"

...[TRUNCATED]...

```

## File: `README.md`
```text
# Sheet Builder / Djungo Builder

Build reusable CRUD web applications starting from spreadsheet exports.

The project generates a portable mini application composed of:

- `index.html` — CRUD/admin frontend
- `viewer.html` — read-only data viewer
- `codice.gs` — Google Apps Script backend

The guiding principle is portability:

- generated files remain readable
- the spreadsheet remains owned by the user
- the frontend can be published anywhere
- Apps Script acts as a lightweight backend layer
- the Flask proxy avoids exposing sensitive backend data in the browser

---

# Live instance

https://builder.sgbh.org/generate.html

---

# Current architecture

## Frontend flow

### `docs/generate.html`

Main entry point.

Responsibilities:

- upload spreadsheet source files
- restore/open last generated app
- start parser flow
- open review/configuration phase

---

### `docs/review.html`

Frontend configuration editor.

Responsibilities:

- review detected spreadsheet structure
- edit labels
- configure visible columns
- configure enum colors
- generate final application assets

This page is intentionally separated from the runtime CRUD viewer.

---

### `docs/app_ready.html`

Delivery and backend connection page.

Responsibilities:

- download generated files
- connect Apps Script backend
- register backend inside the secure Flask proxy
- open the final CRUD application

---

## Generated application

### `index.html`

Generated CRUD/admin frontend.

Responsibilities:

- insert
- update
- delete
- load record by ID
- embedded viewer preview

The embedded viewer is intentionally simplified.

Frontend customization is delegated to `review.html`.

---

### `viewer.html`

Read-only data viewer.

Responsibilities:

- render spreadsheet rows
- enum coloring
- table visualization
- filtering/search when used standalone

---

### `codice.gs`

Google Apps Script backend.

Responsibilities:

- spreadsheet CRUD
- JSON responses
- lightweight API layer

---

# Backend/runtime

## `server.py`

Main Flask runtime.

Responsibilities:

- secure Apps Script proxy
- generated file serving
- app registry
- generation API
- session handling

---

## `wsgi.py`

WSGI entry point used by gunicorn.

---

# Pipeline

## `pipeline/build_all_from_input.py`

Rebuilds generated application assets from example spreadsheet input.

Used mainly for local development and regression testing.

---

## `tools/publish_to_docs.py`

Publishes generated runtime assets into the `docs/` folder.

---

# Current UX flow

## First setup flow

```text
generate.html
→ upload spreadsheet files
→ review.html
→ customize labels/colors
→ Generate final app
→ app_ready.html
→ connect backend
→ index.html?app=...

## Existing app flow

```text
generate.html
→ Open last app
→ index.html?app=...
→ Customize labels and colors
→ review.html?returnApp=...
→ Generate final app
→ automatic return to CRUD
```

This allows progressive frontend customization without repeating the deployment flow.

---

# Local development flow

Start from the project root:

```bash
cd ~/Scrivania/sheet-builder
```

Validate Python files:

```bash
python -m py_compile server.py generators/builder_generators.py
```

Rebuild generated assets from the example spreadsheet:

```bash
python pipeline/build_all_from_input.py examples/case_001
```

Publish generated files into `docs/`:

```bash
python tools/publish_to_docs.py
```

Start the local Flask runtime:

```bash
python server.py
```

Open:

```text
http://127.0.0.1:5000/generate.html
```

---

# Production runtime

Current production stack:

- Flask
- gunicorn
- nginx
- systemd
- Hetzner VPS

The public runtime is served from:

```text
https://builder.sgbh.org
```

---

# Deployment philosophy

The project intentionally separates:

```text
configuration flow
```

from:

```text
runtime CRUD flow
```

This keeps the generated CRUD application lightweight while centralizing UI customization inside the review/configuration editor.

---

# Djungo principle

```text
Spreadsheet → Portable App
```

The generated application should remain:

- understandable
- editable
- portable
- self-hostable
- independent from proprietary SaaS lock-in
```

## File: `app/__init__.py`
```text

```

## File: `app/builder_state.py`
```text
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
            "originalHeader": raw.get("originalHeader", name),
            "label": raw.get("originalHeader", name),
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
```

## File: `app/contracts.py`
```text
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
```

## File: `backup_layout_before_cleanup/build_from_config.py`
```text
from __future__ import annotations

import json
from pathlib import Path

from generators.builder_generators import generate_all
from generators.schema_validators import validate_schema_for_product


ROOT = Path(__file__).resolve().parent
OUTPUT_PROJECT_DIR = ROOT / "output_project"

project_config_path = OUTPUT_PROJECT_DIR / "project.config.json"
fields_schema_path = OUTPUT_PROJECT_DIR / "fields.schema.json"


def main() -> None:
    if not project_config_path.exists():
        raise FileNotFoundError(f"Missing file: {project_config_path}")

    if not fields_schema_path.exists():
        raise FileNotFoundError(f"Missing file: {fields_schema_path}")

    project_config = json.loads(project_config_path.read_text(encoding="utf-8"))
    fields_schema = json.loads(fields_schema_path.read_text(encoding="utf-8"))

    errors = validate_schema_for_product(fields_schema)
    if errors:
        joined = "\n- ".join(errors)
        raise ValueError(f"Schema validation failed:\n- {joined}")

    generated = generate_all(project_config, fields_schema)

    for relative_path, content in generated.items():
        target = OUTPUT_PROJECT_DIR / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    deploy_manifest_path = OUTPUT_PROJECT_DIR / "deploy.manifest.json"
    if not deploy_manifest_path.exists():
        deploy_manifest = {
            "projectName": project_config.get("projectName", ""),
            "projectSlug": project_config.get("projectSlug", ""),
            "backendName": project_config.get("backendName", ""),
            "sheetName": project_config.get("sheetName", ""),
            "generatedFiles": list(generated.keys()),
        }
        deploy_manifest_path.write_text(
            json.dumps(deploy_manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    print("Build completed successfully.")
    print(f"Output directory: {OUTPUT_PROJECT_DIR}")


if __name__ == "__main__":
    main()
```

## File: `backup_layout_before_cleanup/docs/index.html`
```text
<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Prova_film</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 1100px; margin: 28px auto; padding: 0 16px; }
    h1 { margin: 0 0 6px; }
    .muted { color:#666; }
    .card { border:1px solid #e5e5e5; border-radius:10px; padding:14px; background:#fafafa; margin:12px 0; }
    label { display:block; margin:10px 0 6px; font-weight:700; }
    input, select { width:100%; padding:9px; border:1px solid #ccc; border-radius:8px; box-sizing:border-box; background:#fff; }
    button { padding:9px 12px; border:0; border-radius:8px; background:#111; color:#fff; cursor:pointer; font-weight:800; }
    button.secondary { background:#666; }
    button:disabled { opacity:.6; cursor:not-allowed; }
    .row { display:grid; grid-template-columns: 1fr 1fr; gap:12px; }
    .actions { display:flex; gap:10px; align-items:center; flex-wrap:wrap; margin-top:12px; }
    .ok { color:#0a6; font-weight:800; }
    .err { color:#b00; font-weight:800; }
    iframe { width:100%; height:560px; border:1px solid #ddd; border-radius:10px; background:#fff; }
    small { display:block; margin-top:8px; color:#666; }
    pre { background:#0b0b0b; color:#d6ffd6; border-radius:10px; padding:12px; overflow:auto; }
  </style>
</head>
<body>

  <h1>Prova_film <span class="muted">— generated</span></h1>
  <p class="muted">
    Backend: Google Apps Script (JSONP) → tab <b>ProvaFilmData</b>.
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
    <h3 style="margin:0 0 10px;">Insert (ProvaFilmItem)</h3>


    <label for="year">year <span class="muted">(optional)</span></label>
    <input id="year" type="number" min="0" placeholder="year" />


    <label for="title">title <span class="muted">(optional)</span></label>
    <input id="title" placeholder="title" />


    <label for="url">url <span class="muted">(optional)</span></label>
    <input id="url" placeholder="url" />


    <label for="nation">nation <span class="muted">(optional)</span></label>
    <input id="nation" placeholder="nation" />


    <label for="rating">rating <span class="muted">(optional)</span></label>
    <select id="rating">
      <option value="" selected>—</option><option>Mediocre</option><option>Medio</option><option>Buono</option><option>Ottimo</option><option>Capolavoro</option><option>Pessimo</option>
    </select>

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
  function setMsg(el, msg, cls) {
    el.className = cls || "muted";
    el.textContent = msg;
  }

  function makeCbName() {
    return "cb_" + Date.now() + "_" + Math.floor(Math.random() * 1e6);
  }

  function jsonp(url) {
    return new Promise((resolve, reject) => {
      const cbName = makeCbName();
      const script = document.createElement("script");

      const t = setTimeout(() => {
        cleanup();
        reject(new Error("Timeout JSONP"));
      }, 15000);

      function cleanup() {
        clearTimeout(t);
        try { delete window[cbName]; } catch (_) { window[cbName] = undefined; }
        script.remove();
      }

      window[cbName] = (data) => {
        cleanup();
        resolve(data);
      };

      const u = new URL(url);
      u.searchParams.set("cb", cbName);
      u.searchParams.set("_", Date.now().toString());

      script.src = u.toString();
      script.onerror = () => {
        cleanup();
        reject(new Error("JSONP load error (check /exec + access)"));
      };

      document.body.appendChild(script);
    });
  }

  function baseUrl_() {
    return document.getElementById("webAppUrl").value.trim();
  }

  function apiKey_() {
    return document.getElementById("apiKey").value.trim();
  }

  function viewerUrl_(cacheBust) {
    const basePath = window.location.pathname.replace(/[^\/]*$/, "");
    const u = new URL(basePath + "viewer.html", window.location.origin);
    u.searchParams.set("webApp", baseUrl_());
    u.se

...[TRUNCATED]...

```

## File: `backup_layout_before_cleanup/docs/viewer.html`
```text
<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>ProvaFilmItem Viewer</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 12px; }
    .muted { color:#666; }
    .toolbar { display:flex; gap:10px; align-items:end; flex-wrap:wrap; margin: 8px 0 12px; }
    .toolbar label { display:block; font-size:12px; font-weight:700; color:#444; margin-bottom:4px; }
    .toolbar input, .toolbar select {
      padding:8px;
      border:1px solid #ccc;
      border-radius:8px;
      background:#fff;
      min-width:180px;
    }

    table { border-collapse: collapse; width: 100%; }
    th, td {
      border:1px solid #e5e5e5;
      padding:8px;
      font-size: 13px;
      vertical-align: top;
      overflow-wrap:anywhere;
      white-space: pre-wrap;
    }

    thead th {
      position: sticky;
      top: 0;
      z-index: 2;
      background: #2f3b52;
      color: #fff;
      font-weight: 800;
    }

    tbody tr:nth-child(even){ background:#f6f8fb; }
    tbody tr:nth-child(odd){ background:#ffffff; }

    tbody tr.first-row {
      background: #fff3cd !important;
      outline: 2px solid #ffe69c;
      outline-offset: -2px;
    }
  </style>
</head>
<body>

  <div class="muted">Viewer read-only — tab <b>ProvaFilmData</b></div>

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

  const VISIBLE_HEADERS = [
  "id",
  "year",
  "title",
  "url",
  "link",
  "nation",
  "rating"
];
  const ENUMS = {
  "rating": [
    "Mediocre",
    "Medio",
    "Buono",
    "Ottimo",
    "Capolavoro",
    "Pessimo"
  ]
};
  const ENUM_STYLES = {
  "rating": {
    "Capolavoro": {
      "bg": "#215a6c",
      "fg": "#c6dbe1"
    },
    "Ottimo": {
      "bg": "#d4edbc",
      "fg": "#11734b"
    },
    "Buono": {
      "bg": "#ffe5a0",
      "fg": "#473821"
    },
    "Medio": {
      "bg": "#ffc8aa",
      "fg": "#753800"
    },
    "Mediocre": {
      "bg": "#ffcfc9",
      "fg": "#b10202"
    },
    "Pessimo": {
      "bg": "#e8eaed",
      "fg": "#000000"
    }
  }
};

  function jsonp(url) {
    return new Promise((resolve, reject) => {
      const cbName = "cb_" + Math.random().toString(36).slice(2);
      const script = document.createElement("script");

      const t = setTimeout(() => {
        cleanup();
        reject(new Error("Timeout JSONP"));
      }, 15000);

      function cleanup() {
        clearTimeout(t);
        try { delete window[cbName]; } catch (_) { window[cbName] = undefined; }
        script.remove();
      }

      window[cbName] = (data) => {
        cleanup();
        resolve(data);
      };

      const u = new URL(url);
      u.searchParams.set("cb", cbName);
      u.searchParams.set("_", Date.now().toString());

      script.src = u.toString();
      script.onerror = () => {
        cleanup();
        reject(new Error("JSONP load error"));
      };

      document.body.appendChild(script);
    });
  }

  function esc(s) {
    return String(s ?? "").replace(/[&<>"']/g, c => (
      {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]
    ));
  }

  let LAST_HEADERS = [];
  let LAST_ROWS = [];

  function renderTable() {
    const status = document.getElementById("status");
    const tbl = document.getElementById("tbl");
    const search = document.getElementById("searchBox").value.trim().toLowerCase();

    if (!LAST_HEADERS.length) {
      tbl.innerHTML = "";
      status.textContent = "Nessun dato";
      return;
    }

    const visibleIndexes = LAST_HEADERS
      .map((h, i) => (VISIBLE_HEADERS.includes(h) ? i : -1))
      .filter(i => i >= 0);

    let rows = LAST_ROWS.slice();

    if (search) {
      rows = rows.filter(r =>
        visibleIndexes.some(i => String(r[i] ?? "").toLowerCase().includes(search))
      );
    }

    let html = "<table><thead><tr>";
    for (const i of visibleIndexes) {
      html += `<th>${esc(LAST_HEADERS[i])}</th>`;
    }
    html += "</tr></thead><tbody>";

    for (let rI = 0; rI < rows.length; rI++) {
      const r = rows[rI];
      const trClass = (rI === 0) ? "first-row" : "";
      html += `<tr class="${trClass}">`;

      for (const i of visibleIndexes) {
        const header = LAST_HEADERS[i];
        const cellVal = r[i];

        let style = "";
        const stylesForField = ENUM_STYLES[header] || {};
        const styleDef = stylesForField[String(cellVal ?? "").trim()] || null;

        if (styleDef) {
          const bg = styleDef.bg ? `background:${styleDef.bg};` : "";
          const fg = styleDef.fg ? `color:${styleDef.fg};` : "";
          style = `${bg}${fg}font-weight:700;text-align:center;`;
        }

        html += `<td style="${style}">${esc(cellVal)}</td>`;
      }

      html += "</tr>";
    }

    html += "</tbody></table>";
    tbl.innerHTML = html;
    status.textContent = `OK | headers=${LAST_HEADERS.length} | rows=${rows.length}`;
  }

  async function load() {
    const status = document.getElementById("status");

    if (!WEB_APP_URL) {
      status.textContent = "Errore: manca parametro 'webApp' nell'URL.";
      return;
    }

    try {
      const limit = document.getElementById("limitBox").value || URL_LIMIT;
      const u = new URL(WEB_APP_URL);
      u.searchParams.set("mode", "view");
      u.searchParams.set("limit", limit);

      const resp = await jsonp(u.toString());
      if (!resp || resp.ok !

...[TRUNCATED]...

```

## File: `backup_layout_before_cleanup/generators/__init__.py`
```text

```

## File: `backup_layout_before_cleanup/generators/builder_generators.py`
```text
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
            max_le

...[TRUNCATED]...

```

## File: `backup_layout_before_cleanup/generators/import_from_html.py`
```text
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup


def _extract_css_property(style: str, prop: str) -> Optional[str]:
    parts = [p.strip() for p in style.split(";") if p.strip()]
    for part in parts:
        if ":" not in part:
            continue
        key, value = part.split(":", 1)
        if key.strip().lower() == prop.strip().lower():
            return value.strip()
    return None


def _cell_text(td) -> str:
    return td.get_text(separator=" ", strip=True)


def _find_main_table(soup: BeautifulSoup):
    return soup.find("table", class_="waffle") or soup.find("table")


def _extract_headers_and_rows(table) -> tuple[list[str], list[list[str]], list]:
    body = table.find("tbody")
    if body is None:
        return [], [], []

    trs = body.find_all("tr")
    if not trs:
        return [], [], []

    first_row_tds = trs[0].find_all("td")
    headers = [_cell_text(td) for td in first_row_tds]

    data_rows: List[List[str]] = []
    raw_rows = []

    for tr in trs[1:]:
        tds = tr.find_all("td")
        values = [_cell_text(td) for td in tds]
        data_rows.append(values)
        raw_rows.append(tds)

    return headers, data_rows, raw_rows


def _extract_enum_styles_for_column(
    raw_rows: List,
    headers: List[str],
    enum_field_name: str,
) -> Dict[str, Dict[str, str]]:
    result: Dict[str, Dict[str, str]] = {}

    if enum_field_name not in headers:
        return result

    idx = headers.index(enum_field_name)

    for row_tds in raw_rows:
        if len(row_tds) <= idx:
            continue

        td = row_tds[idx]
        span = td.find("span")
        if span is None:
            continue

        value = span.get_text(strip=True)
        value = value.replace("\u200b", "").strip()

        if not value:
            continue

        style = span.get("style", "")
        bg = _extract_css_property(style, "background-color")
        fg = _extract_css_property(style, "color")

        if bg or fg:
            result[value] = {
                "bg": bg or "",
                "fg": fg or "",
            }

    return result


def _extract_side_column_enum_candidates(
    headers: List[str],
    data_rows: List[List[str]],
) -> List[str]:
    """
    Heuristica semplice:
    cerca una colonna oltre gli header principali con pochi valori testuali unici.
    """
    if not data_rows:
        return []

    max_cols = max(len(r) for r in data_rows)
    header_len = len(headers)

    for col_idx in range(header_len, max_cols):
        seen: List[str] = []

        for row in data_rows:
            if len(row) <= col_idx:
                continue

            v = row[col_idx].strip()
            if not v:
                continue

            if v not in seen:
                seen.append(v)

        if 2 <= len(seen) <= 20:
            return seen

    return []


def import_visuals_from_html(
    html_path: str | Path,
    enum_field_name: str = "rating",
    debug: bool = False,
) -> Dict[str, Any]:
    html_path = Path(html_path)
    html_text = html_path.read_text(encoding="utf-8", errors="ignore")

    soup = BeautifulSoup(html_text, "html.parser")
    table = _find_main_table(soup)
    if table is None:
        raise ValueError("No HTML table found")

    headers, data_rows, raw_rows = _extract_headers_and_rows(table)
    if not headers:
        raise ValueError("No headers found in HTML table")

    enum_styles = _extract_enum_styles_for_column(raw_rows, headers, enum_field_name)
    enum_values_from_html = _extract_side_column_enum_candidates(headers, data_rows)

    if debug:
        print("HTML headers:", headers)
        print("HTML enum styles:", enum_styles)
        print("HTML enum values from side column:", enum_values_from_html)

    return {
        "headers": headers,
        "enumStyles": {
            enum_field_name: enum_styles
        } if enum_styles else {},
        "enumValuesFromHtml": {
            enum_field_name: enum_values_from_html
        } if enum_values_from_html else {},
    }
```

## File: `backup_layout_before_cleanup/generators/import_from_sheet.py`
```text
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation


def _norm_header(value: Any) -> str:
    return str(value or "").strip().lower()


def _guess_type_from_sample(value: Any) -> str:
    if value is None or value == "":
        return "string"

    if isinstance(value, bool):
        return "string"

    if isinstance(value, int):
        return "int"

    if isinstance(value, float):
        if value.is_integer():
            return "int"
        return "string"

    cls_name = value.__class__.__name__.lower()
    if "date" in cls_name or "datetime" in cls_name:
        return "date"

    s = str(value).strip()
    s_lower = s.lower()

    if s_lower.startswith("http://") or s_lower.startswith("https://") or s_lower.startswith("www."):
        return "string"

    if s.isdigit():
        return "int"

    slash_parts = s.split("/")
    dash_parts = s.split("-")

    if len(slash_parts) == 3 and all(part.strip().isdigit() for part in slash_parts):
        return "date"

    if len(dash_parts) == 3 and all(part.strip().isdigit() for part in dash_parts):
        return "date"

    return "string"


def _cell_in_same_data_column(cell_range: str, col_letter: str) -> bool:
    try:
        parts = cell_range.split(":")
        start = parts[0]
        end = parts[-1]

        start_letters = "".join(ch for ch in start if ch.isalpha()).upper()
        end_letters = "".join(ch for ch in end if ch.isalpha()).upper()

        if not start_letters:
            return False
        if not end_letters:
            end_letters = start_letters

        return start_letters <= col_letter <= end_letters
    except Exception:
        return False


def _read_values_from_range_ref(workbook, ref: str, debug: bool = False) -> List[str]:
    if debug:
        print("READ RANGE REF =", ref)

    if "!" in ref:
        sheet_name, range_ref = ref.split("!", 1)
        sheet_name = sheet_name.strip("'")
        ws = workbook[sheet_name]
    else:
        ws = workbook.active
        range_ref = ref

    values: List[str] = []
    for row in ws[range_ref]:
        for cell in row:
            if cell.value is not None and str(cell.value).strip():
                values.append(str(cell.value).strip())
    return values


def _extract_enum_from_validation(
    workbook,
    ws,
    col_idx: int,
    sample_row: int,
    debug: bool = False,
) -> List[str]:
    col_letter = get_column_letter(col_idx)
    target_coord = f"{col_letter}{sample_row}"

    if debug:
        print(f"\n--- DEBUG ENUM COLONNA {col_letter} ({target_coord}) ---")
        print(f"Tot dataValidations: {len(ws.data_validations.dataValidation)}")

    for dv in ws.data_validations.dataValidation:
        if not isinstance(dv, DataValidation):
            continue

        if debug:
            print("type =", dv.type, "| formula1 =", dv.formula1, "| sqref =", dv.sqref)

        if dv.type != "list":
            continue

        applies = False

        for rng in str(dv.sqref).split():
            if _cell_in_same_data_column(rng, col_letter):
                applies = True
                break

        if not applies:
            try:
                if target_coord in dv.cells:
                    applies = True
            except Exception:
                pass

        if not applies:
            continue

        formula1 = dv.formula1
        if not formula1:
            continue

        formula1 = str(formula1).strip()

        if debug:
            print("MATCH validation list on column", col_letter)
            print("formula1 raw =", formula1)

        if formula1.startswith('"') and formula1.endswith('"'):
            raw = formula1[1:-1]
            values = [x.strip() for x in raw.split(",") if x.strip()]
            if debug:
                print("enum explicit =", values)
            return values

        ref = formula1[1:] if formula1.startswith("=") else formula1

        if "!" in ref or "$" in ref or ":" in ref:
            try:
                values = _read_values_from_range_ref(workbook, ref, debug=debug)
                if debug:
                    print("enum from range =", values)
                return values
            except Exception as exc:
                if debug:
                    print("range parse failed:", exc)
                return []

    if debug:
        print("No enum validation found for column", col_letter)

    return []


def _is_formula_cell(cell) -> bool:
    return isinstance(cell.value, str) and cell.value.startswith("=")


def _build_field_def(
    name: str,
    sample_value: Any,
    has_formula: bool,
    formula_source: str | None,
    formula_anchor_row: int | None,
    enum_values: List[str],
) -> Dict[str, Any]:
    base = {
        "name": name,
        "required": False,
        "visibleInViewer": True,
        "enumValues": enum_values or [],
        "locked": False,
        "formulaSource": None,
        "formulaAnchorRow": None,
        "formulaMode": None,
        "enumStyles": {},
    }

    if name == "id":
        return {
            **base,
            "type": "int",
            "computed": True,
            "visibleInForm": False,
            "locked": True,
        }

    if has_formula:
        return {
            **base,
            "type": "computed",
            "computed": True,
            "visibleInForm": False,
            "locked": True,
            "formulaSource": formula_source,
            "formulaAnchorRow": formula_anchor_row,
            "formulaMode": "incremental_copy",
        }

    field_type = "enum" if enum_values else _guess_type_from_sample(sample_value)

    return {
        **base,
        "type": field_type,
        "computed": False,
        "visibleInForm": True,
    }


def _build_constraint(field: Dict[str, Any]) -> Dict[str, An

...[TRUNCATED]...

```

## File: `backup_layout_before_cleanup/generators/merge_schema.py`
```text
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List


def _merge_unique(*lists: List[str]) -> List[str]:
    out: List[str] = []
    for seq in lists:
        for v in seq:
            if v and v not in out:
                out.append(v)
    return out


def merge_schema_with_visuals(
    sheet_schema: Dict[str, Any],
    html_visuals: Dict[str, Any],
) -> Dict[str, Any]:
    merged = deepcopy(sheet_schema)

    merged.setdefault("enums", {})
    merged.setdefault("enumStyles", {})

    html_enums = html_visuals.get("enumValuesFromHtml", {})
    html_styles = html_visuals.get("enumStyles", {})

    field_names = set(list(html_enums.keys()) + list(html_styles.keys()))

    for field_name in field_names:
        xlsx_values = list(merged.get("enums", {}).get(field_name, []))
        html_values = list(html_enums.get(field_name, []))
        style_values = list(html_styles.get(field_name, {}).keys())

        final_values = _merge_unique(xlsx_values, html_values, style_values)

        if final_values:
            merged["enums"][field_name] = final_values

            for f in merged.get("fields", []):
                if f.get("name") == field_name:
                    f["type"] = "enum"
                    f["enumValues"] = final_values

            if field_name in merged.get("constraints", {}):
                merged["constraints"][field_name]["type"] = "enum"

        styles_for_field = html_styles.get(field_name, {})
        if styles_for_field:
            merged["enumStyles"][field_name] = styles_for_field

        for f in merged.get("fields", []):
            if f.get("name") == field_name:
                f.setdefault("enumStyles", {})
                if styles_for_field:
                    f["enumStyles"] = styles_for_field

    for f in merged.get("fields", []):
        f.setdefault("enumStyles", {})
        f.setdefault("formulaSource", None)
        f.setdefault("formulaAnchorRow", None)
        f.setdefault("formulaMode", None)

    return merged
```

## File: `backup_layout_before_cleanup/generators/schema_validators.py`
```text
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
    enum_styles_top = fields_schema.get("enumStyles", {})

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

    if not isinstance(enum_styles_top, dict):
        errors.append("'enumStyles' must be an object/dict.")

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

    field_names: List[str] = []
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
            errors.append(f"Field '{name}' has invalid 'enumStyles' (must be dict or null).")
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
            errors.append(f"Field '{fname}' is defined but missing from headers."

...[TRUNCATED]...

```

## File: `backup_layout_before_cleanup/output_gas/deploy.manifest.json`
```text
{
  "projectSlug": "prova-film",
  "projectName": "Prova_film",
  "frontend": {
    "provider": "github-pages",
    "repoNameSuggested": "prova-film",
    "branch": "main",
    "publishDir": "docs",
    "entryFile": "docs/index.html",
    "viewerFile": "docs/viewer.html"
  },
  "backend": {
    "provider": "google-apps-script",
    "entryFile": "codice.gs",
    "sheetName": "ProvaFilmData",
    "backendName": "prova-film-backend"
  },
  "files": [
    "codice.gs",
    "docs/index.html",
    "docs/viewer.html",
    "project.config.json",
    "fields.schema.json",
    "deploy.manifest.json"
  ],
  "schemaSummary": {
    "headers": [
      "id",
      "Titolo",
      "Data Produzione"
    ],
    "computed": [
      "id"
    ],
    "visibleInForm": [
      "Data Produzione"
    ],
    "visibleInViewer": [
      "id",
      "Titolo",
      "Data Produzione"
    ]
  }
}
```

## File: `backup_layout_before_cleanup/output_gas/fields.schema.json`
```text
{
  "headers": [
    "id",
    "Titolo",
    "Data Produzione"
  ],
  "requiredOnInsert": [],
  "optionalOnInsert": [
    "Titolo",
    "Data Produzione"
  ],
  "computed": [
    "id"
  ],
  "visibleInForm": [
    "Data Produzione"
  ],
  "visibleInViewer": [
    "id",
    "Titolo",
    "Data Produzione"
  ],
  "enums": {},
  "constraints": {
    "id": {
      "type": "int",
      "required": false,
      "min": 0
    },
    "Titolo": {
      "type": "string",
      "required": false,
      "maxLen": 255
    },
    "Data Produzione": {
      "type": "date",
      "required": false,
      "format": "dd/mm/yyyy"
    }
  },
  "fields": [
    {
      "name": "id",
      "type": "int",
      "required": false,
      "computed": true,
      "visibleInForm": false,
      "visibleInViewer": true,
      "enumValues": [],
      "locked": true
    },
    {
      "name": "Titolo",
      "type": "string",
      "required": false,
      "computed": false,
      "visibleInForm": false,
      "visibleInViewer": true,
      "enumValues": [],
      "locked": false
    },
    {
      "name": "Data Produzione",
      "type": "date",
      "required": false,
      "computed": false,
      "visibleInForm": true,
      "visibleInViewer": true,
      "enumValues": [],
      "locked": false
    }
  ]
}
```

## File: `backup_layout_before_cleanup/output_gas/google_setup.md`
```text
# Google Apps Script setup guide

## Project summary
- Project name: Prova_film
- Project slug: prova-film
- Backend logical name: prova-film-backend
- Sheet name: ProvaFilmData

## Files prepared
- codice.gs
- fields.schema.json
- project.config.json
- deploy.manifest.json
- sample_rows.json
- sample_rows.csv

## Suggested Google flow

### 1. Create the Google Sheet
Create a new Google Sheet and rename the main tab exactly as:

    ProvaFilmData

### 2. Create the header row
Insert these headers in row 1, from column A onward:

    id, Titolo, Data Produzione

### 3. Insert example rows
You have two prepared files:

- sample_rows.json
- sample_rows.csv

Suggested use:
- use `sample_rows.csv` if you want a quick import structure
- use `sample_rows.json` if you want to inspect the data clearly first

### 4. Create a new Apps Script project
Suggested project name:

    Prova_film Backend

### 5. Replace script content
Open:

    codice.gs

Copy everything into the Apps Script editor.

### 6. Deploy as Web App
Use the Apps Script deploy flow:

- Deploy → New deployment
- Type: Web app
- Execute as: Me
- Access: Anyone

Then copy the /exec URL.

### 7. Connect frontend
Paste the /exec URL into your frontend configuration.

## Notes
- No clasp required
- No Google API required
- Fully manual but controlled setup

```

## File: `backup_layout_before_cleanup/output_gas/project.config.json`
```text
{
  "projectName": "Prova_film",
  "projectSlug": "prova-film",
  "backendName": "prova-film-backend",
  "entityName": "ProvaFilmItem",
  "entityLabelLower": "item",
  "sheetName": "ProvaFilmData",
  "outputDirectory": "build/prova-film",
  "buildMarker": "PROVA_FILM_BACKEND_V1",
  "adminPassword": "UVZi4cpCddok7swLSf",
  "generatedAt": "2026-03-22T18:43:14.667Z"
}
```

## File: `backup_layout_before_cleanup/output_gas/sample_rows.json`
```text
[
  {
    "id": 1,
    "Titolo": "Nosferatu",
    "Data Produzione": "04/03/1922"
  },
  {
    "id": 2,
    "Titolo": "Psycho",
    "Data Produzione": "16/06/1960"
  }
]
```

## File: `backup_layout_before_cleanup/output_project/deploy.manifest.json`
```text
{
  "projectSlug": "prova-film",
  "projectName": "Prova_film",
  "frontend": {
    "provider": "github-pages",
    "repoNameSuggested": "prova-film",
    "branch": "main",
    "publishDir": "docs",
    "entryFile": "docs/index.html",
    "viewerFile": "docs/viewer.html"
  },
  "backend": {
    "provider": "google-apps-script",
    "entryFile": "codice.gs",
    "sheetName": "ProvaFilmData",
    "backendName": "prova-film-backend"
  },
  "files": [
    "codice.gs",
    "docs/index.html",
    "docs/viewer.html",
    "project.config.json",
    "fields.schema.json",
    "deploy.manifest.json"
  ],
  "schemaSummary": {
    "headers": [
      "id",
      "Titolo",
      "Data Produzione"
    ],
    "computed": [
      "id"
    ],
    "visibleInForm": [
      "Data Produzione"
    ],
    "visibleInViewer": [
      "id",
      "Titolo",
      "Data Produzione"
    ]
  }
}
```

## File: `backup_layout_before_cleanup/output_project/docs/index.html`
```text
<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Prova_film</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 1100px; margin: 28px auto; padding: 0 16px; }
    h1 { margin: 0 0 6px; }
    .muted { color:#666; }
    .card { border:1px solid #e5e5e5; border-radius:10px; padding:14px; background:#fafafa; margin:12px 0; }
    label { display:block; margin:10px 0 6px; font-weight:700; }
    input, select { width:100%; padding:9px; border:1px solid #ccc; border-radius:8px; box-sizing:border-box; background:#fff; }
    button { padding:9px 12px; border:0; border-radius:8px; background:#111; color:#fff; cursor:pointer; font-weight:800; }
    button.secondary { background:#666; }
    button:disabled { opacity:.6; cursor:not-allowed; }
    .row { display:grid; grid-template-columns: 1fr 1fr; gap:12px; }
    .actions { display:flex; gap:10px; align-items:center; flex-wrap:wrap; margin-top:12px; }
    .ok { color:#0a6; font-weight:800; }
    .err { color:#b00; font-weight:800; }
    iframe { width:100%; height:560px; border:1px solid #ddd; border-radius:10px; background:#fff; }
    small { display:block; margin-top:8px; color:#666; }
    pre { background:#0b0b0b; color:#d6ffd6; border-radius:10px; padding:12px; overflow:auto; }
  </style>
</head>
<body>

  <h1>Prova_film <span class="muted">— generated</span></h1>
  <p class="muted">
    Backend: Google Apps Script (JSONP) → tab <b>ProvaFilmData</b>.
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
    <h3 style="margin:0 0 10px;">Insert (ProvaFilmItem)</h3>


    <label for="year">year <span class="muted">(optional)</span></label>
    <input id="year" type="number" min="0" placeholder="year" />


    <label for="title">title <span class="muted">(optional)</span></label>
    <input id="title" placeholder="title" />


    <label for="url">url <span class="muted">(optional)</span></label>
    <input id="url" placeholder="url" />


    <label for="nation">nation <span class="muted">(optional)</span></label>
    <input id="nation" placeholder="nation" />


    <label for="rating">rating <span class="muted">(optional)</span></label>
    <select id="rating">
      <option value="" selected>—</option><option>Mediocre</option><option>Medio</option><option>Buono</option><option>Ottimo</option><option>Capolavoro</option><option>Pessimo</option>
    </select>

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
  function setMsg(el, msg, cls) {
    el.className = cls || "muted";
    el.textContent = msg;
  }

  function makeCbName() {
    return "cb_" + Date.now() + "_" + Math.floor(Math.random() * 1e6);
  }

  function jsonp(url) {
    return new Promise((resolve, reject) => {
      const cbName = makeCbName();
      const script = document.createElement("script");

      const t = setTimeout(() => {
        cleanup();
        reject(new Error("Timeout JSONP"));
      }, 15000);

      function cleanup() {
        clearTimeout(t);
        try { delete window[cbName]; } catch (_) { window[cbName] = undefined; }
        script.remove();
      }

      window[cbName] = (data) => {
        cleanup();
        resolve(data);
      };

      const u = new URL(url);
      u.searchParams.set("cb", cbName);
      u.searchParams.set("_", Date.now().toString());

      script.src = u.toString();
      script.onerror = () => {
        cleanup();
        reject(new Error("JSONP load error (check /exec + access)"));
      };

      document.body.appendChild(script);
    });
  }

  function baseUrl_() {
    return document.getElementById("webAppUrl").value.trim();
  }

  function apiKey_() {
    return document.getElementById("apiKey").value.trim();
  }

  function viewerUrl_(cacheBust) {
    const basePath = window.location.pathname.replace(/[^\/]*$/, "");
    const u = new URL(basePath + "viewer.html", window.location.origin);
    u.searchParams.set("webApp", baseUrl_());
    u.se

...[TRUNCATED]...

```

## File: `backup_layout_before_cleanup/output_project/docs/viewer.html`
```text
<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>ProvaFilmItem Viewer</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 12px; }
    .muted { color:#666; }
    .toolbar { display:flex; gap:10px; align-items:end; flex-wrap:wrap; margin: 8px 0 12px; }
    .toolbar label { display:block; font-size:12px; font-weight:700; color:#444; margin-bottom:4px; }
    .toolbar input, .toolbar select {
      padding:8px;
      border:1px solid #ccc;
      border-radius:8px;
      background:#fff;
      min-width:180px;
    }

    table { border-collapse: collapse; width: 100%; }
    th, td {
      border:1px solid #e5e5e5;
      padding:8px;
      font-size: 13px;
      vertical-align: top;
      overflow-wrap:anywhere;
      white-space: pre-wrap;
    }

    thead th {
      position: sticky;
      top: 0;
      z-index: 2;
      background: #2f3b52;
      color: #fff;
      font-weight: 800;
    }

    tbody tr:nth-child(even){ background:#f6f8fb; }
    tbody tr:nth-child(odd){ background:#ffffff; }

    tbody tr.first-row {
      background: #fff3cd !important;
      outline: 2px solid #ffe69c;
      outline-offset: -2px;
    }
  </style>
</head>
<body>

  <div class="muted">Viewer read-only — tab <b>ProvaFilmData</b></div>

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

  const VISIBLE_HEADERS = [
  "id",
  "year",
  "title",
  "url",
  "link",
  "nation",
  "rating"
];
  const ENUMS = {
  "rating": [
    "Mediocre",
    "Medio",
    "Buono",
    "Ottimo",
    "Capolavoro",
    "Pessimo"
  ]
};
  const ENUM_STYLES = {
  "rating": {
    "Capolavoro": {
      "bg": "#215a6c",
      "fg": "#c6dbe1"
    },
    "Ottimo": {
      "bg": "#d4edbc",
      "fg": "#11734b"
    },
    "Buono": {
      "bg": "#ffe5a0",
      "fg": "#473821"
    },
    "Medio": {
      "bg": "#ffc8aa",
      "fg": "#753800"
    },
    "Mediocre": {
      "bg": "#ffcfc9",
      "fg": "#b10202"
    },
    "Pessimo": {
      "bg": "#e8eaed",
      "fg": "#000000"
    }
  }
};

  function jsonp(url) {
    return new Promise((resolve, reject) => {
      const cbName = "cb_" + Math.random().toString(36).slice(2);
      const script = document.createElement("script");

      const t = setTimeout(() => {
        cleanup();
        reject(new Error("Timeout JSONP"));
      }, 15000);

      function cleanup() {
        clearTimeout(t);
        try { delete window[cbName]; } catch (_) { window[cbName] = undefined; }
        script.remove();
      }

      window[cbName] = (data) => {
        cleanup();
        resolve(data);
      };

      const u = new URL(url);
      u.searchParams.set("cb", cbName);
      u.searchParams.set("_", Date.now().toString());

      script.src = u.toString();
      script.onerror = () => {
        cleanup();
        reject(new Error("JSONP load error"));
      };

      document.body.appendChild(script);
    });
  }

  function esc(s) {
    return String(s ?? "").replace(/[&<>"']/g, c => (
      {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]
    ));
  }

  let LAST_HEADERS = [];
  let LAST_ROWS = [];

  function renderTable() {
    const status = document.getElementById("status");
    const tbl = document.getElementById("tbl");
    const search = document.getElementById("searchBox").value.trim().toLowerCase();

    if (!LAST_HEADERS.length) {
      tbl.innerHTML = "";
      status.textContent = "Nessun dato";
      return;
    }

    const visibleIndexes = LAST_HEADERS
      .map((h, i) => (VISIBLE_HEADERS.includes(h) ? i : -1))
      .filter(i => i >= 0);

    let rows = LAST_ROWS.slice();

    if (search) {
      rows = rows.filter(r =>
        visibleIndexes.some(i => String(r[i] ?? "").toLowerCase().includes(search))
      );
    }

    let html = "<table><thead><tr>";
    for (const i of visibleIndexes) {
      html += `<th>${esc(LAST_HEADERS[i])}</th>`;
    }
    html += "</tr></thead><tbody>";

    for (let rI = 0; rI < rows.length; rI++) {
      const r = rows[rI];
      const trClass = (rI === 0) ? "first-row" : "";
      html += `<tr class="${trClass}">`;

      for (const i of visibleIndexes) {
        const header = LAST_HEADERS[i];
        const cellVal = r[i];

        let style = "";
        const stylesForField = ENUM_STYLES[header] || {};
        const styleDef = stylesForField[String(cellVal ?? "").trim()] || null;

        if (styleDef) {
          const bg = styleDef.bg ? `background:${styleDef.bg};` : "";
          const fg = styleDef.fg ? `color:${styleDef.fg};` : "";
          style = `${bg}${fg}font-weight:700;text-align:center;`;
        }

        html += `<td style="${style}">${esc(cellVal)}</td>`;
      }

      html += "</tr>";
    }

    html += "</tbody></table>";
    tbl.innerHTML = html;
    status.textContent = `OK | headers=${LAST_HEADERS.length} | rows=${rows.length}`;
  }

  async function load() {
    const status = document.getElementById("status");

    if (!WEB_APP_URL) {
      status.textContent = "Errore: manca parametro 'webApp' nell'URL.";
      return;
    }

    try {
      const limit = document.getElementById("limitBox").value || URL_LIMIT;
      const u = new URL(WEB_APP_URL);
      u.searchParams.set("mode", "view");
      u.searchParams.set("limit", limit);

      const resp = await jsonp(u.toString());
      if (!resp || resp.ok !

...[TRUNCATED]...

```

## File: `backup_layout_before_cleanup/output_project/fields.schema.json`
```text
{
  "headers": [
    "id",
    "year",
    "title",
    "url",
    "link",
    "nation",
    "rating"
  ],
  "requiredOnInsert": [],
  "optionalOnInsert": [
    "year",
    "title",
    "url",
    "nation",
    "rating"
  ],
  "computed": [
    "id",
    "link"
  ],
  "visibleInForm": [
    "year",
    "title",
    "url",
    "nation",
    "rating"
  ],
  "visibleInViewer": [
    "id",
    "year",
    "title",
    "url",
    "link",
    "nation",
    "rating"
  ],
  "enums": {
    "rating": [
      "Mediocre",
      "Medio",
      "Buono",
      "Ottimo",
      "Capolavoro",
      "Pessimo"
    ]
  },
  "constraints": {
    "id": {
      "type": "int",
      "required": false,
      "min": 0
    },
    "year": {
      "type": "int",
      "required": false,
      "min": 0
    },
    "title": {
      "type": "string",
      "required": false,
      "maxLen": 255
    },
    "url": {
      "type": "string",
      "required": false,
      "maxLen": 255
    },
    "link": {
      "type": "computed",
      "required": false
    },
    "nation": {
      "type": "string",
      "required": false,
      "maxLen": 255
    },
    "rating": {
      "type": "enum",
      "required": false
    }
  },
  "fields": [
    {
      "name": "id",
      "required": false,
      "visibleInViewer": true,
      "enumValues": [],
      "locked": true,
      "formulaSource": null,
      "formulaAnchorRow": null,
      "formulaMode": null,
      "enumStyles": {},
      "type": "int",
      "computed": true,
      "visibleInForm": false
    },
    {
      "name": "year",
      "required": false,
      "visibleInViewer": true,
      "enumValues": [],
      "locked": false,
      "formulaSource": null,
      "formulaAnchorRow": null,
      "formulaMode": null,
      "enumStyles": {},
      "type": "int",
      "computed": false,
      "visibleInForm": true
    },
    {
      "name": "title",
      "required": false,
      "visibleInViewer": true,
      "enumValues": [],
      "locked": false,
      "formulaSource": null,
      "formulaAnchorRow": null,
      "formulaMode": null,
      "enumStyles": {},
      "type": "string",
      "computed": false,
      "visibleInForm": true
    },
    {
      "name": "url",
      "required": false,
      "visibleInViewer": true,
      "enumValues": [],
      "locked": false,
      "formulaSource": null,
      "formulaAnchorRow": null,
      "formulaMode": null,
      "enumStyles": {},
      "type": "string",
      "computed": false,
      "visibleInForm": true
    },
    {
      "name": "link",
      "required": false,
      "visibleInViewer": true,
      "enumValues": [],
      "locked": true,
      "formulaSource": "=HYPERLINK(D2:D987, C2:C987)",
      "formulaAnchorRow": 2,
      "formulaMode": "incremental_copy",
      "enumStyles": {},
      "type": "computed",
      "computed": true,
      "visibleInForm": false
    },
    {
      "name": "nation",
      "required": false,
      "visibleInViewer": true,
      "enumValues": [],
      "locked": false,
      "formulaSource": null,
      "formulaAnchorRow": null,
      "formulaMode": null,
      "enumStyles": {},
      "type": "string",
      "computed": false,
      "visibleInForm": true
    },
    {
      "name": "rating",
      "required": false,
      "visibleInViewer": true,
      "enumValues": [
        "Mediocre",
        "Medio",
        "Buono",
        "Ottimo",
        "Capolavoro",
        "Pessimo"
      ],
      "locked": false,
      "formulaSource": null,
      "formulaAnchorRow": null,
      "formulaMode": null,
      "enumStyles": {
        "Capolavoro": {
          "bg": "#215a6c",
          "fg": "#c6dbe1"
        },
        "Ottimo": {
          "bg": "#d4edbc",
          "fg": "#11734b"
        },
        "Buono": {
          "bg": "#ffe5a0",
          "fg": "#473821"
        },
        "Medio": {
          "bg": "#ffc8aa",
          "fg": "#753800"
        },
        "Mediocre": {
          "bg": "#ffcfc9",
          "fg": "#b10202"
        },
        "Pessimo": {
          "bg": "#e8eaed",
          "fg": "#000000"
        }
      },
      "type": "enum",
      "computed": false,
      "visibleInForm": true
    }
  ],
  "enumStyles": {
    "rating": {
      "Capolavoro": {
        "bg": "#215a6c",
        "fg": "#c6dbe1"
      },
      "Ottimo": {
        "bg": "#d4edbc",
        "fg": "#11734b"
      },
      "Buono": {
        "bg": "#ffe5a0",
        "fg": "#473821"
      },
      "Medio": {
        "bg": "#ffc8aa",
        "fg": "#753800"
      },
      "Mediocre": {
        "bg": "#ffcfc9",
        "fg": "#b10202"
      },
      "Pessimo": {
        "bg": "#e8eaed",
        "fg": "#000000"
      }
    }
  }
}
```

## File: `backup_layout_before_cleanup/output_project/project.config.json`
```text
{
  "projectName": "Prova_film",
  "projectSlug": "prova-film",
  "backendName": "prova-film-backend",
  "entityName": "ProvaFilmItem",
  "entityLabelLower": "item",
  "sheetName": "ProvaFilmData",
  "outputDirectory": "build/prova-film",
  "buildMarker": "PROVA_FILM_BACKEND_V1",
  "adminPassword": "UVZi4cpCddok7swLSf",
  "generatedAt": "2026-03-22T18:43:14.667Z"
}
```

## File: `backup_layout_before_cleanup/pipeline/__init__.py`
```text

```

## File: `backup_layout_before_cleanup/pipeline/build_all_from_input.py`
```text
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OUTPUT_PROJECT_DIR = ROOT / "output_project"
EXAMPLES_DIR = ROOT / "examples"
PROJECT_CONFIG_PATH = OUTPUT_PROJECT_DIR / "project.config.json"
FIELDS_SCHEMA_PATH = OUTPUT_PROJECT_DIR / "fields.schema.json"


def ensure_default_project_config() -> dict:
    """
    Se project.config.json non esiste in output_project, ne crea uno minimale.
    Se esiste già, lo lascia invariato.
    """
    OUTPUT_PROJECT_DIR.mkdir(parents=True, exist_ok=True)

    if PROJECT_CONFIG_PATH.exists():
        return json.loads(PROJECT_CONFIG_PATH.read_text(encoding="utf-8"))

    config = {
        "projectName": "Imported Sheet Project",
        "projectSlug": "imported-sheet-project",
        "backendName": "imported-sheet-backend",
        "entityName": "ImportedItem",
        "entityLabelLower": "item",
        "sheetName": "Sheet1",
        "outputDirectory": str(OUTPUT_PROJECT_DIR),
        "buildMarker": "IMPORTED_SHEET_BACKEND_V1",
        "adminPassword": "CHANGE_ME_WRITE_KEY_2026",
    }

    PROJECT_CONFIG_PATH.write_text(
        json.dumps(config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return config


def run_step(cmd: list[str], title: str) -> None:
    print(f"\n=== {title} ===")
    print(" ".join(cmd))
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        raise SystemExit(f"Step failed: {title}")


def find_single_input_dir() -> Path:
    candidate_dirs = [p for p in EXAMPLES_DIR.iterdir() if p.is_dir()]
    if not candidate_dirs:
        raise SystemExit(f"No subdirectories found inside examples/: {EXAMPLES_DIR}")
    if len(candidate_dirs) > 1:
        raise SystemExit(
            "More than one subdirectory found inside examples/. "
            "Pass the desired input directory explicitly."
        )
    return candidate_dirs[0]


def main() -> None:
    if len(sys.argv) == 1:
        input_dir = find_single_input_dir()
    else:
        input_dir = Path(sys.argv[1])

    ensure_default_project_config()

    run_step(
        [
            sys.executable,
            str(ROOT / "pipeline" / "build_schema_from_input.py"),
            str(input_dir),
        ],
        "STEP 1 - Build fields.schema.json from input basket",
    )

    if not FIELDS_SCHEMA_PATH.exists():
        raise SystemExit(f"Missing generated schema: {FIELDS_SCHEMA_PATH}")

    run_step(
        [
            sys.executable,
            str(ROOT / "build_from_config.py"),
        ],
        "STEP 2 - Generate codice.gs + index.html + viewer.html",
    )

    print("\nBuild completed successfully.")
    print(f"Schema:   {FIELDS_SCHEMA_PATH}")
    print(f"Config:   {PROJECT_CONFIG_PATH}")
    print(f"Output:   {OUTPUT_PROJECT_DIR}")
    print(f"Frontend: {OUTPUT_PROJECT_DIR / 'docs' / 'index.html'}")
    print(f"Viewer:   {OUTPUT_PROJECT_DIR / 'docs' / 'viewer.html'}")
    print(f"Backend:  {OUTPUT_PROJECT_DIR / 'codice.gs'}")


if __name__ == "__main__":
    main()
```

## File: `backup_layout_before_cleanup/pipeline/build_schema_from_input.py`
```text
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import json
from typing import Dict, Optional

from generators.import_from_html import import_visuals_from_html
from generators.import_from_sheet import save_schema_from_xlsx
from generators.merge_schema import merge_schema_with_visuals


OUTPUT_PROJECT_DIR = ROOT / "output_project"
EXAMPLES_DIR = ROOT / "examples"


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def find_input_files(input_dir: str | Path) -> Dict[str, Optional[Path]]:
    input_dir = Path(input_dir)
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    xlsx_files = sorted(input_dir.rglob("*.xlsx"))
    html_files = sorted(input_dir.rglob("*.html"))
    css_files = sorted(input_dir.rglob("*.css"))

    if not xlsx_files:
        raise FileNotFoundError(
            f"Missing required .xlsx file inside: {input_dir}"
        )

    if not html_files:
        print(f"WARNING: no .html file found inside {input_dir}. Visual enrichment will be skipped.")

    if not css_files:
        print(f"WARNING: no .css file found inside {input_dir}. This is not blocking.")

    return {
        "input_dir": input_dir,
        "xlsx": xlsx_files[0],
        "html": html_files[0] if html_files else None,
        "css": css_files[0] if css_files else None,
    }


def build_schema_from_directory(
    input_dir: str | Path,
    output_json_path: str | Path,
    enum_field_name: str = "rating",
    debug: bool = False,
) -> dict:
    paths = find_input_files(input_dir)

    sheet_schema = save_schema_from_xlsx(
        xlsx_path=paths["xlsx"],
        output_json_path=None,
        sheet_name=None,
        header_row=1,
        sample_row=2,
        debug=debug,
    )

    final_schema = sheet_schema

    if paths["html"] is not None:
        html_visuals = import_visuals_from_html(
            html_path=paths["html"],
            enum_field_name=enum_field_name,
            debug=debug,
        )

        final_schema = merge_schema_with_visuals(
            sheet_schema=sheet_schema,
            html_visuals=html_visuals,
        )

    output_json_path = Path(output_json_path)
    write_json(output_json_path, final_schema)

    if debug:
        print("\nINPUT PATHS")
        print(paths)

        print("\nFINAL ENUMS")
        print(final_schema.get("enums", {}))

        print("\nFINAL ENUM STYLES")
        print(final_schema.get("enumStyles", {}))

    return final_schema


def main() -> None:
    if len(sys.argv) == 1:
        candidate_dirs = [p for p in EXAMPLES_DIR.iterdir() if p.is_dir()]
        if not candidate_dirs:
            raise SystemExit(
                f"No subdirectories found inside examples/: {EXAMPLES_DIR}"
            )
        if len(candidate_dirs) > 1:
            raise SystemExit(
                "More than one subdirectory found inside examples/. "
                "Pass the desired input directory explicitly."
            )
        input_dir = candidate_dirs[0]
        enum_field_name = "rating"

    elif len(sys.argv) == 2:
        input_dir = Path(sys.argv[1])
        enum_field_name = "rating"

    else:
        input_dir = Path(sys.argv[1])
        enum_field_name = sys.argv[2]

    output_json = OUTPUT_PROJECT_DIR / "fields.schema.json"

    schema = build_schema_from_directory(
        input_dir=input_dir,
        output_json_path=output_json,
        enum_field_name=enum_field_name,
        debug=True,
    )

    print("\nSchema generated successfully.")
    print("Output:", output_json)
    print("Headers:", schema.get("headers", []))
    print("Enums:", schema.get("enums", {}))


if __name__ == "__main__":
    main()
```

## File: `build_from_config.py`
```text
from __future__ import annotations

import json
from pathlib import Path

from app.contracts import (
    builder_state_to_legacy_schema,
    project_section_to_project_config,
)
from generators.builder_generators import generate_all
from generators.schema_validators import validate_schema_for_product


ROOT = Path(__file__).resolve().parent
OUTPUT_CURRENT_DIR = ROOT / "output" / "current"

BUILDER_STATE_PATH = OUTPUT_CURRENT_DIR / "builder_state.json"
FIELDS_SCHEMA_PATH = OUTPUT_CURRENT_DIR / "fields.schema.json"
PROJECT_CONFIG_PATH = OUTPUT_CURRENT_DIR / "project.config.json"


def main() -> None:
    if not BUILDER_STATE_PATH.exists():
        raise FileNotFoundError(f"Missing file: {BUILDER_STATE_PATH}")

    builder_state = json.loads(BUILDER_STATE_PATH.read_text(encoding="utf-8"))

    project_config = project_section_to_project_config(builder_state)
    fields_schema = builder_state_to_legacy_schema(builder_state)

    # manteniamo aggiornati i file compatibili finché il refactor non è completo
    PROJECT_CONFIG_PATH.write_text(
        json.dumps(project_config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    FIELDS_SCHEMA_PATH.write_text(
        json.dumps(fields_schema, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    errors = validate_schema_for_product(fields_schema)
    if errors:
        joined = "\n- ".join(errors)
        raise ValueError(f"Schema validation failed:\n- {joined}")

    generated = generate_all(project_config, fields_schema)

    for relative_path, content in generated.items():
        target = OUTPUT_CURRENT_DIR / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    deploy_manifest_path = OUTPUT_CURRENT_DIR / "deploy.manifest.json"
    deploy_manifest = {
        "projectName": project_config.get("projectName", ""),
        "projectSlug": project_config.get("projectSlug", ""),
        "backendName": project_config.get("backendName", ""),
        "sheetName": project_config.get("sheetName", ""),
        "generatedFiles": list(generated.keys()),
        "sourceOfTruth": "builder_state.json",
    }
    deploy_manifest_path.write_text(
        json.dumps(deploy_manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("Build completed successfully.")
    print(f"Builder state:    {BUILDER_STATE_PATH}")
    print(f"Compat schema:    {FIELDS_SCHEMA_PATH}")
    print(f"Compat config:    {PROJECT_CONFIG_PATH}")
    print(f"Output directory: {OUTPUT_CURRENT_DIR}")


if __name__ == "__main__":
    main()
```

## File: `data/apps_registry.json`
```text
{
  "horror-movie": {
    "web_app_url": "https://script.google.com/macros/s/AKfycbzmP0437k6Mo5ebcAv3N2Kdx_ZG0IqCVnO3x28YKSrBJ2EclnShUgHJJ1s2NH2od0FQ/exec",
    "api_key": "CHANGE_ME_WRITE_KEY_2026"
  },
  "export": {
    "web_app_url": "https://script.google.com/macros/s/AKfycbxf2-Ndj7A-Vj3W5evfFZMHk_AxPQl6sTr9SpNMxi6XJt_OBEBGulGg4pCkx7w87jOhag/exec",
    "api_key": "CHANGE_ME_WRITE_KEY_2026"
  }
}
```

## File: `docs/app_ready.html`
```text
<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>App Ready — Djungo Builder</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      max-width: 980px;
      margin: 32px auto;
      padding: 0 16px;
      background: #f7f7f7;
      color: #111;
    }

    h1, h2 { margin-bottom: 8px; }

    .card {
      background: #fff;
      border: 1px solid #ddd;
      border-radius: 12px;
      padding: 18px;
      margin: 18px 0;
    }

    .muted { color: #666; line-height: 1.5; }
    .ok { color: #0a6; font-weight: bold; }
    .err { color: #b00; font-weight: bold; }

    label {
      display: block;
      margin: 10px 0 6px;
      font-weight: bold;
    }

    input[type="text"] {
      width: 100%;
      box-sizing: border-box;
      padding: 10px;
      border: 1px solid #bbb;
      border-radius: 8px;
      background: #fff;
    }

    .actions {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      align-items: center;
      margin-top: 14px;
    }

    a.button, button {
      display: inline-block;
      padding: 10px 14px;
      border: 0;
      border-radius: 8px;
      background: #111;
      color: #fff;
      text-decoration: none;
      font-weight: bold;
      cursor: pointer;
    }

    a.button.secondary, button.secondary { background: #666; }

    ol {
      margin: 10px 0 0 18px;
      color: #333;
      line-height: 1.6;
    }

    code {
      background: #f0f0f0;
      padding: 2px 5px;
      border-radius: 6px;
    }
  </style>
</head>
<body>

  <h1>Your app is ready</h1>
  <div class="card">
  <h2>Publishing mode</h2>

  <p class="muted">
    Choose how you want to publish the generated app.
  </p>

  <div class="actions">
    <button id="hostedModeBtn" type="button">Hosted on builder.sgbh.org</button>
    <button id="githubModeBtn" type="button" class="secondary">Export for GitHub Pages</button>
  </div>

  <p id="modeStatus" class="muted">
    Hosted mode is recommended for the simplest setup.
  </p>
</div>
  <p class="muted">
  Connect the generated app to its Apps Script backend.
</p>

<div id="hostedPanel">
  <div class="card">
    <h2>1. Publish Apps Script backend</h2>

    <p class="muted">
      Download the generated <code>codice.gs</code>, paste it into Google Apps Script,
      then publish it as a Web App.
    </p>

    <div class="actions">
      <a id="downloadGas" class="button secondary" href="codice.gs" download="codice.gs">
        Download codice.gs
      </a>
    </div>
  </div>

  <div class="card">
    <h2>2. Connect Apps Script backend</h2>

    <p class="muted">
      After publishing <code>codice.gs</code> as an Apps Script Web App, paste the Web App URL below.
      The app identifier is generated automatically from the saved sheet name.
    </p>

    <input id="sheetName" type="hidden" />

    <label for="webAppUrl">Apps Script Web App URL</label>
    <input id="webAppUrl" type="text" placeholder="https://script.google.com/macros/s/.../exec" />

    <label for="crudEndpoint">Generated app URL</label>
    <input id="crudEndpoint" type="text" readonly />

    <div class="actions">
      <button id="connectBtn" type="button">Connect and open app</button>
      <span id="status" class="muted"></span>
    </div>
  </div>

  <div class="card">
    <h2>3. Minimal deployment steps</h2>
    <ol>
      <li>Open Google Apps Script and paste <code>codice.gs</code>.</li>
      <li>Publish or update the Web App.</li>
      <li>Copy the final Web App URL.</li>
      <li>Paste the Web App URL above.</li>
      <li>Click <b>Connect and open app</b>.</li>
    </ol>
  </div>
</div>

<div id="githubPanel" class="card" style="display:none;">
  <h2>Export for GitHub Pages</h2>

  <p class="muted">
    Use this mode if you want to publish the generated frontend on your own GitHub Pages site.
    The frontend can still use the secure Djungo proxy on <code>builder.sgbh.org</code>.
  </p>

  <div class="actions">
    <a id="downloadIndex" class="button secondary" href="index.html" download="index.html">
      Download index.html
    </a>

    <a id="downloadViewer" class="button secondary" href="viewer.html" download="viewer.html">
      Download viewer.html
    </a>

    <a id="downloadGasGithub" class="button secondary" href="codice.gs" download="codice.gs">
      Download codice.gs
    </a>
  </div>

  <p class="muted">
    After downloading the files, upload <code>index.html</code> and <code>viewer.html</code>
    to your GitHub Pages repository. Then deploy <code>codice.gs</code> as an Apps Script Web App
    and register the backend connection using the hosted connection section.
  </p>
</div>

<div class="card">
  <h2>Djungo principle</h2>
  <p class="muted">
    The generated app remains portable: the code is readable, the data stays in your spreadsheet,
    and the browser does not expose the Apps Script URL or write key.
  </p>
</div>

<script>
  const sheetName = document.getElementById("sheetName");
  const webAppUrl = document.getElementById("webAppUrl");
  const crudEndpoint = document.getElementById("crudEndpoint");
  const statusEl = document.getElementById("status");

  const DEFAULT_API_KEY = "CHANGE_ME_WRITE_KEY_2026";

  const hostedPanel = document.getElementById("hostedPanel");
const githubPanel = document.getElementById("githubPanel");

const hostedModeBtn = document.getElementById("hostedModeBtn");
const githubModeBtn = document.getElementById("githubModeBtn");

const modeStatus = document.getElementById("modeStatus");

let publishingMode =
  sessionStorage.getItem("DJUNGO_PUBLISHING_MODE") || "hosted";

function setPublishingMode(mode) {
  publishingMode = mode;

  sessionStorage.setItem(
    "DJUNGO_PUBLISHING_MODE",
    mode
  );

  if (mode === "hosted") {
    hostedPanel.style.display = "block";
    githubPanel.style.display = "none";

    modeStatus.textContent =
      "Hosted mode selected. Only codice.gs is requ

...[TRUNCATED]...

```

## File: `docs/builder.html`
```text
<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Sheet Builder Editor</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      max-width: 1280px;
      margin: 24px auto;
      padding: 0 16px;
      background: #f7f7f7;
      color: #111;
    }

    #enumStylesWrap .card {
      box-shadow: none;
    }

    h1, h2, h3 {
      margin-bottom: 8px;
    }

    .muted {
      color: #666;
    }

    .card {
      background: #fff;
      border: 1px solid #ddd;
      border-radius: 10px;
      padding: 16px;
      margin: 16px 0;
    }

    label {
      display: block;
      margin: 10px 0 6px;
      font-weight: bold;
    }

    input, textarea, select {
      width: 100%;
      box-sizing: border-box;
      padding: 10px;
      border: 1px solid #bbb;
      border-radius: 8px;
      background: #fff;
    }

    button {
      margin-top: 14px;
      padding: 10px 14px;
      border: 0;
      border-radius: 8px;
      background: #111;
      color: #fff;
      font-weight: bold;
      cursor: pointer;
    }

    button.secondary {
      background: #666;
    }

    button:disabled {
      opacity: .6;
      cursor: not-allowed;
    }

    .grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
    }

    .actions {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin-top: 12px;
      align-items: center;
    }

    pre {
      background: #111;
      color: #d8ffd8;
      padding: 14px;
      border-radius: 10px;
      overflow: auto;
      white-space: pre-wrap;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 10px;
      background: #fff;
    }

    th, td {
      border: 1px solid #ddd;
      padding: 8px;
      font-size: 14px;
      text-align: left;
      vertical-align: top;
    }

    th {
      background: #efefef;
    }

    .readonly-cell {
      background: #f3f3f3;
      color: #666;
    }

    .tiny {
      font-size: 12px;
      color: #666;
      line-height: 1.4;
    }

    .ok {
      color: #0a6;
      font-weight: bold;
    }

    .err {
      color: #b00;
      font-weight: bold;
    }
  </style>
</head>
<body>

  <h1>Sheet Builder Editor <span class="muted">— builder_state v0</span></h1>
  <p class="muted">
  In questa v0 puoi modificare <b>label</b>, <b>required</b>, visibilità nel form e nel viewer.
  Il <b>type</b> resta visibile ma non modificabile, perché deriva dalla struttura del foglio sorgente.
  I campi marcati come <b>system field</b> sono campi strutturali o auto-gestiti.
</p>

  <div class="card">
    <h2>1. Load builder state</h2>

    <label for="fileInput">builder_state.json</label>
    <input id="fileInput" type="file" accept=".json,application/json" />

    <div class="actions">
      <button id="loadSampleBtn" type="button" class="secondary">Load sample from textarea</button>
      <span id="loadStatus" class="muted"></span>
    </div>

    <label for="rawJsonInput">Optional raw JSON paste area</label>
    <textarea id="rawJsonInput" rows="10" placeholder='Incolla qui builder_state.json se preferisci'></textarea>
  </div>

    <div class="card">
    <h2>
      <div class="card">
        
  <h2>2. Project</h2>
  <p class="muted">
    Qui modifichi i metadati principali del progetto generato. Il campo <b>Backend write key</b>
    è la chiave usata dal backend Apps Script per autorizzare insert, update e delete.
  </p>

  <div class="grid">
    <div>
      <label for="projectName">Project name</label>
      <input id="projectName" />

      <label for="projectSlug">Project slug</label>
      <input id="projectSlug" />

      <label for="backendName">Backend name</label>
      <input id="backendName" />

      <label for="entityName">Entity name</label>
      <input id="entityName" />
    </div>

    <div>
      <label for="entityLabelLower">Entity label (lowercase)</label>
      <input id="entityLabelLower" />

      <label for="sheetName">Sheet name</label>
      <input id="sheetName" />

      <label for="buildMarker">Build marker</label>
      <input id="buildMarker" />

      <label for="adminPassword">Backend write key</label>
      <input id="adminPassword" />
    </div>
  </div>
</div>

  <div class="card">
  <h2>3. Fields editor</h2>
  <p class="muted">
    In questa v0 puoi modificare <b>label</b>, <b>required</b>, visibilità nel form e nel viewer.
    Il <b>type</b> resta visibile ma non modificabile, perché deriva dalla struttura del foglio sorgente.
    I campi marcati come <b>system field</b> sono campi strutturali o auto-gestiti.
  </p>

  <table id="fieldsTable">
    <thead>
      <tr>
        <th>name</th>
        <th>label</th>
        <th>type</th>
        <th>required</th>
        <th>visibleInForm</th>
        <th>visibleInViewer</th>
        <th>system field</th>
      </tr>
    </thead>
    <tbody></tbody>
  </table>
</div>

        <table id="fieldsTable">
      <thead>
        <tr>
          <th>name</th>
          <th>label</th>
          <th>type</th>
          <th>required</th>
          <th>visibleInForm</th>
          <th>visibleInViewer</th>
          <th>system field</th>
        </tr>
      </thead>
      <tbody></tbody>
    </table>
  </div>

  <div class="card">
    <h2>4. Updated builder state preview</h2>
    <pre id="stateOut"></pre>
  </div>

    <div class="card">
    <h2>5. Enum styles editor</h2>
    <p class="muted">
      Per i campi di tipo <b>enum</b> puoi modificare i colori dei singoli valori.
      <br>Formato suggerito: <code>#RRGGBB</code>
    </p>

    <div id="enumStylesWrap"></div>
  </div>

  <div class="card">
    <h2>6. Export</h2>
    <div class="actions">
      <button id="downloadBtn" type="button">Download updated builder_state.json</button>
      <span id="downloadStatus" class="muted"></span>
    </div>
  </div>

  

<script>
  let builderState = null;

  function setStatus(id, msg, cls = "m

...[TRUNCATED]...

```

## File: `docs/generate.html`
```text
<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Generate App — Djungo Builder</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      max-width: 1100px;
      margin: 32px auto;
      padding: 0 16px;
      background: #f7f7f7;
      color: #111;
    }

    h1, h2 {
      margin-bottom: 8px;
    }

    .card {
      background: #fff;
      border: 1px solid #ddd;
      border-radius: 12px;
      padding: 18px;
      margin: 18px 0;
    }

    .muted {
      color: #666;
      line-height: 1.5;
    }

    .grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
    }

    label {
      display: block;
      margin: 10px 0 6px;
      font-weight: bold;
    }

    input[type="file"], input[type="text"], textarea {
      width: 100%;
      box-sizing: border-box;
      padding: 10px;
      border: 1px solid #bbb;
      border-radius: 8px;
      background: #fff;
    }

    .actions {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      align-items: center;
      margin-top: 14px;
    }

    a.button, button {
      display: inline-block;
      padding: 10px 14px;
      border: 0;
      border-radius: 8px;
      background: #111;
      color: #fff;
      text-decoration: none;
      font-weight: bold;
      cursor: pointer;
    }

    a.button.secondary, button.secondary {
      background: #666;
    }

    .ok {
      color: #0a6;
      font-weight: bold;
    }

    .err {
      color: #b00;
      font-weight: bold;
    }

    .hidden {
      display: none;
    }

    pre {
      background: #111;
      color: #d8ffd8;
      padding: 14px;
      border-radius: 10px;
      overflow: auto;
      white-space: pre-wrap;
    }

    code {
      background: #f0f0f0;
      padding: 2px 5px;
      border-radius: 6px;
    }

    ul {
      margin: 8px 0 0 18px;
      color: #333;
      line-height: 1.6;
    }

    @media (max-width: 860px) {
      .grid {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>

  <h1>Generate your app</h1>
  <p class="muted">
    Carica i file esportati da Google Sheets e prepara la generazione del progetto finale.
    In questa fase il parser e il generatore reali continuano a essere gestiti dalla pipeline Python,
    ma questa pagina rappresenta il flusso cliente corretto.
  </p>
  
  <div id="resumeBlock" class="card" style="display:none;">
  <h2>Resume your last app</h2>
  <p class="muted">
    You recently used this app. You can open it directly.
  </p>

  <div class="actions">
  <button id="resumeBtn" type="button">
    Open last app
  </button>

  <button id="clearLastBtn" type="button" class="secondary">
    Forget
  </button>
</div>

<p class="muted" style="margin-top:8px;">
  Use this only if the spreadsheet structure has NOT changed.
</p>
</div>

  <div class="card">
    <h2>1. Source files</h2>
    <p class="muted">
      I tre input logici di partenza sono:
      <code>.xlsx</code>, <code>.html</code> e <code>sheet name</code>.
      Il nome del foglio è obbligatorio perché viene usato nella configurazione del progetto.
    </p>

    <div class="card">
  <h2>2. Connect an already deployed Apps Script backend</h2>
  <p class="muted">
    If your Apps Script backend is already published, enter the sheet name and Web App URL.
    The app slug will be generated automatically from the sheet name.
  </p>

  <label for="existingSheetName">Sheet name *</label>
  <input id="existingSheetName" type="text" placeholder="Es. HorrorMovie" />

  <label for="existingWebAppUrl">Apps Script Web App URL *</label>
  <input id="existingWebAppUrl" type="text" placeholder="https://script.google.com/macros/s/.../exec" />

  <div class="actions">
    <button id="openExistingBtn" type="button">Connect backend and open app</button>
    <span id="existingStatus" class="muted"></span>
  </div>
</div>

    <div class="grid">
      <div>
        <label for="xlsxFile">Google Sheets export (.xlsx) *</label>
        <input id="xlsxFile" type="file" accept=".xlsx" />
      </div>
      <div>
        <label for="htmlFile">Google Sheets export (.html) *</label>
        <input id="htmlFile" type="file" accept=".html,text/html" />
      </div>
    </div>

    <label for="sheetName">Sheet name *</label>
    <input id="sheetName" type="text" placeholder="Es. HorrorMovie" />

    <div class="actions">
      <button id="parserBtn" type="button">Start parser</button>
      <span id="parserStatus" class="muted"></span>
    </div>
  </div>

  <div id="parserPanel" class="card hidden">
    <h2>2. Parser status</h2>
    <p class="muted">
      Il parser legge la struttura del database, i campi, le formule rilevate, gli enum e i colori.
      In questa fase intermedia, il controllo tecnico dettagliato può ancora essere rifinito nella pipeline interna.
    </p>

    <ul>
      <li>Campi rilevati dal foglio</li>
      <li>Formule trovate nei campi calcolati</li>
      <li>Enum e colori visuali</li>
      <li>Configurazione di base del frontend</li>
    </ul>

    <div class="actions">
     <button id="openReviewBtn" type="button" class="secondary">Open internal review page</button>
    </div>
  </div>

  <div id="generatePanel" class="card hidden">
    <h2>3. Prepare Apps Script backend</h2>
    <p class="muted">
  Hosted mode only requires <code>codice.gs</code>.
  Frontend files are already managed by builder.sgbh.org.
</p>

    <div class="actions">
      <button id="generateBtn" type="button">Generate index.html, viewer.html and codice.gs</button>
      <span id="generateStatus" class="muted"></span>
    </div>

    <div id="generatedFilesBox" class="hidden" style="margin-top:14px;">
      <p class="ok">Final package prepared</p>
      <ul>
        <li><code>index.html</code> — home page del database e CRUD finale</li>
        <li><code>viewer.html</code> — viewer tabellare</li>
        <li><code>codice.gs</code> — backend G

...[TRUNCATED]...

```

## File: `docs/index.html`
```text
<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Generated App</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 1100px; margin: 28px auto; padding: 0 16px; }
    h1 { margin: 0 0 6px; }
    .muted { color:#666; }
    .card { border:1px solid #e5e5e5; border-radius:10px; padding:14px; background:#fafafa; margin:12px 0; }
    label { display:block; margin:10px 0 6px; font-weight:700; }
    input, select { width:100%; padding:9px; border:1px solid #ccc; border-radius:8px; box-sizing:border-box; background:#fff; }
    button { padding:9px 12px; border:0; border-radius:8px; background:#111; color:#fff; cursor:pointer; font-weight:800; }
    button.secondary { background:#666; }
    button:disabled { opacity:.6; cursor:not-allowed; }
    .row { display:grid; grid-template-columns: 1fr 1fr; gap:12px; }
    .actions { display:flex; gap:10px; align-items:center; flex-wrap:wrap; margin-top:12px; }
    .ok { color:#0a6; font-weight:800; }
    .err { color:#b00; font-weight:800; }
    iframe { width:100%; height:560px; border:1px solid #ddd; border-radius:10px; background:#fff; }
    small { display:block; margin-top:8px; color:#666; }
    pre { background:#0b0b0b; color:#d6ffd6; border-radius:10px; padding:12px; overflow:auto; }
  </style>
</head>
<body>

  <h1>Generated App database</h1>

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

    <small>Slug app: <code>generated-app</code></small>
  </div>

  <div class="card">
    <h3 style="margin:0 0 10px;">Insert (Item)</h3>


    <label for="year">year <span class="muted">(optional)</span></label>
    <input id="year" type="number" min="0" placeholder="year" />


    <label for="title">Title <span class="muted">(optional)</span></label>
    <input id="title" placeholder="Title" />


    <label for="url">url <span class="muted">(optional)</span></label>
    <input id="url" placeholder="url" />


    <label for="nation">nation <span class="muted">(optional)</span></label>
    <input id="nation" placeholder="nation" />


    <label for="rating">rating <span class="muted">(optional)</span></label>
    <select id="rating">
      <option value="" selected>—</option><option>Mediocre</option><option>Medio</option><option>Buono</option><option>Ottimo</option><option>Capolavoro</option><option>Pessimo</option>
    </select>

    <div class="actions">
      <button id="insertBtn" type="button">Insert</button>
      <span id="insertStatus" class="muted"></span>
    </div>
  </div>

  <div class="card">
    <h3 style="margin:0 0 10px;">Find, update or delete an existing record</h3>
      <p class="muted">
    Enter a record id, load the record into the form, then update or delete it.
      </p>
    <div class="row">
      <div>
        <label for="crud_id">id</label>
        <input id="crud_id" type="number" min="1" step="1" placeholder="1" />
      </div>
      <div>
        <label>&nbsp;</label>
        <div class="actions" style="margin-top:0;">
          <button id="getBtn" type="button" class="secondary">Load record</button>
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
  const APP_SLUG = qs.get("app") || "generated-app";

  function setMsg(el, msg, cls) {
    el.className = cls || "muted";
    el.textContent = msg;
  }


    async function apiCall_(mode, params = {}) {
    let url = `/api/apps/${APP_SLUG}/${mode}`;

    const qs = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      qs.set(k, String(v ?? ""));
    });

    const query = qs.toString();
    if (query) url += "?" + query;

    const resp = await fetch(url);
    const data = await resp.json();

    if (!resp.ok) {
      throw new Error(data.error || `HTTP ${resp.status}`);
    }

    return data;
  }

    function apiUrl_(mode) {
    return `/api/apps/${APP_SLUG}/${mode}`;
  }

  async function apiCall_(mode, params = {}, method = "GET") {
    let url = apiUrl_(mode);

    const options = {
      method,
      headers: {}
    };

    if (method === "GET") {
      const qs = new URLSearchParams();
      Object.entries(params).forEach(([k, v]) => {
        qs.set(k, String(v ?? ""));
      });

      const query = qs.toString();
      if (query) url += "?" + query;
    } else {
      options.headers["Content-Type"] = "application/json";
      optio

...[TRUNCATED]...

```

## File: `docs/review.html`
```text
<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Review Generated App</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      max-width: 1240px;
      margin: 24px auto;
      padding: 0 16px;
      background: #f7f7f7;
      color: #111;
    }

    a.button, button {
  display: inline-block;
  padding: 10px 14px;
  border: 0;
  border-radius: 8px;
  background: #111;
  color: #fff;
  text-decoration: none;
  font-weight: bold;
  cursor: pointer;
}

a.button.secondary {
  background: #666;
}

    h1, h2, h3 {
      margin-bottom: 8px;
    }

    .card h2 {
      margin-top: 0;
    }

    .muted {
      color: #666;
    }

    .card {
      background: #fff;
      border: 1px solid #ddd;
      border-radius: 10px;
      padding: 16px;
      margin: 16px 0;
    }

    label {
      display: block;
      margin: 10px 0 6px;
      font-weight: bold;
    }

    input, textarea, select {
      width: 100%;
      box-sizing: border-box;
      padding: 10px;
      border: 1px solid #bbb;
      border-radius: 8px;
      background: #fff;
    }

    button {
      margin-top: 14px;
      padding: 10px 14px;
      border: 0;
      border-radius: 8px;
      background: #111;
      color: #fff;
      font-weight: bold;
      cursor: pointer;
    }

    button.secondary {
      background: #666;
    }

    button:disabled {
      opacity: .6;
      cursor: not-allowed;
    }

    .grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
    }

    .actions {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin-top: 12px;
      align-items: center;
    }

    pre {
      background: #111;
      color: #d8ffd8;
      padding: 14px;
      border-radius: 10px;
      overflow: auto;
      white-space: pre-wrap;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 10px;
      background: #fff;
    }

    th, td {
      border: 1px solid #ddd;
      padding: 8px;
      font-size: 14px;
      text-align: left;
      vertical-align: top;
    }

    th {
      background: #efefef;
    }

    .readonly-cell {
      background: #f3f3f3;
      color: #666;
    }

    .ok {
      color: #0a6;
      font-weight: bold;
    }

    .err {
      color: #b00;
      font-weight: bold;
    }

    .badge {
      display: inline-block;
      padding: 3px 8px;
      border-radius: 999px;
      background: #eee;
      font-size: 12px;
      margin-left: 6px;
    }

    .hero-note {
      line-height: 1.5;
    }

    .hidden {
  display: none;
}
  </style>
</head>
<body>

  <h1>Review Your Generated App <span class="badge">customer flow</span></h1>
  <p class="muted hero-note">
    In questa pagina puoi controllare la struttura rilevata dal sistema prima della generazione finale
    della tua interfaccia CRUD. Puoi verificare campi, nomi visualizzati e colori dei valori speciali.
  </p>

  <div class="card">
  <h2>1. App summary</h2>

  <p class="muted">
    Review the detected spreadsheet structure before generating the final app.
  </p>

  <div class="grid">
    <div>
      <label for="sheetName">Sheet name</label>
      <input id="sheetName" readonly />
    </div>

    <div>
      <label for="projectName">App name</label>
      <input id="projectName" readonly />
    </div>
  </div>

  <input id="entityName" type="hidden" />
  <input id="entityLabelLower" type="hidden" />
  <input id="projectSlug" type="hidden" />
  <input id="backendName" type="hidden" />
  <input id="buildMarker" type="hidden" />
  <input id="adminPassword" type="hidden" />
  <input id="fileInput" type="file" accept=".json,application/json" style="display:none;" />
  <textarea id="rawJsonInput" style="display:none;"></textarea>
  <button id="loadSampleBtn" type="button" style="display:none;">Load</button>
  <span id="loadStatus" style="display:none;"></span>
</div>

  <div class="card">
    <h2>2. Detected fields</h2>
    <p class="muted">
      Qui puoi controllare i nomi visualizzati dei campi e decidere se devono comparire nel form o nel viewer finale.
      I tipi rilevati dal parser restano non modificabili in questa fase.
    </p>

    <table id="fieldsTable">
      <thead>
        <tr>
          <th>field name</th>
          <th>display label</th>
          <th>type</th>
          <th>required</th>
          <th>show in form</th>
          <th>show in viewer</th>
          <th>system field</th>
        </tr>
      </thead>
      <tbody></tbody>
    </table>
  </div>

  <div class="card">
    <h2>3. Special value colors</h2>
    <p class="muted">
      Per i campi con valori predefiniti puoi controllare i colori visualizzati nel viewer finale.
    </p>

    <div id="enumStylesWrap"></div>
  </div>

  

 <div class="card">
  <h2>4. Generate final app</h2>

  <p class="muted">
    Review fields, labels and colors. When everything is correct, generate the final CRUD app.
  </p>

  <div id="idWarning" class="card" style="display:none; border-color:#f0b429; background:#fff8e1;">
    <h3 style="margin-top:0;">No ID column detected</h3>

    <p class="muted">
      The generated CRUD app needs a unique record identifier to load, update and delete existing rows safely.
    </p>

    <p class="muted">
      Add an <code>id</code> column to the spreadsheet, then export the source files again and restart the parser flow.
    </p>

    <div class="actions">
      <button id="restartForIdBtn" type="button" class="secondary">
        Restart from source files
      </button>
    </div>
  </div>

  <div class="actions">
    <button id="downloadBtn" type="button">
      Generate final app
    </button>

    <a
      id="openAppReady"
      class="button secondary"
      href="app_ready.html"
      style="display:none;"
    >
      Continue to delivery page
    </a>

    <span id="downloadStatus" class="muted"></span>
  </div>
</div>

 
  <a
    id="openAppReady"
    cla

...[TRUNCATED]...

```

## File: `docs/viewer.html`
```text
<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Item Viewer</title>
  <link href="https://cdn.jsdelivr.net/npm/tabulator-tables@6.4.0/dist/css/tabulator.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/tabulator-tables@6.4.0/dist/js/tabulator.min.js"></script>
  <style>
    body { font-family: Arial, sans-serif; margin: 12px; }
    .muted { color:#666; }
    .toolbar { display:flex; gap:10px; align-items:end; flex-wrap:wrap; margin: 8px 0 12px; }
    .toolbar label { display:block; font-size:12px; font-weight:700; color:#444; margin-bottom:4px; }
    .toolbar input, .toolbar select {
      padding:8px;
      border:1px solid #ccc;
      border-radius:8px;
      background:#fff;
      min-width:180px;
    }

    table { border-collapse: collapse; width: 100%; }
    th, td {
      border:1px solid #e5e5e5;
      padding:8px;
      font-size: 13px;
      vertical-align: top;
      overflow-wrap:anywhere;
      white-space: pre-wrap;
    }

    thead th {
      position: sticky;
      top: 0;
      z-index: 2;
      background: #2f3b52;
      color: #fff;
      font-weight: 800;
    }

    tbody tr:nth-child(even){ background:#f6f8fb; }
    tbody tr:nth-child(odd){ background:#ffffff; }

    tbody tr.first-row {
      background: #fff3cd !important;
      outline: 2px solid #ffe69c;
      outline-offset: -2px;
    }
  </style>
</head>
<body>

  <div class="muted">Viewer read-only — tab <b>Sheet1</b></div>

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
  const APP_SLUG = qs.get("app") || "generated-app";
  const URL_LIMIT = qs.get("limit") || "50";
  const EMBEDDED_MODE = qs.get("embedded") === "1";

  const VISIBLE_HEADERS = [
  "id",
  "year",
  "title",
  "url",
  "link",
  "nation",
  "rating"
];
  const ENUMS = {
  "rating": [
    "Mediocre",
    "Medio",
    "Buono",
    "Ottimo",
    "Capolavoro",
    "Pessimo"
  ]
};
  const LABELS = {
  "id": "id",
  "year": "year",
  "title": "Title",
  "url": "url",
  "link": "link",
  "nation": "nation",
  "rating": "rating"
};
  const ENUM_STYLES = {
  "rating": {
    "Capolavoro": {
      "bg": "#215a6c",
      "fg": "#c6dbe1"
    },
    "Ottimo": {
      "bg": "#d4edbc",
      "fg": "#11734b"
    },
    "Buono": {
      "bg": "#ffe5a0",
      "fg": "#473821"
    },
    "Medio": {
      "bg": "#ffc8aa",
      "fg": "#753800"
    },
    "Mediocre": {
      "bg": "#ffcfc9",
      "fg": "#b10202"
    },
    "Pessimo": {
      "bg": "#e8eaed",
      "fg": "#000000"
    }
  }
};

    async function apiCall_(mode, params = {}) {
    let url = `/api/apps/${APP_SLUG}/${mode}`;

    const qs = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      qs.set(k, String(v ?? ""));
    });

    const query = qs.toString();
    if (query) url += "?" + query;

    const resp = await fetch(url);
    const data = await resp.json();

    if (!resp.ok) {
      throw new Error(data.error || `HTTP ${resp.status}`);
    }

    return data;
  }

  function esc(s) {
    return String(s ?? "").replace(/[&<>"']/g, c => (
      {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]
    ));
  }

  function styleAttrForEnum(headerName, value) {
    const fieldStyles = ENUM_STYLES[headerName];
    if (!fieldStyles) return "";
    const styleDef = fieldStyles[String(value ?? "").trim()];
    if (!styleDef) return "";

    const parts = [];
    if (styleDef.bg) parts.push(`background:${styleDef.bg}`);
    if (styleDef.fg) parts.push(`color:${styleDef.fg}`);
    if (!parts.length) return "";

    parts.push("font-weight:700");
    parts.push("text-align:center");
    return parts.join("; ");
  }

  let LAST_HEADERS = [];
  let LAST_ROWS = [];

    let DATA_TABLE = null;

  function rowsToObjects(headers, rows) {
    return rows.map(row => {
      const obj = {};

      headers.forEach((h, i) => {
        obj[h] = row[i];
      });

      return obj;
    });
  }

  function buildColumns(headers) {
    return headers
      .filter(h => VISIBLE_HEADERS.includes(h))
      .map(h => {
        return {
          title: LABELS[h] || h,
          field: h,
          headerFilter: "input",
          sorter: "string",
          resizable: true,
          formatter: function(cell) {
            const value = cell.getValue();
            const style = styleAttrForEnum(h, value);

            if (style) {
              const el = cell.getElement();

              style.split(";").forEach(rule => {
                const parts = rule.split(":");

                if (parts.length === 2) {
                  el.style[parts[0].trim()] = parts[1].trim();
                }
              });
            }

            return esc(value);
          }
        };
      });
  }

  function renderTable() {
    const status = document.getElementById("status");
    const search = document.getElementById("searchBox").value.trim().toLowerCase();

    if (!LAST_HEADERS.length) {
      status.textContent = "No data loaded";
      return;
    }

    const visibleHeaders = LAST_HEADERS.filter(h => VISIBLE_HEADERS.includes(h));

    const visibleIndexes = LAST_HEADERS
      .map((h, i) => (visibleHeaders.includes(h) ? i : -1))
      .filter(i => i >= 0);

    let rows = LAST_ROWS.slice();

    if (search) {
      rows = rows.filter(r =>
        visibleIndexes.some(i =>
          String(r[i] ?? "").toLowerCase().includes(search)
        )
      );
   

...[TRUNCATED]...

```

## File: `examples/case_001/HorrorMovie.html`
```text
<meta http-equiv="Content-Type" content="text/html; charset=utf-8"><link type="text/css" rel="stylesheet" href="resources/sheet.css" >
<style type="text/css">.ritz .waffle a { color: inherit; }.ritz .waffle .s2{background-color:#ffffff;text-align:left;color:#000000;font-family:Arial;font-size:10pt;vertical-align:bottom;white-space:nowrap;direction:ltr;padding:2px 3px 2px 3px;}.ritz .waffle .s7{background-color:#fef8e3;text-align:right;color:#000000;font-family:Arial;font-size:10pt;vertical-align:bottom;white-space:nowrap;direction:ltr;padding:2px 3px 2px 3px;}.ritz .waffle .s9{background-color:#fef8e3;text-align:left;text-decoration:underline;text-decoration-skip-ink:none;-webkit-text-decoration-skip:none;color:#1155cc;font-family:Arial;font-size:10pt;vertical-align:bottom;white-space:nowrap;direction:ltr;padding:2px 3px 2px 3px;}.ritz .waffle .s4{background-color:#ffe599;text-align:left;color:#000000;font-family:Arial;font-size:10pt;vertical-align:bottom;white-space:nowrap;direction:ltr;padding:2px 3px 2px 3px;}.ritz .waffle .s5{background-color:#ffe599;text-align:left;text-decoration:underline;text-decoration-skip-ink:none;-webkit-text-decoration-skip:none;color:#1155cc;font-family:Arial;font-size:10pt;vertical-align:bottom;white-space:nowrap;direction:ltr;padding:2px 3px 2px 3px;}.ritz .waffle .s1{background-color:#ffffff;text-align:center;color:#000000;font-family:Arial;font-size:10pt;vertical-align:bottom;white-space:nowrap;direction:ltr;padding:2px 3px 2px 3px;}.ritz .waffle .s0{background-color:#f7cb4d;text-align:left;color:#000000;font-family:Arial;font-size:10pt;vertical-align:bottom;white-space:nowrap;direction:ltr;padding:2px 3px 2px 3px;}.ritz .waffle .s3{background-color:#ffe599;text-align:right;color:#000000;font-family:Arial;font-size:10pt;vertical-align:bottom;white-space:nowrap;direction:ltr;padding:2px 3px 2px 3px;}.ritz .waffle .s6{text-overflow:ellipsis;overflow:hidden;vertical-align:top;display:inline-block;height:fit-content;border-radius:8px;}.ritz .waffle .s8{background-color:#fef8e3;text-align:left;color:#000000;font-family:Arial;font-size:10pt;vertical-align:bottom;white-space:nowrap;direction:ltr;padding:2px 3px 2px 3px;}</style><div class="ritz grid-container" dir="ltr"><table class="waffle" cellspacing="0" cellpadding="0"><thead><tr><th class="row-header freezebar-origin-ltr"></th><th id="855617048C0" style="width:100px;" class="column-headers-background">A</th><th id="855617048C1" style="width:100px;" class="column-headers-background">B</th><th id="855617048C2" style="width:179px;" class="column-headers-background">C</th><th id="855617048C3" style="width:403px;" class="column-headers-background">D</th><th id="855617048C4" style="width:100px;" class="column-headers-background">E</th><th id="855617048C5" style="width:100px;" class="column-headers-background">F</th><th id="855617048C6" style="width:184px;" class="column-headers-background">G</th><th id="855617048C7" style="width:100px;" class="column-headers-background">H</th><th id="855617048C8" style="width:100px;" class="column-headers-background">I</th><th id="855617048C9" style="width:100px;" class="column-headers-background">J</th><th id="855617048C10" style="width:100px;" class="column-headers-background">K</th><th id="855617048C11" style="width:100px;" class="column-headers-background">L</th><th id="855617048C12" style="width:100px;" class="column-headers-background">M</th><th id="855617048C13" style="width:100px;" class="column-headers-background">N</th><th id="855617048C14" style="width:100px;" class="column-headers-background">O</th></tr></thead><tbody><tr style="height: 20px"><th id="855617048R0" style="height: 20px;" class="row-headers-background"><div class="row-header-wrapper" style="line-height: 20px">1</div></th><td class="s0" dir="ltr">id</td><td class="s0" dir="ltr">year</td><td class="s0" dir="ltr">Title</td><td class="s0" dir="ltr">url</td><td class="s0" dir="ltr">link</td><td class="s0" dir="ltr">nation</td><td class="s0" dir="ltr">rating</td><td></td><td class="s1">#N/A</td><td></td><td></td><td></td><td></td><td></td><td class="s2" dir="ltr">Pessimo</td></tr><tr style="height: 20px"><th id="855617048R1" style="height: 20px;" class="row-headers-background"><div class="row-header-wrapper" style="line-height: 20px">2</div></th><td class="s3" dir="ltr">1</td><td class="s3" dir="ltr">1960</td><td class="s4" dir="ltr">Psycho</td><td class="s5" dir="ltr"><a target="_blank" href="https://en.wikipedia.org/wiki/Psycho_(1960_film)">https://en.wikipedia.org/wiki/Psycho_(1960_film)</a></td><td class="s5" dir="ltr"><a target="_blank" href="https://en.wikipedia.org/wiki/Psycho_(1960_film)">Psycho</a></td><td class="s4" dir="ltr">USA</td><td class="s4" dir="ltr"><span class="s6" style="background-color: #215a6c; color: #c6dbe1; width: 156.0px; max-width: 156.0px; margin-left: 6.0px;  padding: 1.0px 5.0px 1.0px 5.0px ; ">Capolavoro</span></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td class="s2" dir="ltr">Mediocre</td></tr><tr style="height: 20px"><th id="855617048R2" style="height: 20px;" class="row-headers-background"><div class="row-header-wrapper" style="line-height: 20px">3</div></th><td class="s7" dir="ltr">2</td><td class="s7" dir="ltr">1973</td><td class="s8" dir="ltr">The Exorcist</td><td class="s9" dir="ltr"><a target="_blank" href="https://en.wikipedia.org/wiki/The_Exorcist">https://en.wikipedia.org/wiki/The_Exorcist</a></td><td class="s9" dir="ltr"><a target="_blank" href="https://en.wikipedia.org/wiki/The_Exorcist">The Exorcist</a></td><td class="s8" dir="ltr">USA</td><td class="s8" dir="ltr"><span class="s6" style="background-color: #d4edbc; color: #11734b; width: 156.0px; max-width: 156.0px; margin-left: 6.0px;  padding: 1.0px 5.0px 1.0px 5.0px ; ">Ottimo</span></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td class="s2" dir="ltr">Medio</td></tr><tr style="height: 20px"><th id="855617048R3" style="height: 20px;" class="row-headers-background"><

...[TRUNCATED]...

```

## File: `examples/case_001/sheet.css`
```text
@charset "UTF-8";@import url(https://fonts.googleapis.com/css?family=Google+Sans);a{text-decoration:none}a:link{color:#15c}a:visited{color:#61c}a:active{color:#d14836}a:hover{text-decoration:underline}.quantumIconsIcon{font-family:Material Icons Extended;font-weight:400;font-style:normal;font-size:24px;line-height:1;letter-spacing:normal;text-rendering:optimizeLegibility;text-transform:none;display:inline-block;word-wrap:normal;direction:ltr;font-feature-settings:"liga" 1;-webkit-font-smoothing:antialiased}html[dir=rtl] .quantumIconsRtlIcon{transform:scaleX(-1)}.waffleDialogRitzImportDialogStandardDialog{--W1aG0b:6px 24px 0px;--V5opxd:var(--gm3-sys-color-surface,#fff);--o0m4Bd:var(--gm3-sys-color-surface,#fff);--Tlqqfc:569px;--urucif:6px;--Cv3aid:24px;--xkSh4b:0px;--tukwab:24px}.waffleDialogRitzImportDialogStandardInfoDialog{--W1aG0b:50px 36px 0px;--urucif:50px;--Cv3aid:36px;--xkSh4b:0px;--tukwab:36px}.waffleDialogRitzImportDialogStandardLandingDialog{--W1aG0b:24px 22px 0px;--Tlqqfc:540px;--urucif:24px;--Cv3aid:22px;--xkSh4b:0px;--tukwab:22px}.waffleDialogRitzImportDialogStandardSuccessDialog{--W1aG0b:54px 36px;--urucif:54px;--Cv3aid:36px;--xkSh4b:54px;--tukwab:36px}.waffleDialogRitzImportDialogStandardErrorDialog{--W1aG0b:20px;--urucif:20px;--Cv3aid:20px;--xkSh4b:20px;--tukwab:20px}.waffleDialogRitzImportDialogInfoAlertCard{--gm3-card-filled-container-color:var(--gm3-sys-color-error-container,#f9dedc);align-items:center;display:flex;padding:12px 20px;margin-bottom:20px}.waffleDialogRitzImportDialogInfoIcon.docs-icon.goog-inline-block{min-height:20px;min-width:20px;margin-right:12px}.waffleDialogRitzImportDialogFile{font-family:Google Sans,Roboto,Arial,sans-serif;font-size:1rem;font-weight:500;letter-spacing:0;line-height:1.5rem}.waffleDialogRitzImportDialogFileName{font-family:Google Sans,Roboto,Arial,sans-serif;font-size:1rem;font-weight:400;letter-spacing:0;line-height:1.5rem;padding:6px 0 16px}.waffleDialogRitzImportDialogOkButton{--gm3-button-filled-tonal-label-text-size:14px;--gm3-button-filled-tonal-container-color:var(--gm3-sys-color-primary,#0b57d0);--gm3-button-filled-tonal-label-text-color:var(--gm3-sys-color-on-primary,#fff);--gm3-button-filled-tonal-focus-label-text-color:var(--gm3-sys-color-on-primary,#fff);--gm3-button-filled-tonal-hover-label-text-color:var(--gm3-sys-color-on-primary,#fff);--gm3-button-filled-tonal-pressed-label-text-color:var(--gm3-sys-color-on-primary,#fff)}.waffleDialogRitzImportDialogPromptCard{--gm3-card-outlined-container-color:var(--gm3-sys-color-on-primary,#fff);--gm3-card-outlined-container-shape-start-start:28px;--gm3-card-outlined-container-shape-start-end:28px;--gm3-card-outlined-container-shape-end-end:28px;--gm3-card-outlined-container-shape-end-start:28px;padding:26px 15px 26px 24px}.waffleDialogRitzImportDialogPromptCardContent{display:flex;flex-direction:row;gap:16px}.waffleDialogRitzImportDialogPromptCardTextContent{display:flex;flex-direction:column;gap:12px}.waffleDialogRitzImportDialogPromptCardBoldText{font-weight:500}.waffleDialogRitzImportDialogInfoImage{width:496px;height:182px}.waffleDialogRitzImportDialogInfoDialogTitle{font-size:22px;font-weight:400;line-height:28px}.waffleDialogRitzImportDialogInfoDialogText{font-family:Google Sans,Roboto,Arial,sans-serif;font-size:.875rem;font-weight:400;letter-spacing:0;line-height:1.25rem;color:var(--gm3-sys-color-on-surface,#1f1f1f)}.waffleDialogRitzImportDialogInfoDialogFileNameContainer{display:flex;flex-direction:column;gap:8px;text-align:left}.waffleDialogRitzImportDialogInfoDialogFileNameLabel{font-family:Google Sans,Roboto,Arial,sans-serif;font-size:.875rem;font-weight:400;letter-spacing:0;line-height:1.25rem;color:var(--gm3-sys-color-on-surface-variant,#444746)}.waffleDialogRitzImportDialogInfoDialogFileName{font-family:Google Sans,Roboto,Arial,sans-serif;font-size:1rem;font-weight:400;letter-spacing:0;line-height:1.5rem;color:var(--gm3-sys-color-on-surface-variant,#444746)}.waffleDialogRitzImportDialogInfoDialogNote{font-family:Google Sans,Roboto,Arial,sans-serif;font-size:.75rem;font-weight:400;letter-spacing:.00625rem;line-height:1rem;color:var(--gm3-sys-color-on-surface-variant,#444746)}.waffleDialogRitzImportDialogInfoDialogTextContent{align-self:stretch;display:flex;flex-direction:column;gap:16px;padding:24px 2px 0 2px;font-style:normal}.waffleDialogRitzImportDialogLoadingDialogContent{align-items:center;align-self:stretch;display:flex;flex-direction:column;gap:16px;padding:20px 0;text-align:center;font-style:normal}.waffleDialogRitzImportDialogLoadingDialog{--W1aG0b:24px 22px;--urucif:24px;--Cv3aid:22px;--xkSh4b:24px;--tukwab:22px}.waffleDialogRitzImportDialogLoadingSpinnerContainer{align-items:center;display:flex;flex-direction:row;gap:16px}.waffleDialogRitzImportDialogLoadingStatusText{font-family:Google Sans,Roboto,Arial,sans-serif;font-size:.875rem;font-weight:400;letter-spacing:0;line-height:1.25rem;color:var(--gm3-sys-color-on-surface,#1f1f1f)}.waffleDialogRitzImportDialogFullScreenSuccessDialog{--RSexXb:540px;--V5opxd:var(--gm3-sys-color-surface,#fff)}.waffleDialogRitzImportDialogSuccessDialogContent{align-items:center;align-self:stretch;display:flex;flex-direction:column;gap:16px;padding:44px 24px 24px}.waffleDialogRitzImportDialogDimensionsText{font-family:Google Sans,Roboto,Arial,sans-serif;font-size:.875rem;font-weight:500;letter-spacing:0;line-height:1.25rem;color:var(--gm3-sys-color-primary,#0b57d0)}.waffleDialogRitzImportDialogSuccessDialogText{font-family:Google Sans,Roboto,Arial,sans-serif;font-size:.875rem;font-weight:400;letter-spacing:0;line-height:1.25rem;color:var(--gm3-sys-color-on-surface,#1f1f1f);text-align:center;margin:0 45px;width:344px;height:64px}.waffleDialogRitzImportDialogErrorDialogContent{font-family:Google Sans,Roboto,Arial,sans-serif;font-size:.875rem;font-weight:400;letter-spacing:0;line-height:1.25rem;color:var(--gm3-sys-color-on-surface-variant,#444746);display:flex;flex-direction:column;gap:20px}.waffleDialogRitzImportDialogErrorDialogT

...[TRUNCATED]...

```

## File: `generators/__init__.py`
```text

```

## File: `generators/builder_generators.py`
```text
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

    for f 

...[TRUNCATED]...

```

## File: `generators/import_from_html.py`
```text
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup


def _extract_css_property(style: str, prop: str) -> Optional[str]:
    parts = [p.strip() for p in style.split(";") if p.strip()]
    for part in parts:
        if ":" not in part:
            continue
        key, value = part.split(":", 1)
        if key.strip().lower() == prop.strip().lower():
            return value.strip()
    return None


def _cell_text(td) -> str:
    return td.get_text(separator=" ", strip=True)


def _find_main_table(soup: BeautifulSoup):
    return soup.find("table", class_="waffle") or soup.find("table")


def _extract_headers_and_rows(table) -> tuple[list[str], list[list[str]], list]:
    body = table.find("tbody")
    if body is None:
        return [], [], []

    trs = body.find_all("tr")
    if not trs:
        return [], [], []

    first_row_tds = trs[0].find_all("td")
    headers = [_cell_text(td) for td in first_row_tds]

    data_rows: List[List[str]] = []
    raw_rows = []

    for tr in trs[1:]:
        tds = tr.find_all("td")
        values = [_cell_text(td) for td in tds]
        data_rows.append(values)
        raw_rows.append(tds)

    return headers, data_rows, raw_rows


def _extract_enum_styles_for_column(
    raw_rows: List,
    headers: List[str],
    enum_field_name: str,
) -> Dict[str, Dict[str, str]]:
    result: Dict[str, Dict[str, str]] = {}

    if enum_field_name not in headers:
        return result

    idx = headers.index(enum_field_name)

    for row_tds in raw_rows:
        if len(row_tds) <= idx:
            continue

        td = row_tds[idx]
        span = td.find("span")
        if span is None:
            continue

        value = span.get_text(strip=True)
        value = value.replace("\u200b", "").strip()

        if not value:
            continue

        style = span.get("style", "")
        bg = _extract_css_property(style, "background-color")
        fg = _extract_css_property(style, "color")

        if bg or fg:
            result[value] = {
                "bg": bg or "",
                "fg": fg or "",
            }

    return result


def _extract_side_column_enum_candidates(
    headers: List[str],
    data_rows: List[List[str]],
) -> List[str]:
    """
    Heuristica semplice:
    cerca una colonna oltre gli header principali con pochi valori testuali unici.
    """
    if not data_rows:
        return []

    max_cols = max(len(r) for r in data_rows)
    header_len = len(headers)

    for col_idx in range(header_len, max_cols):
        seen: List[str] = []

        for row in data_rows:
            if len(row) <= col_idx:
                continue

            v = row[col_idx].strip()
            if not v:
                continue

            if v not in seen:
                seen.append(v)

        if 2 <= len(seen) <= 20:
            return seen

    return []


def import_visuals_from_html(
    html_path: str | Path,
    enum_field_name: str = "rating",
    debug: bool = False,
) -> Dict[str, Any]:
    html_path = Path(html_path)
    html_text = html_path.read_text(encoding="utf-8", errors="ignore")

    soup = BeautifulSoup(html_text, "html.parser")
    table = _find_main_table(soup)
    if table is None:
        raise ValueError("No HTML table found")

    headers, data_rows, raw_rows = _extract_headers_and_rows(table)
    if not headers:
        raise ValueError("No headers found in HTML table")

    enum_styles = _extract_enum_styles_for_column(raw_rows, headers, enum_field_name)
    enum_values_from_html = _extract_side_column_enum_candidates(headers, data_rows)

    if debug:
        print("HTML headers:", headers)
        print("HTML enum styles:", enum_styles)
        print("HTML enum values from side column:", enum_values_from_html)

    return {
        "headers": headers,
        "enumStyles": {
            enum_field_name: enum_styles
        } if enum_styles else {},
        "enumValuesFromHtml": {
            enum_field_name: enum_values_from_html
        } if enum_values_from_html else {},
    }
```

## File: `generators/import_from_sheet.py`
```text
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation


def _norm_header(value: Any) -> str:
    return str(value or "").strip().lower()


def _guess_type_from_sample(value: Any) -> str:
    if value is None or value == "":
        return "string"

    if isinstance(value, bool):
        return "string"

    if isinstance(value, int):
        return "int"

    if isinstance(value, float):
        if value.is_integer():
            return "int"
        return "string"

    cls_name = value.__class__.__name__.lower()
    if "date" in cls_name or "datetime" in cls_name:
        return "date"

    s = str(value).strip()
    s_lower = s.lower()

    if s_lower.startswith("http://") or s_lower.startswith("https://") or s_lower.startswith("www."):
        return "string"

    if s.isdigit():
        return "int"

    slash_parts = s.split("/")
    dash_parts = s.split("-")

    if len(slash_parts) == 3 and all(part.strip().isdigit() for part in slash_parts):
        return "date"

    if len(dash_parts) == 3 and all(part.strip().isdigit() for part in dash_parts):
        return "date"

    return "string"


def _cell_in_same_data_column(cell_range: str, col_letter: str) -> bool:
    try:
        parts = cell_range.split(":")
        start = parts[0]
        end = parts[-1]

        start_letters = "".join(ch for ch in start if ch.isalpha()).upper()
        end_letters = "".join(ch for ch in end if ch.isalpha()).upper()

        if not start_letters:
            return False
        if not end_letters:
            end_letters = start_letters

        return start_letters <= col_letter <= end_letters
    except Exception:
        return False


def _read_values_from_range_ref(workbook, ref: str, debug: bool = False) -> List[str]:
    if debug:
        print("READ RANGE REF =", ref)

    if "!" in ref:
        sheet_name, range_ref = ref.split("!", 1)
        sheet_name = sheet_name.strip("'")
        ws = workbook[sheet_name]
    else:
        ws = workbook.active
        range_ref = ref

    values: List[str] = []
    for row in ws[range_ref]:
        for cell in row:
            if cell.value is not None and str(cell.value).strip():
                values.append(str(cell.value).strip())
    return values


def _extract_enum_from_validation(
    workbook,
    ws,
    col_idx: int,
    sample_row: int,
    debug: bool = False,
) -> List[str]:
    col_letter = get_column_letter(col_idx)
    target_coord = f"{col_letter}{sample_row}"

    if debug:
        print(f"\n--- DEBUG ENUM COLONNA {col_letter} ({target_coord}) ---")
        print(f"Tot dataValidations: {len(ws.data_validations.dataValidation)}")

    for dv in ws.data_validations.dataValidation:
        if not isinstance(dv, DataValidation):
            continue

        if debug:
            print("type =", dv.type, "| formula1 =", dv.formula1, "| sqref =", dv.sqref)

        if dv.type != "list":
            continue

        applies = False

        for rng in str(dv.sqref).split():
            if _cell_in_same_data_column(rng, col_letter):
                applies = True
                break

        if not applies:
            try:
                if target_coord in dv.cells:
                    applies = True
            except Exception:
                pass

        if not applies:
            continue

        formula1 = dv.formula1
        if not formula1:
            continue

        formula1 = str(formula1).strip()

        if debug:
            print("MATCH validation list on column", col_letter)
            print("formula1 raw =", formula1)

        if formula1.startswith('"') and formula1.endswith('"'):
            raw = formula1[1:-1]
            values = [x.strip() for x in raw.split(",") if x.strip()]
            if debug:
                print("enum explicit =", values)
            return values

        ref = formula1[1:] if formula1.startswith("=") else formula1

        if "!" in ref or "$" in ref or ":" in ref:
            try:
                values = _read_values_from_range_ref(workbook, ref, debug=debug)
                if debug:
                    print("enum from range =", values)
                return values
            except Exception as exc:
                if debug:
                    print("range parse failed:", exc)
                return []

    if debug:
        print("No enum validation found for column", col_letter)

    return []


def _is_formula_cell(cell) -> bool:
    return isinstance(cell.value, str) and cell.value.startswith("=")


def _build_field_def(
    name: str,
    sample_value: Any,
    has_formula: bool,
    formula_source: str | None,
    formula_anchor_row: int | None,
    enum_values: List[str],
) -> Dict[str, Any]:
    base = {
        "name": name,
        "required": False,
        "visibleInViewer": True,
        "enumValues": enum_values or [],
        "locked": False,
        "formulaSource": None,
        "formulaAnchorRow": None,
        "formulaMode": None,
        "enumStyles": {},
    }

    if name == "id":
        return {
            **base,
            "type": "int",
            "computed": True,
            "visibleInForm": False,
            "locked": True,
        }

    if has_formula:
        return {
            **base,
            "type": "computed",
            "computed": True,
            "visibleInForm": False,
            "locked": True,
            "formulaSource": formula_source,
            "formulaAnchorRow": formula_anchor_row,
            "formulaMode": "incremental_copy",
        }

    field_type = "enum" if enum_values else _guess_type_from_sample(sample_value)

    return {
        **base,
        "type": field_type,
        "computed": False,
        "visibleInForm": True,
    }


def _build_constraint(field: Dict[str, Any]) -> Dict[str, An

...[TRUNCATED]...

```

## File: `generators/merge_schema.py`
```text
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List


def _merge_unique(*lists: List[str]) -> List[str]:
    out: List[str] = []
    for seq in lists:
        for v in seq:
            if v and v not in out:
                out.append(v)
    return out


def merge_schema_with_visuals(
    sheet_schema: Dict[str, Any],
    html_visuals: Dict[str, Any],
) -> Dict[str, Any]:
    merged = deepcopy(sheet_schema)

    merged.setdefault("enums", {})
    merged.setdefault("enumStyles", {})

    html_enums = html_visuals.get("enumValuesFromHtml", {})
    html_styles = html_visuals.get("enumStyles", {})

    field_names = set(list(html_enums.keys()) + list(html_styles.keys()))

    for field_name in field_names:
        xlsx_values = list(merged.get("enums", {}).get(field_name, []))
        html_values = list(html_enums.get(field_name, []))
        style_values = list(html_styles.get(field_name, {}).keys())

        final_values = _merge_unique(xlsx_values, html_values, style_values)

        if final_values:
            merged["enums"][field_name] = final_values

            for f in merged.get("fields", []):
                if f.get("name") == field_name:
                    f["type"] = "enum"
                    f["enumValues"] = final_values

            if field_name in merged.get("constraints", {}):
                merged["constraints"][field_name]["type"] = "enum"

        styles_for_field = html_styles.get(field_name, {})
        if styles_for_field:
            merged["enumStyles"][field_name] = styles_for_field

        for f in merged.get("fields", []):
            if f.get("name") == field_name:
                f.setdefault("enumStyles", {})
                if styles_for_field:
                    f["enumStyles"] = styles_for_field

    for f in merged.get("fields", []):
        f.setdefault("enumStyles", {})
        f.setdefault("formulaSource", None)
        f.setdefault("formulaAnchorRow", None)
        f.setdefault("formulaMode", None)

    return merged
```

## File: `generators/rollback_to_commit.sh`
```text
#!/usr/bin/env bash
set -e

if [ -z "$1" ]; then
  echo "Usage: ./rollback_to_commit.sh <commit-hash>"
  exit 1
fi

TARGET="$1"

echo "=== Creating rollback branch from current state ==="
git status
read -p "Continue rollback to $TARGET? Type YES: " CONFIRM

if [ "$CONFIRM" != "YES" ]; then
  echo "Aborted."
  exit 1
fi

echo "=== Reset local working tree to target commit ==="
git reset --hard "$TARGET"

echo "=== Rebuild generated demo files ==="
python pipeline/build_all_from_input.py examples/case_001
python tools/publish_to_docs.py

echo "=== Commit rollback state ==="
git add .
git commit -m "Rollback to stable state $TARGET" || true

echo "=== Push to GitHub ==="
git push origin main --force-with-lease

echo "=== Sync Hetzner ==="
ssh root@65.21.176.227 <<'EOF'
set -e
cd /opt/sheets.builder
git fetch origin
git reset --hard origin/main
source venv/bin/activate
pip install -r requirements.txt
systemctl restart sheets-builder
systemctl status sheets-builder --no-pager
curl -s https://builder.sgbh.org/health
EOF

echo "=== Rollback published successfully ==="
```

## File: `generators/schema_validators.py`
```text
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
    enum_styles_top = fields_schema.get("enumStyles", {})

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

    if not isinstance(enum_styles_top, dict):
        errors.append("'enumStyles' must be an object/dict.")

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

    field_names: List[str] = []
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
            errors.append(f"Field '{name}' has invalid 'enumStyles' (must be dict or null).")
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
            errors.append(f"Field '{fname}' is defined but missing from headers."

...[TRUNCATED]...

```

## File: `index.html`
```text
<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>HorrorAtlas — v1</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 1100px; margin: 28px auto; padding: 0 16px; }
    h1 { margin: 0 0 6px; }
    .muted { color:#666; }
    .card { border:1px solid #e5e5e5; border-radius:10px; padding:14px; background:#fafafa; margin:12px 0; }
    label { display:block; margin:10px 0 6px; font-weight:700; }
    input, select { width:100%; padding:9px; border:1px solid #ccc; border-radius:8px; box-sizing:border-box; background:#fff; }
    button { padding:9px 12px; border:0; border-radius:8px; background:#111; color:#fff; cursor:pointer; font-weight:800; }
    button.secondary { background:#666; }
    button:disabled { opacity:.6; cursor:not-allowed; }
    .row { display:grid; grid-template-columns: 1fr 1fr; gap:12px; }
    .actions { display:flex; gap:10px; align-items:center; flex-wrap:wrap; margin-top:12px; }
    .ok { color:#0a6; font-weight:800; }
    .err { color:#b00; font-weight:800; }
    iframe { width:100%; height:560px; border:1px solid #ddd; border-radius:10px; background:#fff; }
    small { display:block; margin-top:8px; color:#666; }
    pre { background:#0b0b0b; color:#d6ffd6; border-radius:10px; padding:12px; overflow:auto; }
  </style>
</head>
<body>

  <h1>HorrorAtlas <span class="muted">— v1</span></h1>
  <p class="muted">
    Backend: Google Apps Script (JSONP) → tab <b>HorrorMovie</b>.
    <br>Read: pubblico. Write: protetto da <code>apiKey</code>.
  </p>

  <div class="card">
    <h3 style="margin:0 0 10px;">Config</h3>

    <label for="apiKey">apiKey (solo insert/update/delete/getById)</label>
    <input id="apiKey" type="password" autocomplete="off" spellcheck="false"
           placeholder="CHANGE_ME_WRITE_KEY_2026" />

    <div class="actions">
      <button id="pingBtn" type="button">meta</button>
      <button id="schemaBtn" type="button" class="secondary">schema</button>
      <span id="cfgStatus" class="muted"></span>
    </div>

    <small>Tip: fai prima <b>schema</b>, poi inserisci 1 record, poi controlla nel viewer.</small>
  </div>

  <div class="card">
    <h3 style="margin:0 0 10px;">Insert (new movie)</h3>

    <div class="row">
      <div>
        <label for="year">year <span class="muted">(required)</span></label>
        <input id="year" type="number" min="1890" max="2100" placeholder="1981" />
      </div>
      <div>
        <label for="nation">nation <span class="muted">(optional)</span></label>
        <input id="nation" placeholder="USA" />
      </div>
    </div>

    <label for="title">Title <span class="muted">(required)</span></label>
    <input id="title" placeholder="Psycho" />

    <label for="url">url <span class="muted">(optional)</span></label>
    <input id="url" placeholder="https://en.wikipedia.org/wiki/Psycho_(1960_film)" />

    <label for="rating">rating <span class="muted">(optional)</span></label>
    <select id="rating">
      <option value="" selected>—</option>
      <option>Pessimo</option>
      <option>Mediocre</option>
      <option>Medio</option>
      <option>Buono</option>
      <option>Ottimo</option>
      <option>Capolavoro</option>
    </select>

    <div class="actions">
      <button id="insertBtn" type="button">Insert</button>
      <span id="insertStatus" class="muted"></span>
    </div>
  </div>

  <div class="card">
    <h3 style="margin:0 0 10px;">CRUD by id</h3>
    <div class="row">
      <div>
        <label for="id">id</label>
        <input id="id" type="number" min="1" step="1" placeholder="1" />
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

    <small class="muted">
      update riscrive year/title/url/nation/rating e rigenera <b>link</b> (se url presente).
    </small>
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
  // ===== CONFIG FISSA =====
  const WEB_APP_URL = "https://script.google.com/macros/s/AKfycbzmP0437k6Mo5ebcAv3N2Kdx_ZG0IqCVnO3x28YKSrBJ2EclnShUgHJJ1s2NH2od0FQ/exec";

  function setMsg(el, msg, cls) {
    el.className = cls || "muted";
    el.textContent = msg;
  }

  function makeCbName() {
    return "cb_" + Date.now() + "_" + Math.floor(Math.random() * 1e6);
  }

  function jsonp(url) {
    return new Promise((resolve, reject) => {
      const cbName = makeCbName();
      const script = document.createElement("script");

      const t = setTimeout(() => {
        cleanup();
        reject(new Error("Timeout JSONP"));
      }, 15000);

      function cleanup() {
        clearTimeout(t);
        try { delete window[cbName]; } catch (_) { window[cbName] = undefined; }
        script.remove();
      }

      window[cbName] = (data) => {
        cleanup();
        resolve(data);
      };

      const u = new URL(url);
      u.searchParams.set("cb", cbName);
      u.searchParams.set("_", Date.now().toString());

      script.src = u.toString();
      script.onerror = () => {
        cleanup();
        reject(new Error("JSONP load error (check /exec + access)"));
      };

      document.body.appendChild(script);
    });
  }

  function baseUrl_() {
    return WEB_APP_URL;
  }

  function apiKey_() {
    return document.getElementById("apiKey").value.tri

...[TRUNCATED]...

```

## File: `output/current/builder_state.json`
```text
{
  "project": {
    "projectName": "Generated App",
    "projectSlug": "generated-app",
    "backendName": "generated-app-backend",
    "entityName": "Item",
    "entityLabelLower": "item",
    "sheetName": "Sheet1",
    "buildMarker": "GENERATED_APP_BACKEND_V1",
    "adminPassword": "CHANGE_ME_WRITE_KEY_2026"
  },
  "fields": [
    {
      "name": "id",
      "originalHeader": "id",
      "label": "id",
      "type": "int",
      "required": false,
      "computed": true,
      "visibleInForm": false,
      "visibleInViewer": true,
      "locked": true,
      "enumValues": []
    },
    {
      "name": "year",
      "originalHeader": "year",
      "label": "year",
      "type": "int",
      "required": false,
      "computed": false,
      "visibleInForm": true,
      "visibleInViewer": true,
      "locked": false,
      "enumValues": []
    },
    {
      "name": "title",
      "originalHeader": "Title",
      "label": "Title",
      "type": "string",
      "required": false,
      "computed": false,
      "visibleInForm": true,
      "visibleInViewer": true,
      "locked": false,
      "enumValues": []
    },
    {
      "name": "url",
      "originalHeader": "url",
      "label": "url",
      "type": "string",
      "required": false,
      "computed": false,
      "visibleInForm": true,
      "visibleInViewer": true,
      "locked": false,
      "enumValues": []
    },
    {
      "name": "link",
      "originalHeader": "link",
      "label": "link",
      "type": "computed",
      "required": false,
      "computed": true,
      "visibleInForm": false,
      "visibleInViewer": true,
      "locked": true,
      "enumValues": [],
      "formulaSource": "=HYPERLINK(D2:D987, C2:C987)",
      "formulaAnchorRow": 2,
      "formulaMode": "incremental_copy"
    },
    {
      "name": "nation",
      "originalHeader": "nation",
      "label": "nation",
      "type": "string",
      "required": false,
      "computed": false,
      "visibleInForm": true,
      "visibleInViewer": true,
      "locked": false,
      "enumValues": []
    },
    {
      "name": "rating",
      "originalHeader": "rating",
      "label": "rating",
      "type": "enum",
      "required": false,
      "computed": false,
      "visibleInForm": true,
      "visibleInViewer": true,
      "locked": false,
      "enumValues": [
        "Mediocre",
        "Medio",
        "Buono",
        "Ottimo",
        "Capolavoro",
        "Pessimo"
      ],
      "enumStyles": {
        "Capolavoro": {
          "bg": "#215a6c",
          "fg": "#c6dbe1"
        },
        "Ottimo": {
          "bg": "#d4edbc",
          "fg": "#11734b"
        },
        "Buono": {
          "bg": "#ffe5a0",
          "fg": "#473821"
        },
        "Medio": {
          "bg": "#ffc8aa",
          "fg": "#753800"
        },
        "Mediocre": {
          "bg": "#ffcfc9",
          "fg": "#b10202"
        },
        "Pessimo": {
          "bg": "#e8eaed",
          "fg": "#000000"
        }
      }
    }
  ],
  "constraints": {
    "id": {
      "type": "int",
      "required": false,
      "min": 0
    },
    "year": {
      "type": "int",
      "required": false,
      "min": 0
    },
    "title": {
      "type": "string",
      "required": false,
      "maxLen": 255
    },
    "url": {
      "type": "string",
      "required": false,
      "maxLen": 255
    },
    "link": {
      "type": "computed",
      "required": false
    },
    "nation": {
      "type": "string",
      "required": false,
      "maxLen": 255
    },
    "rating": {
      "type": "enum",
      "required": false
    }
  },
  "enums": {
    "rating": [
      "Mediocre",
      "Medio",
      "Buono",
      "Ottimo",
      "Capolavoro",
      "Pessimo"
    ]
  },
  "enumStyles": {
    "rating": {
      "Capolavoro": {
        "bg": "#215a6c",
        "fg": "#c6dbe1"
      },
      "Ottimo": {
        "bg": "#d4edbc",
        "fg": "#11734b"
      },
      "Buono": {
        "bg": "#ffe5a0",
        "fg": "#473821"
      },
      "Medio": {
        "bg": "#ffc8aa",
        "fg": "#753800"
      },
      "Mediocre": {
        "bg": "#ffcfc9",
        "fg": "#b10202"
      },
      "Pessimo": {
        "bg": "#e8eaed",
        "fg": "#000000"
      }
    }
  },
  "lists": {
    "headers": [
      "id",
      "year",
      "title",
      "url",
      "link",
      "nation",
      "rating"
    ],
    "requiredOnInsert": [],
    "optionalOnInsert": [
      "year",
      "title",
      "url",
      "nation",
      "rating"
    ],
    "computed": [
      "id",
      "link"
    ],
    "visibleInForm": [
      "year",
      "title",
      "url",
      "nation",
      "rating"
    ],
    "visibleInViewer": [
      "id",
      "year",
      "title",
      "url",
      "link",
      "nation",
      "rating"
    ]
  },
  "options": {}
}
```

## File: `output/current/deploy.manifest.json`
```text
{
  "projectName": "Generated App",
  "projectSlug": "generated-app",
  "backendName": "generated-app-backend",
  "sheetName": "Sheet1",
  "generatedFiles": [
    "codice.gs",
    "docs/index.html",
    "docs/viewer.html"
  ],
  "sourceOfTruth": "builder_state.json"
}
```

## File: `output/current/docs/index.html`
```text
<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Generated App</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 1100px; margin: 28px auto; padding: 0 16px; }
    h1 { margin: 0 0 6px; }
    .muted { color:#666; }
    .card { border:1px solid #e5e5e5; border-radius:10px; padding:14px; background:#fafafa; margin:12px 0; }
    label { display:block; margin:10px 0 6px; font-weight:700; }
    input, select { width:100%; padding:9px; border:1px solid #ccc; border-radius:8px; box-sizing:border-box; background:#fff; }
    button { padding:9px 12px; border:0; border-radius:8px; background:#111; color:#fff; cursor:pointer; font-weight:800; }
    button.secondary { background:#666; }
    button:disabled { opacity:.6; cursor:not-allowed; }
    .row { display:grid; grid-template-columns: 1fr 1fr; gap:12px; }
    .actions { display:flex; gap:10px; align-items:center; flex-wrap:wrap; margin-top:12px; }
    .ok { color:#0a6; font-weight:800; }
    .err { color:#b00; font-weight:800; }
    iframe { width:100%; height:560px; border:1px solid #ddd; border-radius:10px; background:#fff; }
    small { display:block; margin-top:8px; color:#666; }
    pre { background:#0b0b0b; color:#d6ffd6; border-radius:10px; padding:12px; overflow:auto; }
  </style>
</head>
<body>

  <h1>Generated App database</h1>

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

    <small>Slug app: <code>generated-app</code></small>
  </div>

  <div class="card">
    <h3 style="margin:0 0 10px;">Insert (Item)</h3>


    <label for="year">year <span class="muted">(optional)</span></label>
    <input id="year" type="number" min="0" placeholder="year" />


    <label for="title">Title <span class="muted">(optional)</span></label>
    <input id="title" placeholder="Title" />


    <label for="url">url <span class="muted">(optional)</span></label>
    <input id="url" placeholder="url" />


    <label for="nation">nation <span class="muted">(optional)</span></label>
    <input id="nation" placeholder="nation" />


    <label for="rating">rating <span class="muted">(optional)</span></label>
    <select id="rating">
      <option value="" selected>—</option><option>Mediocre</option><option>Medio</option><option>Buono</option><option>Ottimo</option><option>Capolavoro</option><option>Pessimo</option>
    </select>

    <div class="actions">
      <button id="insertBtn" type="button">Insert</button>
      <span id="insertStatus" class="muted"></span>
    </div>
  </div>

  <div class="card">
    <h3 style="margin:0 0 10px;">Find, update or delete an existing record</h3>
      <p class="muted">
    Enter a record id, load the record into the form, then update or delete it.
      </p>
    <div class="row">
      <div>
        <label for="crud_id">id</label>
        <input id="crud_id" type="number" min="1" step="1" placeholder="1" />
      </div>
      <div>
        <label>&nbsp;</label>
        <div class="actions" style="margin-top:0;">
          <button id="getBtn" type="button" class="secondary">Load record</button>
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
  const APP_SLUG = qs.get("app") || "generated-app";

  function setMsg(el, msg, cls) {
    el.className = cls || "muted";
    el.textContent = msg;
  }


    async function apiCall_(mode, params = {}) {
    let url = `/api/apps/${APP_SLUG}/${mode}`;

    const qs = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      qs.set(k, String(v ?? ""));
    });

    const query = qs.toString();
    if (query) url += "?" + query;

    const resp = await fetch(url);
    const data = await resp.json();

    if (!resp.ok) {
      throw new Error(data.error || `HTTP ${resp.status}`);
    }

    return data;
  }

    function apiUrl_(mode) {
    return `/api/apps/${APP_SLUG}/${mode}`;
  }

  async function apiCall_(mode, params = {}, method = "GET") {
    let url = apiUrl_(mode);

    const options = {
      method,
      headers: {}
    };

    if (method === "GET") {
      const qs = new URLSearchParams();
      Object.entries(params).forEach(([k, v]) => {
        qs.set(k, String(v ?? ""));
      });

      const query = qs.toString();
      if (query) url += "?" + query;
    } else {
      options.headers["Content-Type"] = "application/json";
      optio

...[TRUNCATED]...

```

## File: `output/current/docs/viewer.html`
```text
<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Item Viewer</title>
  <link href="https://cdn.jsdelivr.net/npm/tabulator-tables@6.4.0/dist/css/tabulator.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/tabulator-tables@6.4.0/dist/js/tabulator.min.js"></script>
  <style>
    body { font-family: Arial, sans-serif; margin: 12px; }
    .muted { color:#666; }
    .toolbar { display:flex; gap:10px; align-items:end; flex-wrap:wrap; margin: 8px 0 12px; }
    .toolbar label { display:block; font-size:12px; font-weight:700; color:#444; margin-bottom:4px; }
    .toolbar input, .toolbar select {
      padding:8px;
      border:1px solid #ccc;
      border-radius:8px;
      background:#fff;
      min-width:180px;
    }

    table { border-collapse: collapse; width: 100%; }
    th, td {
      border:1px solid #e5e5e5;
      padding:8px;
      font-size: 13px;
      vertical-align: top;
      overflow-wrap:anywhere;
      white-space: pre-wrap;
    }

    thead th {
      position: sticky;
      top: 0;
      z-index: 2;
      background: #2f3b52;
      color: #fff;
      font-weight: 800;
    }

    tbody tr:nth-child(even){ background:#f6f8fb; }
    tbody tr:nth-child(odd){ background:#ffffff; }

    tbody tr.first-row {
      background: #fff3cd !important;
      outline: 2px solid #ffe69c;
      outline-offset: -2px;
    }
  </style>
</head>
<body>

  <div class="muted">Viewer read-only — tab <b>Sheet1</b></div>

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
  const APP_SLUG = qs.get("app") || "generated-app";
  const URL_LIMIT = qs.get("limit") || "50";
  const EMBEDDED_MODE = qs.get("embedded") === "1";

  const VISIBLE_HEADERS = [
  "id",
  "year",
  "title",
  "url",
  "link",
  "nation",
  "rating"
];
  const ENUMS = {
  "rating": [
    "Mediocre",
    "Medio",
    "Buono",
    "Ottimo",
    "Capolavoro",
    "Pessimo"
  ]
};
  const LABELS = {
  "id": "id",
  "year": "year",
  "title": "Title",
  "url": "url",
  "link": "link",
  "nation": "nation",
  "rating": "rating"
};
  const ENUM_STYLES = {
  "rating": {
    "Capolavoro": {
      "bg": "#215a6c",
      "fg": "#c6dbe1"
    },
    "Ottimo": {
      "bg": "#d4edbc",
      "fg": "#11734b"
    },
    "Buono": {
      "bg": "#ffe5a0",
      "fg": "#473821"
    },
    "Medio": {
      "bg": "#ffc8aa",
      "fg": "#753800"
    },
    "Mediocre": {
      "bg": "#ffcfc9",
      "fg": "#b10202"
    },
    "Pessimo": {
      "bg": "#e8eaed",
      "fg": "#000000"
    }
  }
};

    async function apiCall_(mode, params = {}) {
    let url = `/api/apps/${APP_SLUG}/${mode}`;

    const qs = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      qs.set(k, String(v ?? ""));
    });

    const query = qs.toString();
    if (query) url += "?" + query;

    const resp = await fetch(url);
    const data = await resp.json();

    if (!resp.ok) {
      throw new Error(data.error || `HTTP ${resp.status}`);
    }

    return data;
  }

  function esc(s) {
    return String(s ?? "").replace(/[&<>"']/g, c => (
      {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]
    ));
  }

  function styleAttrForEnum(headerName, value) {
    const fieldStyles = ENUM_STYLES[headerName];
    if (!fieldStyles) return "";
    const styleDef = fieldStyles[String(value ?? "").trim()];
    if (!styleDef) return "";

    const parts = [];
    if (styleDef.bg) parts.push(`background:${styleDef.bg}`);
    if (styleDef.fg) parts.push(`color:${styleDef.fg}`);
    if (!parts.length) return "";

    parts.push("font-weight:700");
    parts.push("text-align:center");
    return parts.join("; ");
  }

  let LAST_HEADERS = [];
  let LAST_ROWS = [];

    let DATA_TABLE = null;

  function rowsToObjects(headers, rows) {
    return rows.map(row => {
      const obj = {};

      headers.forEach((h, i) => {
        obj[h] = row[i];
      });

      return obj;
    });
  }

  function buildColumns(headers) {
    return headers
      .filter(h => VISIBLE_HEADERS.includes(h))
      .map(h => {
        return {
          title: LABELS[h] || h,
          field: h,
          headerFilter: "input",
          sorter: "string",
          resizable: true,
          formatter: function(cell) {
            const value = cell.getValue();
            const style = styleAttrForEnum(h, value);

            if (style) {
              const el = cell.getElement();

              style.split(";").forEach(rule => {
                const parts = rule.split(":");

                if (parts.length === 2) {
                  el.style[parts[0].trim()] = parts[1].trim();
                }
              });
            }

            return esc(value);
          }
        };
      });
  }

  function renderTable() {
    const status = document.getElementById("status");
    const search = document.getElementById("searchBox").value.trim().toLowerCase();

    if (!LAST_HEADERS.length) {
      status.textContent = "No data loaded";
      return;
    }

    const visibleHeaders = LAST_HEADERS.filter(h => VISIBLE_HEADERS.includes(h));

    const visibleIndexes = LAST_HEADERS
      .map((h, i) => (visibleHeaders.includes(h) ? i : -1))
      .filter(i => i >= 0);

    let rows = LAST_ROWS.slice();

    if (search) {
      rows = rows.filter(r =>
        visibleIndexes.some(i =>
          String(r[i] ?? "").toLowerCase().includes(search)
        )
      );
   

...[TRUNCATED]...

```

## File: `output/current/fields.schema.json`
```text
{
  "headers": [
    "id",
    "year",
    "title",
    "url",
    "link",
    "nation",
    "rating"
  ],
  "requiredOnInsert": [],
  "optionalOnInsert": [
    "year",
    "title",
    "url",
    "nation",
    "rating"
  ],
  "computed": [
    "id",
    "link"
  ],
  "visibleInForm": [
    "year",
    "title",
    "url",
    "nation",
    "rating"
  ],
  "visibleInViewer": [
    "id",
    "year",
    "title",
    "url",
    "link",
    "nation",
    "rating"
  ],
  "enums": {
    "rating": [
      "Mediocre",
      "Medio",
      "Buono",
      "Ottimo",
      "Capolavoro",
      "Pessimo"
    ]
  },
  "constraints": {
    "id": {
      "type": "int",
      "required": false,
      "min": 0
    },
    "year": {
      "type": "int",
      "required": false,
      "min": 0
    },
    "title": {
      "type": "string",
      "required": false,
      "maxLen": 255
    },
    "url": {
      "type": "string",
      "required": false,
      "maxLen": 255
    },
    "link": {
      "type": "computed",
      "required": false
    },
    "nation": {
      "type": "string",
      "required": false,
      "maxLen": 255
    },
    "rating": {
      "type": "enum",
      "required": false
    }
  },
  "fields": [
    {
      "name": "id",
      "originalHeader": "id",
      "label": "id",
      "type": "int",
      "required": false,
      "computed": true,
      "visibleInForm": false,
      "visibleInViewer": true,
      "locked": true,
      "enumValues": []
    },
    {
      "name": "year",
      "originalHeader": "year",
      "label": "year",
      "type": "int",
      "required": false,
      "computed": false,
      "visibleInForm": true,
      "visibleInViewer": true,
      "locked": false,
      "enumValues": []
    },
    {
      "name": "title",
      "originalHeader": "Title",
      "label": "Title",
      "type": "string",
      "required": false,
      "computed": false,
      "visibleInForm": true,
      "visibleInViewer": true,
      "locked": false,
      "enumValues": []
    },
    {
      "name": "url",
      "originalHeader": "url",
      "label": "url",
      "type": "string",
      "required": false,
      "computed": false,
      "visibleInForm": true,
      "visibleInViewer": true,
      "locked": false,
      "enumValues": []
    },
    {
      "name": "link",
      "originalHeader": "link",
      "label": "link",
      "type": "computed",
      "required": false,
      "computed": true,
      "visibleInForm": false,
      "visibleInViewer": true,
      "locked": true,
      "enumValues": [],
      "formulaSource": "=HYPERLINK(D2:D987, C2:C987)",
      "formulaAnchorRow": 2,
      "formulaMode": "incremental_copy"
    },
    {
      "name": "nation",
      "originalHeader": "nation",
      "label": "nation",
      "type": "string",
      "required": false,
      "computed": false,
      "visibleInForm": true,
      "visibleInViewer": true,
      "locked": false,
      "enumValues": []
    },
    {
      "name": "rating",
      "originalHeader": "rating",
      "label": "rating",
      "type": "enum",
      "required": false,
      "computed": false,
      "visibleInForm": true,
      "visibleInViewer": true,
      "locked": false,
      "enumValues": [
        "Mediocre",
        "Medio",
        "Buono",
        "Ottimo",
        "Capolavoro",
        "Pessimo"
      ],
      "enumStyles": {
        "Capolavoro": {
          "bg": "#215a6c",
          "fg": "#c6dbe1"
        },
        "Ottimo": {
          "bg": "#d4edbc",
          "fg": "#11734b"
        },
        "Buono": {
          "bg": "#ffe5a0",
          "fg": "#473821"
        },
        "Medio": {
          "bg": "#ffc8aa",
          "fg": "#753800"
        },
        "Mediocre": {
          "bg": "#ffcfc9",
          "fg": "#b10202"
        },
        "Pessimo": {
          "bg": "#e8eaed",
          "fg": "#000000"
        }
      }
    }
  ],
  "enumStyles": {
    "rating": {
      "Capolavoro": {
        "bg": "#215a6c",
        "fg": "#c6dbe1"
      },
      "Ottimo": {
        "bg": "#d4edbc",
        "fg": "#11734b"
      },
      "Buono": {
        "bg": "#ffe5a0",
        "fg": "#473821"
      },
      "Medio": {
        "bg": "#ffc8aa",
        "fg": "#753800"
      },
      "Mediocre": {
        "bg": "#ffcfc9",
        "fg": "#b10202"
      },
      "Pessimo": {
        "bg": "#e8eaed",
        "fg": "#000000"
      }
    }
  }
}
```

## File: `output/current/parsed.schema.json`
```text
{
  "headers": [
    "id",
    "year",
    "title",
    "url",
    "link",
    "nation",
    "rating"
  ],
  "requiredOnInsert": [],
  "optionalOnInsert": [
    "year",
    "title",
    "url",
    "nation",
    "rating"
  ],
  "computed": [
    "id",
    "link"
  ],
  "visibleInForm": [
    "year",
    "title",
    "url",
    "nation",
    "rating"
  ],
  "visibleInViewer": [
    "id",
    "year",
    "title",
    "url",
    "link",
    "nation",
    "rating"
  ],
  "enums": {
    "rating": [
      "Mediocre",
      "Medio",
      "Buono",
      "Ottimo",
      "Capolavoro",
      "Pessimo"
    ]
  },
  "constraints": {
    "id": {
      "type": "int",
      "required": false,
      "min": 0
    },
    "year": {
      "type": "int",
      "required": false,
      "min": 0
    },
    "title": {
      "type": "string",
      "required": false,
      "maxLen": 255
    },
    "url": {
      "type": "string",
      "required": false,
      "maxLen": 255
    },
    "link": {
      "type": "computed",
      "required": false
    },
    "nation": {
      "type": "string",
      "required": false,
      "maxLen": 255
    },
    "rating": {
      "type": "enum",
      "required": false
    }
  },
  "fields": [
    {
      "name": "id",
      "required": false,
      "visibleInViewer": true,
      "enumValues": [],
      "locked": true,
      "formulaSource": null,
      "formulaAnchorRow": null,
      "formulaMode": null,
      "enumStyles": {},
      "type": "int",
      "computed": true,
      "visibleInForm": false,
      "originalHeader": "id"
    },
    {
      "name": "year",
      "required": false,
      "visibleInViewer": true,
      "enumValues": [],
      "locked": false,
      "formulaSource": null,
      "formulaAnchorRow": null,
      "formulaMode": null,
      "enumStyles": {},
      "type": "int",
      "computed": false,
      "visibleInForm": true,
      "originalHeader": "year"
    },
    {
      "name": "title",
      "required": false,
      "visibleInViewer": true,
      "enumValues": [],
      "locked": false,
      "formulaSource": null,
      "formulaAnchorRow": null,
      "formulaMode": null,
      "enumStyles": {},
      "type": "string",
      "computed": false,
      "visibleInForm": true,
      "originalHeader": "Title"
    },
    {
      "name": "url",
      "required": false,
      "visibleInViewer": true,
      "enumValues": [],
      "locked": false,
      "formulaSource": null,
      "formulaAnchorRow": null,
      "formulaMode": null,
      "enumStyles": {},
      "type": "string",
      "computed": false,
      "visibleInForm": true,
      "originalHeader": "url"
    },
    {
      "name": "link",
      "required": false,
      "visibleInViewer": true,
      "enumValues": [],
      "locked": true,
      "formulaSource": "=HYPERLINK(D2:D987, C2:C987)",
      "formulaAnchorRow": 2,
      "formulaMode": "incremental_copy",
      "enumStyles": {},
      "type": "computed",
      "computed": true,
      "visibleInForm": false,
      "originalHeader": "link"
    },
    {
      "name": "nation",
      "required": false,
      "visibleInViewer": true,
      "enumValues": [],
      "locked": false,
      "formulaSource": null,
      "formulaAnchorRow": null,
      "formulaMode": null,
      "enumStyles": {},
      "type": "string",
      "computed": false,
      "visibleInForm": true,
      "originalHeader": "nation"
    },
    {
      "name": "rating",
      "required": false,
      "visibleInViewer": true,
      "enumValues": [
        "Mediocre",
        "Medio",
        "Buono",
        "Ottimo",
        "Capolavoro",
        "Pessimo"
      ],
      "locked": false,
      "formulaSource": null,
      "formulaAnchorRow": null,
      "formulaMode": null,
      "enumStyles": {
        "Capolavoro": {
          "bg": "#215a6c",
          "fg": "#c6dbe1"
        },
        "Ottimo": {
          "bg": "#d4edbc",
          "fg": "#11734b"
        },
        "Buono": {
          "bg": "#ffe5a0",
          "fg": "#473821"
        },
        "Medio": {
          "bg": "#ffc8aa",
          "fg": "#753800"
        },
        "Mediocre": {
          "bg": "#ffcfc9",
          "fg": "#b10202"
        },
        "Pessimo": {
          "bg": "#e8eaed",
          "fg": "#000000"
        }
      },
      "type": "enum",
      "computed": false,
      "visibleInForm": true,
      "originalHeader": "rating"
    }
  ],
  "enumStyles": {
    "rating": {
      "Capolavoro": {
        "bg": "#215a6c",
        "fg": "#c6dbe1"
      },
      "Ottimo": {
        "bg": "#d4edbc",
        "fg": "#11734b"
      },
      "Buono": {
        "bg": "#ffe5a0",
        "fg": "#473821"
      },
      "Medio": {
        "bg": "#ffc8aa",
        "fg": "#753800"
      },
      "Mediocre": {
        "bg": "#ffcfc9",
        "fg": "#b10202"
      },
      "Pessimo": {
        "bg": "#e8eaed",
        "fg": "#000000"
      }
    }
  }
}
```

## File: `output/current/project.config.json`
```text
{
  "projectName": "Generated App",
  "projectSlug": "generated-app",
  "backendName": "generated-app-backend",
  "entityName": "Item",
  "entityLabelLower": "item",
  "sheetName": "Sheet1",
  "outputDirectory": "",
  "buildMarker": "GENERATED_APP_BACKEND_V1",
  "adminPassword": "CHANGE_ME_WRITE_KEY_2026"
}
```

## File: `output/gas_manual/deploy.manifest.json`
```text
{
  "projectSlug": "prova-film",
  "projectName": "Prova_film",
  "frontend": {
    "provider": "github-pages",
    "repoNameSuggested": "prova-film",
    "branch": "main",
    "publishDir": "docs",
    "entryFile": "docs/index.html",
    "viewerFile": "docs/viewer.html"
  },
  "backend": {
    "provider": "google-apps-script",
    "entryFile": "codice.gs",
    "sheetName": "ProvaFilmData",
    "backendName": "prova-film-backend"
  },
  "files": [
    "codice.gs",
    "docs/index.html",
    "docs/viewer.html",
    "project.config.json",
    "fields.schema.json",
    "deploy.manifest.json"
  ],
  "schemaSummary": {
    "headers": [
      "id",
      "Titolo",
      "Data Produzione"
    ],
    "computed": [
      "id"
    ],
    "visibleInForm": [
      "Data Produzione"
    ],
    "visibleInViewer": [
      "id",
      "Titolo",
      "Data Produzione"
    ]
  }
}
```

## File: `output/gas_manual/fields.schema.json`
```text
{
  "headers": [
    "id",
    "Titolo",
    "Data Produzione"
  ],
  "requiredOnInsert": [],
  "optionalOnInsert": [
    "Titolo",
    "Data Produzione"
  ],
  "computed": [
    "id"
  ],
  "visibleInForm": [
    "Data Produzione"
  ],
  "visibleInViewer": [
    "id",
    "Titolo",
    "Data Produzione"
  ],
  "enums": {},
  "constraints": {
    "id": {
      "type": "int",
      "required": false,
      "min": 0
    },
    "Titolo": {
      "type": "string",
      "required": false,
      "maxLen": 255
    },
    "Data Produzione": {
      "type": "date",
      "required": false,
      "format": "dd/mm/yyyy"
    }
  },
  "fields": [
    {
      "name": "id",
      "type": "int",
      "required": false,
      "computed": true,
      "visibleInForm": false,
      "visibleInViewer": true,
      "enumValues": [],
      "locked": true
    },
    {
      "name": "Titolo",
      "type": "string",
      "required": false,
      "computed": false,
      "visibleInForm": false,
      "visibleInViewer": true,
      "enumValues": [],
      "locked": false
    },
    {
      "name": "Data Produzione",
      "type": "date",
      "required": false,
      "computed": false,
      "visibleInForm": true,
      "visibleInViewer": true,
      "enumValues": [],
      "locked": false
    }
  ]
}
```

## File: `output/gas_manual/google_setup.md`
```text
# Google Apps Script setup guide

## Project summary
- Project name: Prova_film
- Project slug: prova-film
- Backend logical name: prova-film-backend
- Sheet name: ProvaFilmData

## Files prepared
- codice.gs
- fields.schema.json
- project.config.json
- deploy.manifest.json
- sample_rows.json
- sample_rows.csv

## Suggested Google flow

### 1. Create the Google Sheet
Create a new Google Sheet and rename the main tab exactly as:

    ProvaFilmData

### 2. Create the header row
Insert these headers in row 1, from column A onward:

    id, Titolo, Data Produzione

### 3. Insert example rows
You have two prepared files:

- sample_rows.json
- sample_rows.csv

Suggested use:
- use `sample_rows.csv` if you want a quick import structure
- use `sample_rows.json` if you want to inspect the data clearly first

### 4. Create a new Apps Script project
Suggested project name:

    Prova_film Backend

### 5. Replace script content
Open:

    codice.gs

Copy everything into the Apps Script editor.

### 6. Deploy as Web App
Use the Apps Script deploy flow:

- Deploy → New deployment
- Type: Web app
- Execute as: Me
- Access: Anyone

Then copy the /exec URL.

### 7. Connect frontend
Paste the /exec URL into your frontend configuration.

## Notes
- No clasp required
- No Google API required
- Fully manual but controlled setup

```

## File: `output/gas_manual/project.config.json`
```text
{
  "projectName": "Prova_film",
  "projectSlug": "prova-film",
  "backendName": "prova-film-backend",
  "entityName": "ProvaFilmItem",
  "entityLabelLower": "item",
  "sheetName": "ProvaFilmData",
  "outputDirectory": "build/prova-film",
  "buildMarker": "PROVA_FILM_BACKEND_V1",
  "adminPassword": "UVZi4cpCddok7swLSf",
  "generatedAt": "2026-03-22T18:43:14.667Z"
}
```

## File: `output/gas_manual/sample_rows.json`
```text
[
  {
    "id": 1,
    "Titolo": "Nosferatu",
    "Data Produzione": "04/03/1922"
  },
  {
    "id": 2,
    "Titolo": "Psycho",
    "Data Produzione": "16/06/1960"
  }
]
```

## File: `output_project/fields.schema.json`
```text
{
  "headers": [
    "id",
    "year",
    "title",
    "url",
    "link",
    "nation",
    "rating"
  ],
  "requiredOnInsert": [],
  "optionalOnInsert": [
    "year",
    "title",
    "url",
    "nation",
    "rating"
  ],
  "computed": [
    "id",
    "link"
  ],
  "visibleInForm": [
    "year",
    "title",
    "url",
    "nation",
    "rating"
  ],
  "visibleInViewer": [
    "id",
    "year",
    "title",
    "url",
    "link",
    "nation",
    "rating"
  ],
  "enums": {
    "rating": [
      "Mediocre",
      "Medio",
      "Buono",
      "Ottimo",
      "Capolavoro",
      "Pessimo"
    ]
  },
  "constraints": {
    "id": {
      "type": "int",
      "required": false,
      "min": 0
    },
    "year": {
      "type": "int",
      "required": false,
      "min": 0
    },
    "title": {
      "type": "string",
      "required": false,
      "maxLen": 255
    },
    "url": {
      "type": "string",
      "required": false,
      "maxLen": 255
    },
    "link": {
      "type": "computed",
      "required": false
    },
    "nation": {
      "type": "string",
      "required": false,
      "maxLen": 255
    },
    "rating": {
      "type": "enum",
      "required": false
    }
  },
  "fields": [
    {
      "name": "id",
      "required": false,
      "visibleInViewer": true,
      "enumValues": [],
      "locked": true,
      "formulaSource": null,
      "formulaAnchorRow": null,
      "formulaMode": null,
      "enumStyles": {},
      "type": "int",
      "computed": true,
      "visibleInForm": false
    },
    {
      "name": "year",
      "required": false,
      "visibleInViewer": true,
      "enumValues": [],
      "locked": false,
      "formulaSource": null,
      "formulaAnchorRow": null,
      "formulaMode": null,
      "enumStyles": {},
      "type": "int",
      "computed": false,
      "visibleInForm": true
    },
    {
      "name": "title",
      "required": false,
      "visibleInViewer": true,
      "enumValues": [],
      "locked": false,
      "formulaSource": null,
      "formulaAnchorRow": null,
      "formulaMode": null,
      "enumStyles": {},
      "type": "string",
      "computed": false,
      "visibleInForm": true
    },
    {
      "name": "url",
      "required": false,
      "visibleInViewer": true,
      "enumValues": [],
      "locked": false,
      "formulaSource": null,
      "formulaAnchorRow": null,
      "formulaMode": null,
      "enumStyles": {},
      "type": "string",
      "computed": false,
      "visibleInForm": true
    },
    {
      "name": "link",
      "required": false,
      "visibleInViewer": true,
      "enumValues": [],
      "locked": true,
      "formulaSource": "=HYPERLINK(D2:D987, C2:C987)",
      "formulaAnchorRow": 2,
      "formulaMode": "incremental_copy",
      "enumStyles": {},
      "type": "computed",
      "computed": true,
      "visibleInForm": false
    },
    {
      "name": "nation",
      "required": false,
      "visibleInViewer": true,
      "enumValues": [],
      "locked": false,
      "formulaSource": null,
      "formulaAnchorRow": null,
      "formulaMode": null,
      "enumStyles": {},
      "type": "string",
      "computed": false,
      "visibleInForm": true
    },
    {
      "name": "rating",
      "required": false,
      "visibleInViewer": true,
      "enumValues": [
        "Mediocre",
        "Medio",
        "Buono",
        "Ottimo",
        "Capolavoro",
        "Pessimo"
      ],
      "locked": false,
      "formulaSource": null,
      "formulaAnchorRow": null,
      "formulaMode": null,
      "enumStyles": {
        "Capolavoro": {
          "bg": "#215a6c",
          "fg": "#c6dbe1"
        },
        "Ottimo": {
          "bg": "#d4edbc",
          "fg": "#11734b"
        },
        "Buono": {
          "bg": "#ffe5a0",
          "fg": "#473821"
        },
        "Medio": {
          "bg": "#ffc8aa",
          "fg": "#753800"
        },
        "Mediocre": {
          "bg": "#ffcfc9",
          "fg": "#b10202"
        },
        "Pessimo": {
          "bg": "#e8eaed",
          "fg": "#000000"
        }
      },
      "type": "enum",
      "computed": false,
      "visibleInForm": true
    }
  ],
  "enumStyles": {
    "rating": {
      "Capolavoro": {
        "bg": "#215a6c",
        "fg": "#c6dbe1"
      },
      "Ottimo": {
        "bg": "#d4edbc",
        "fg": "#11734b"
      },
      "Buono": {
        "bg": "#ffe5a0",
        "fg": "#473821"
      },
      "Medio": {
        "bg": "#ffc8aa",
        "fg": "#753800"
      },
      "Mediocre": {
        "bg": "#ffcfc9",
        "fg": "#b10202"
      },
      "Pessimo": {
        "bg": "#e8eaed",
        "fg": "#000000"
      }
    }
  }
}
```

## File: `pipeline/__init__.py`
```text

```

## File: `pipeline/apply_builder_state.py`
```text
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OUTPUT_CURRENT_DIR = ROOT / "output" / "current"
TARGET_BUILDER_STATE = OUTPUT_CURRENT_DIR / "builder_state.json"


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage:\n"
            "  python pipeline/apply_builder_state.py <path_to_builder_state.json>"
        )

    source = Path(sys.argv[1]).expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(f"Builder state file not found: {source}")
    if not source.is_file():
        raise FileNotFoundError(f"Path is not a file: {source}")

    OUTPUT_CURRENT_DIR.mkdir(parents=True, exist_ok=True)

    shutil.copy2(source, TARGET_BUILDER_STATE)

    print("Builder state imported successfully.")
    print(f"Source: {source}")
    print(f"Target: {TARGET_BUILDER_STATE}")

    print("\nRebuilding generated files...")
    result = subprocess.run(
        [sys.executable, str(ROOT / "build_from_config.py")],
        cwd=ROOT,
    )
    if result.returncode != 0:
        raise SystemExit("Build failed after importing builder_state.json")

    print("\nDone.")
    print(f"Updated backend:  {OUTPUT_CURRENT_DIR / 'codice.gs'}")
    print(f"Updated frontend: {OUTPUT_CURRENT_DIR / 'docs' / 'index.html'}")
    print(f"Updated viewer:   {OUTPUT_CURRENT_DIR / 'docs' / 'viewer.html'}")


if __name__ == "__main__":
    main()
```

## File: `pipeline/apply_review_state.py`
```text
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OUTPUT_CURRENT_DIR = ROOT / "output" / "current"
TARGET_BUILDER_STATE = OUTPUT_CURRENT_DIR / "builder_state.json"


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage:\n"
            "  python pipeline/apply_review_state.py <path_to_reviewed_app_state.json>"
        )

    source = Path(sys.argv[1]).expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(f"Reviewed app state file not found: {source}")
    if not source.is_file():
        raise FileNotFoundError(f"Path is not a file: {source}")

    OUTPUT_CURRENT_DIR.mkdir(parents=True, exist_ok=True)

    shutil.copy2(source, TARGET_BUILDER_STATE)

    print("Reviewed app state imported successfully.")
    print(f"Source: {source}")
    print(f"Target: {TARGET_BUILDER_STATE}")

    print("\nRebuilding generated files...")
    result = subprocess.run(
        [sys.executable, str(ROOT / "build_from_config.py")],
        cwd=ROOT,
    )
    if result.returncode != 0:
        raise SystemExit("Build failed after importing reviewed_app_state.json")

    print("\nDone.")
    print(f"Updated backend:  {OUTPUT_CURRENT_DIR / 'codice.gs'}")
    print(f"Updated frontend: {OUTPUT_CURRENT_DIR / 'docs' / 'index.html'}")
    print(f"Updated viewer:   {OUTPUT_CURRENT_DIR / 'docs' / 'viewer.html'}")


if __name__ == "__main__":
    main()
```

## File: `pipeline/build_all_from_input.py`
```text
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OUTPUT_CURRENT_DIR = ROOT / "output" / "current"
EXAMPLES_DIR = ROOT / "examples"
PROJECT_CONFIG_PATH = OUTPUT_CURRENT_DIR / "project.config.json"
FIELDS_SCHEMA_PATH = OUTPUT_CURRENT_DIR / "fields.schema.json"


def ensure_default_project_config() -> dict:
    """
    Se project.config.json non esiste in output/current, ne crea uno minimale.
    Se esiste già, lo lascia invariato.
    """
    OUTPUT_CURRENT_DIR.mkdir(parents=True, exist_ok=True)

    if PROJECT_CONFIG_PATH.exists():
        return json.loads(PROJECT_CONFIG_PATH.read_text(encoding="utf-8"))

    config = {
        "projectName": "Imported Sheet Project",
        "projectSlug": "imported-sheet-project",
        "backendName": "imported-sheet-backend",
        "entityName": "ImportedItem",
        "entityLabelLower": "item",
        "sheetName": "Sheet1",
        "outputDirectory": str(OUTPUT_CURRENT_DIR),
        "buildMarker": "IMPORTED_SHEET_BACKEND_V1",
        "adminPassword": "CHANGE_ME_WRITE_KEY_2026",
    }

    PROJECT_CONFIG_PATH.write_text(
        json.dumps(config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return config


def run_step(cmd: list[str], title: str) -> None:
    print(f"\n=== {title} ===")
    print(" ".join(cmd))
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        raise SystemExit(f"Step failed: {title}")


def find_single_input_dir() -> Path:
    candidate_dirs = [p for p in EXAMPLES_DIR.iterdir() if p.is_dir()]
    if not candidate_dirs:
        raise SystemExit(f"No subdirectories found inside examples/: {EXAMPLES_DIR}")
    if len(candidate_dirs) > 1:
        raise SystemExit(
            "More than one subdirectory found inside examples/. "
            "Pass the desired input directory explicitly."
        )
    return candidate_dirs[0]


def main() -> None:
    if len(sys.argv) == 1:
        input_dir = find_single_input_dir()
    else:
        input_dir = Path(sys.argv[1])

    ensure_default_project_config()

    run_step(
        [
            sys.executable,
            str(ROOT / "pipeline" / "build_schema_from_input.py"),
            str(input_dir),
        ],
        "STEP 1 - Build fields.schema.json from input basket",
    )

    if not FIELDS_SCHEMA_PATH.exists():
        raise SystemExit(f"Missing generated schema: {FIELDS_SCHEMA_PATH}")

    run_step(
        [
            sys.executable,
            str(ROOT / "build_from_config.py"),
        ],
        "STEP 2 - Generate codice.gs + index.html + viewer.html",
    )

    print("\nBuild completed successfully.")
    print(f"Schema:   {FIELDS_SCHEMA_PATH}")
    print(f"Config:   {PROJECT_CONFIG_PATH}")
    print(f"Output:   {OUTPUT_CURRENT_DIR}")
    print(f"Frontend: {OUTPUT_CURRENT_DIR / 'docs' / 'index.html'}")
    print(f"Viewer:   {OUTPUT_CURRENT_DIR / 'docs' / 'viewer.html'}")
    print(f"Backend:  {OUTPUT_CURRENT_DIR / 'codice.gs'}")


if __name__ == "__main__":
    main()
```

## File: `pipeline/build_schema_from_input.py`
```text
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import json
from typing import Dict, Optional

from generators.import_from_html import import_visuals_from_html
from generators.import_from_sheet import save_schema_from_xlsx
from generators.merge_schema import merge_schema_with_visuals
from app.builder_state import build_builder_state


OUTPUT_CURRENT_DIR = ROOT / "output" / "current"
EXAMPLES_DIR = ROOT / "examples"


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def find_input_files(input_dir: str | Path) -> Dict[str, Optional[Path]]:
    input_dir = Path(input_dir)
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    xlsx_files = sorted(input_dir.rglob("*.xlsx"))
    html_files = sorted(input_dir.rglob("*.html"))
    css_files = sorted(input_dir.rglob("*.css"))

    if not xlsx_files:
        raise FileNotFoundError(
            f"Missing required .xlsx file inside: {input_dir}"
        )

    if not html_files:
        print(f"WARNING: no .html file found inside {input_dir}. Visual enrichment will be skipped.")

    if not css_files:
        print(f"WARNING: no .css file found inside {input_dir}. This is not blocking.")

    return {
        "input_dir": input_dir,
        "xlsx": xlsx_files[0],
        "html": html_files[0] if html_files else None,
        "css": css_files[0] if css_files else None,
    }


def build_schema_from_directory(
    input_dir: str | Path,
    output_json_path: str | Path,
    enum_field_name: str = "rating",
    debug: bool = False,
) -> dict:
    paths = find_input_files(input_dir)

    sheet_schema = save_schema_from_xlsx(
        xlsx_path=paths["xlsx"],
        output_json_path=None,
        sheet_name=None,
        header_row=1,
        sample_row=2,
        debug=debug,
    )

    final_schema = sheet_schema

    if paths["html"] is not None:
        html_visuals = import_visuals_from_html(
            html_path=paths["html"],
            enum_field_name=enum_field_name,
            debug=debug,
        )

        final_schema = merge_schema_with_visuals(
            sheet_schema=sheet_schema,
            html_visuals=html_visuals,
        )

    output_json_path = Path(output_json_path)
    write_json(output_json_path, final_schema)

    if debug:
        print("\nINPUT PATHS")
        print(paths)

        print("\nFINAL ENUMS")
        print(final_schema.get("enums", {}))

        print("\nFINAL ENUM STYLES")
        print(final_schema.get("enumStyles", {}))

    return final_schema


def apply_project_config(builder_state: dict, project_config: dict) -> dict:
    project = builder_state.setdefault("project", {})

    keys = [
        "sheetName",
        "projectName",
        "projectSlug",
        "backendName",
        "entityName",
        "entityLabelLower",
        "buildMarker",
        "adminPassword",
    ]

    for key in keys:
        if key in project_config and project_config[key]:
            project[key] = project_config[key]

    return builder_state


def main() -> None:
    if len(sys.argv) == 1:
        candidate_dirs = [p for p in EXAMPLES_DIR.iterdir() if p.is_dir()]
        if not candidate_dirs:
            raise SystemExit(
                f"No subdirectories found inside examples/: {EXAMPLES_DIR}"
            )
        if len(candidate_dirs) > 1:
            raise SystemExit(
                "More than one subdirectory found inside examples/. "
                "Pass the desired input directory explicitly."
            )
        input_dir = candidate_dirs[0]
        enum_field_name = "rating"

    elif len(sys.argv) == 2:
        input_dir = Path(sys.argv[1])
        enum_field_name = "rating"

    else:
        input_dir = Path(sys.argv[1])
        enum_field_name = sys.argv[2]

    parsed_output_json = OUTPUT_CURRENT_DIR / "parsed.schema.json"
    builder_state_output_json = OUTPUT_CURRENT_DIR / "builder_state.json"
    compat_output_json = OUTPUT_CURRENT_DIR / "fields.schema.json"
    project_config_path = OUTPUT_CURRENT_DIR / "project.config.json"

    schema = build_schema_from_directory(
        input_dir=input_dir,
        output_json_path=parsed_output_json,
        enum_field_name=enum_field_name,
        debug=True,
    )

    if project_config_path.exists():
        project_config = json.loads(project_config_path.read_text(encoding="utf-8"))
    else:
        project_config = {
            "projectName": "Imported Sheet Project",
            "projectSlug": "imported-sheet-project",
            "backendName": "imported-sheet-backend",
            "entityName": "ImportedItem",
            "entityLabelLower": "item",
            "sheetName": "Sheet1",
            "outputDirectory": str(OUTPUT_CURRENT_DIR),
            "buildMarker": "IMPORTED_SHEET_BACKEND_V1",
            "adminPassword": "CHANGE_ME_WRITE_KEY_2026",
        }

    builder_state = build_builder_state(schema)
    builder_state = apply_project_config(builder_state, project_config)

    write_json(builder_state_output_json, builder_state)

    # compatibilità temporanea con il resto della pipeline attuale
    write_json(compat_output_json, schema)

    print("\nSchema generated successfully.")
    print("Parsed output:", parsed_output_json)
    print("Builder state:", builder_state_output_json)
    print("Compat output:", compat_output_json)
    print("Headers:", schema.get("headers", []))
    print("Enums:", schema.get("enums", {}))


if __name__ == "__main__":
    main()
```

## File: `pipeline/generate_final_app.py`
```text
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage:\n"
            "  python pipeline/generate_final_app.py <approved_configuration.json>"
        )

    source = Path(sys.argv[1]).expanduser().resolve()

    if not source.exists():
        raise FileNotFoundError(f"File not found: {source}")

    print("Generating final app from approved configuration...\n")

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "pipeline" / "apply_review_state.py"),
            str(source),
        ],
        cwd=ROOT,
    )

    if result.returncode != 0:
        raise SystemExit("Final app generation failed.")

    print("\nFinal app generated successfully.")
    print("\nFiles updated in:")
    print(ROOT / "output" / "current")


if __name__ == "__main__":
    main()
```

## File: `pipeline/prepare_review_from_input.py`
```text
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.build_schema_from_input import build_schema_from_directory
from app.builder_state import build_builder_state


OUTPUT_CURRENT_DIR = ROOT / "output" / "current"
EXAMPLES_DIR = ROOT / "examples"


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def find_single_input_dir() -> Path:
    candidate_dirs = [p for p in EXAMPLES_DIR.iterdir() if p.is_dir()]
    if not candidate_dirs:
        raise SystemExit(f"No subdirectories found inside examples/: {EXAMPLES_DIR}")
    if len(candidate_dirs) > 1:
        raise SystemExit(
            "More than one subdirectory found inside examples/. "
            "Pass the desired input directory explicitly."
        )
    return candidate_dirs[0]


def main() -> None:
    if len(sys.argv) == 1:
        input_dir = find_single_input_dir()
        enum_field_name = "rating"
    elif len(sys.argv) == 2:
        input_dir = Path(sys.argv[1])
        enum_field_name = "rating"
    elif len(sys.argv) == 3:
        input_dir = Path(sys.argv[1])
        enum_field_name = sys.argv[2]
    else:
        raise SystemExit(
            "Usage:\n"
            "  python pipeline/prepare_review_from_input.py <input_dir> [enum_field_name]\n\n"
            "Example:\n"
            "  python pipeline/prepare_review_from_input.py examples/case_001\n"
            "  python pipeline/prepare_review_from_input.py examples/case_001 rating"
        )

    OUTPUT_CURRENT_DIR.mkdir(parents=True, exist_ok=True)

    parsed_schema_path = OUTPUT_CURRENT_DIR / "parsed.schema.json"
    builder_state_path = OUTPUT_CURRENT_DIR / "builder_state.json"

    parsed_schema = build_schema_from_directory(
        input_dir=input_dir,
        output_json_path=parsed_schema_path,
        enum_field_name=enum_field_name,
        debug=True,
    )

    builder_state = build_builder_state(parsed_schema)
    write_json(builder_state_path, builder_state)

    print("\nReview preparation completed successfully.")
    print(f"Input directory:      {input_dir}")
    print(f"Parsed schema output: {parsed_schema_path}")
    print(f"Builder state output: {builder_state_path}")
    print("\nNext step:")
    print("1. Open docs/review.html")
    print("2. Load output/current/builder_state.json")
    print("3. Review fields and enum styles")
    print("4. Export reviewed_configuration.json")
    print("5. Apply it with pipeline/apply_review_state.py")


if __name__ == "__main__":
    main()
```

## File: `publish.sh`
```text
#!/usr/bin/env bash
set -e

echo "=== Djungo Builder Publish ==="

echo ""
echo "=== Step 1 - Rebuild demo files ==="

python pipeline/build_all_from_input.py examples/case_001
python tools/publish_to_docs.py

echo ""
echo "=== Step 2 - Git status ==="

git status

echo ""
read -p "Commit message: " MSG

git add .
git commit -m "$MSG" || true
git push origin main

echo ""
echo "=== Step 3 - Hetzner sync ==="

ssh root@65.21.176.227 <<'EOF'
set -e

cd /opt/sheets.builder

echo ""
echo "=== Reset local deploy artifacts ==="

git reset --hard HEAD

echo ""
echo "=== Pull latest changes ==="

git pull origin main

echo ""
echo "=== Activate venv ==="

source venv/bin/activate

echo ""
echo "=== Install requirements ==="

pip install -r requirements.txt

echo ""
echo "=== Restart service ==="

systemctl restart sheets-builder
systemctl status sheets-builder --no-pager

echo ""
echo "=== Health check ==="

curl -s https://builder.sgbh.org/health

echo ""
echo "=== Current commit ==="

git log --oneline -n 1
EOF

echo ""
echo "=== Published successfully ==="
```

## File: `requirements.txt`
```text
beautifulsoup4==4.14.3
blinker==1.9.0
certifi==2026.4.22
charset-normalizer==3.4.7
click==8.3.3
et_xmlfile==2.0.0
Flask==3.1.3
gunicorn==25.3.0
idna==3.13
itsdangerous==2.2.0
Jinja2==3.1.6
lxml==6.1.0
MarkupSafe==3.0.3
numpy==2.4.4
openpyxl==3.1.5
packaging==26.2
pandas==3.0.2
python-dateutil==2.9.0.post0
requests==2.33.1
six==1.17.0
soupsieve==2.8.3
typing_extensions==4.15.0
urllib3==2.6.3
Werkzeug==3.1.8

```

## File: `server.py`
```text
from __future__ import annotations

import json
import re
import uuid
from pathlib import Path
from typing import Any, Dict

import requests

from flask import (
    Flask,
    jsonify,
    redirect,
    request,
    send_file,
)
from werkzeug.utils import secure_filename

from pipeline.build_schema_from_input import build_schema_from_directory
from app.builder_state import build_builder_state
from generators.builder_generators import generate_all


ROOT = Path(__file__).resolve().parent
DOCS_DIR = ROOT / "docs"
WORKDIR = ROOT / "workdir" / "flask_sessions"
DATA_DIR = ROOT / "data"
APPS_REGISTRY_PATH = DATA_DIR / "apps_registry.json"

# =========================================================
# APPS CONFIG (slug -> hidden backend config)
# =========================================================


PUBLIC_MODES = {"meta", "schema", "view"}
PROTECTED_MODES = {"insert", "getById", "update", "delete"}
ALL_PROXY_MODES = PUBLIC_MODES | PROTECTED_MODES

# =========================================================
# FLASK APP
# =========================================================
app = Flask(
    __name__,
    static_folder=str(DOCS_DIR),
    static_url_path="",
)

WORKDIR.mkdir(parents=True, exist_ok=True)

def slugify_app_name(value: str) -> str:
    value = str(value or "").strip()
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", value)
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-")
    return value or "generated-app"

def load_apps_registry() -> Dict[str, Dict[str, str]]:
    if not APPS_REGISTRY_PATH.exists():
        return {}

    raw = APPS_REGISTRY_PATH.read_text(encoding="utf-8").strip()

    if not raw:
        return {}

    return json.loads(raw)


def save_apps_registry(registry: Dict[str, Dict[str, str]]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    APPS_REGISTRY_PATH.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def register_app_config(slug: str, web_app_url: str, api_key: str) -> Dict[str, str]:
    safe_slug = slugify_app_name(slug)

    registry = load_apps_registry()
    registry[safe_slug] = {
        "web_app_url": web_app_url.strip(),
        "api_key": api_key.strip(),
    }

    save_apps_registry(registry)
    return registry[safe_slug]


# =========================================================
# HELPERS
# =========================================================
def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def builder_state_to_runtime_data(
    builder_state: Dict[str, Any]
) -> tuple[Dict[str, Any], Dict[str, Any]]:
    project = dict(builder_state.get("project", {}) or {})
    fields = list(builder_state.get("fields", []) or [])
    constraints = dict(builder_state.get("constraints", {}) or {})
    enums = dict(builder_state.get("enums", {}) or {})
    enum_styles = dict(builder_state.get("enumStyles", {}) or {})

    headers = [f["name"] for f in fields]

    required_on_insert = [
        f["name"]
        for f in fields
        if bool(f.get("required")) and not bool(f.get("computed"))
    ]

    optional_on_insert = [
        f["name"]
        for f in fields
        if not bool(f.get("required")) and not bool(f.get("computed"))
    ]

    computed = [
        f["name"]
        for f in fields
        if bool(f.get("computed"))
    ]

    visible_in_form = [
        f["name"]
        for f in fields
        if bool(f.get("visibleInForm"))
    ]

    visible_in_viewer = [
        f["name"]
        for f in fields
        if bool(f.get("visibleInViewer"))
    ]

    fields_schema = {
        "headers": headers,
        "requiredOnInsert": required_on_insert,
        "optionalOnInsert": optional_on_insert,
        "computed": computed,
        "visibleInForm": visible_in_form,
        "visibleInViewer": visible_in_viewer,
        "constraints": constraints,
        "enums": enums,
        "enumStyles": enum_styles,
        "fields": fields,
    }

    return project, fields_schema


def create_session_dir() -> Path:
    session_id = uuid.uuid4().hex[:12]
    session_dir = WORKDIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir


def get_session_dir(session_id: str) -> Path:
    safe = secure_filename(session_id)
    path = WORKDIR / safe

    if not path.exists() or not path.is_dir():
        raise FileNotFoundError(f"Session not found: {session_id}")

    return path


# =========================================================
# PROXY HELPERS
# =========================================================
def get_app_config(slug: str) -> Dict[str, str]:
    safe_slug = slugify_app_name(slug)
    registry = load_apps_registry()
    config = registry.get(safe_slug)

    if not config:
        raise FileNotFoundError(f"Unknown app slug: {slug}")

    return config


def parse_apps_script_response(text: str) -> Dict[str, Any]:
    payload = text.strip()

    # JSONP style: callback({...});
    if "(" in payload and payload.endswith(");"):
        start = payload.find("(")
        payload = payload[start + 1:-2]

    return json.loads(payload)


def call_apps_script_proxy(
    slug: str,
    mode: str,
    params: Dict[str, Any],
) -> Dict[str, Any]:
    if mode not in ALL_PROXY_MODES:
        raise ValueError(f"Invalid mode: {mode}")

    config = get_app_config(slug)

    outbound = {
    "mode": mode,
    "cb": "djungoProxy",
}

    for key, value in params.items():
        if key in {"mode", "apiKey", "webApp", "cb", "_"}:
            continue
        outbound[key] = value

    if mode in PROTECTED_MODES:
        outbound["apiKey"] = config["api_key"]

    resp = requests.get(
        config["web_app_url"],
        params=outbound,
        timeout=45,
    )

    resp.raise_for_status()

    return parse_apps_script_resp

...[TRUNCATED]...

```

## File: `tools/deploy_frontend_rest.py`
```text
from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib import error, request


API_BASE = "https://api.github.com"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class ProjectConfig:
    project_name: str
    project_slug: str
    backend_name: str
    entity_name: str
    entity_label_lower: str
    sheet_name: str
    output_directory: str
    build_marker: str
    admin_password: str
    generated_at: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProjectConfig":
        return cls(
            project_name=data["projectName"],
            project_slug=data["projectSlug"],
            backend_name=data["backendName"],
            entity_name=data["entityName"],
            entity_label_lower=data["entityLabelLower"],
            sheet_name=data["sheetName"],
            output_directory=data["outputDirectory"],
            build_marker=data["buildMarker"],
            admin_password=data["adminPassword"],
            generated_at=data["generatedAt"],
        )


@dataclass
class DeployManifest:
    project_slug: str
    project_name: str
    frontend_repo_name_suggested: str
    frontend_branch: str
    frontend_publish_dir: str
    frontend_entry_file: str
    frontend_viewer_file: str
    files: list[str]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DeployManifest":
        frontend = data["frontend"]
        return cls(
            project_slug=data["projectSlug"],
            project_name=data["projectName"],
            frontend_repo_name_suggested=frontend["repoNameSuggested"],
            frontend_branch=frontend["branch"],
            frontend_publish_dir=frontend["publishDir"],
            frontend_entry_file=frontend["entryFile"],
            frontend_viewer_file=frontend["viewerFile"],
            files=list(data["files"]),
        )


# ============================================================
# GENERIC HELPERS
# ============================================================

def print_header(title: str) -> None:
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def print_kv(key: str, value: Any) -> None:
    print(f"{key:<28}: {value}")


def ensure_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"File richiesto non trovato: {path}")
    if not path.is_file():
        raise FileNotFoundError(f"Percorso non valido (non è file): {path}")


def read_json(path: Path) -> dict[str, Any]:
    ensure_file(path)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON non valido: {path}") from exc


def extract_zip(zip_path: Path, extract_dir: Path, clean: bool = False) -> None:
    if not zip_path.exists():
        raise FileNotFoundError(
            f"ZIP non trovato: {zip_path}\n"
            f"Controlla nome e percorso. Esempio: examples/prova-film.zip"
        )

    if clean and extract_dir.exists():
        shutil.rmtree(extract_dir)

    extract_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_dir)


def collect_frontend_files(root: Path, publish_dir: str) -> list[Path]:
    base = root / publish_dir
    if not base.exists():
        raise FileNotFoundError(f"Directory frontend non trovata nel package: {base}")

    files: list[Path] = []
    for path in base.rglob("*"):
        if path.is_file():
            files.append(path)
    return sorted(files)


def build_pages_url(owner: str, repo: str) -> str:
    return f"https://{owner}.github.io/{repo}/"


# ============================================================
# GITHUB REST CLIENT
# ============================================================

class GitHubApi:
    def __init__(self, token: str):
        self.token = token.strip()
        if not self.token:
            raise ValueError("Token GitHub vuoto")

    def _request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
        expected_status: tuple[int, ...] = (200,),
    ) -> dict[str, Any] | None:
        url = f"{API_BASE}{path}"
        data = None

        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "sheet-builder-deployer",
        }

        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = request.Request(url=url, data=data, headers=headers, method=method)

        try:
            with request.urlopen(req) as resp:
                raw = resp.read().decode("utf-8")
                if resp.status not in expected_status:
                    raise RuntimeError(f"HTTP inatteso {resp.status}: {raw}")
                return json.loads(raw) if raw else None

        except error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"GitHub API error {exc.code} su {method} {path}\n{raw}"
            ) from exc

    def get_authenticated_user(self) -> dict[str, Any]:
        return self._request("GET", "/user", expected_status=(200,)) or {}

    def get_repo(self, owner: str, repo: str) -> dict[str, Any] | None:
        try:
            return self._request("GET", f"/repos/{owner}/{repo}", expected_status=(200,))
        except RuntimeError as exc:
            if "GitHub API error 404" in str(exc):
                return None
            raise

    def create_user_repo(self, repo_name: str, private: bool = False, description: str = "") -> dict[str, Any]:
        body = {
            "

...[TRUNCATED]...

```

## File: `tools/prepare_google_manual.py`
```text
from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class ProjectConfig:
    project_name: str
    project_slug: str
    backend_name: str
    entity_name: str
    entity_label_lower: str
    sheet_name: str
    output_directory: str
    build_marker: str
    admin_password: str
    generated_at: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProjectConfig":
        return cls(
            project_name=data["projectName"],
            project_slug=data["projectSlug"],
            backend_name=data["backendName"],
            entity_name=data["entityName"],
            entity_label_lower=data["entityLabelLower"],
            sheet_name=data["sheetName"],
            output_directory=data["outputDirectory"],
            build_marker=data["buildMarker"],
            admin_password=data["adminPassword"],
            generated_at=data["generatedAt"],
        )


@dataclass
class DeployManifest:
    project_slug: str
    project_name: str
    backend_entry_file: str
    backend_sheet_name: str
    backend_name: str
    files: list[str]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DeployManifest":
        backend = data["backend"]
        return cls(
            project_slug=data["projectSlug"],
            project_name=data["projectName"],
            backend_entry_file=backend["entryFile"],
            backend_sheet_name=backend["sheetName"],
            backend_name=backend["backendName"],
            files=list(data["files"]),
        )


# ============================================================
# HELPERS
# ============================================================

def print_header(title: str) -> None:
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def print_kv(key: str, value: Any) -> None:
    print(f"{key:<28}: {value}")


def ensure_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"File richiesto non trovato: {path}")
    if not path.is_file():
        raise FileNotFoundError(f"Percorso non valido (non è file): {path}")


def read_json(path: Path) -> dict[str, Any]:
    ensure_file(path)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON non valido: {path}") from exc


def extract_zip(zip_path: Path, extract_dir: Path, clean: bool = False) -> None:
    if not zip_path.exists():
        raise FileNotFoundError(
            f"ZIP non trovato: {zip_path}\n"
            f"Controlla nome e percorso. Esempio corretto: examples/prova-film.zip"
        )

    if clean and extract_dir.exists():
        shutil.rmtree(extract_dir)

    extract_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_dir)


def write_text_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json_file(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv_file(path: Path, headers: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


# ============================================================
# CORE LOGIC
# ============================================================

def inspect_package(extract_dir: Path) -> tuple[ProjectConfig, DeployManifest, dict[str, Any]]:
    project_config = ProjectConfig.from_dict(read_json(extract_dir / "project.config.json"))
    deploy_manifest = DeployManifest.from_dict(read_json(extract_dir / "deploy.manifest.json"))
    fields_schema = read_json(extract_dir / "fields.schema.json")
    return project_config, deploy_manifest, fields_schema


def build_example_rows(fields_schema: dict[str, Any]) -> list[dict[str, Any]]:
    headers = fields_schema.get("headers", [])
    computed = set(fields_schema.get("computed", []))
    enums = fields_schema.get("enums", {})

    rows: list[dict[str, Any]] = []

    row1: dict[str, Any] = {}
    row2: dict[str, Any] = {}

    for header in headers:
        if header in computed:
            if header == "id":
                row1[header] = 1
                row2[header] = 2
            else:
                row1[header] = ""
                row2[header] = ""
            continue

        h_norm = header.strip().lower().replace(" ", "_")

        if header in enums and enums[header]:
            row1[header] = enums[header][0]
            row2[header] = enums[header][-1]
        elif "title" in h_norm or "titolo" in h_norm:
            row1[header] = "Nosferatu"
            row2[header] = "Psycho"
        elif "date" in h_norm or "data" in h_norm:
            row1[header] = "04/03/1922"
            row2[header] = "16/06/1960"
        elif "year" in h_norm or "anno" in h_norm:
            row1[header] = 1922
            row2[header] = 1960
        elif "nation" in h_norm or "nazione" in h_norm:
            row1[header] = "Germania"
            row2[header] = "USA"
        elif "url" in h_norm:
            row1[header] = "https://example.org/nosferatu"
            row2[header] = "https://example.org/psycho"
        else:
            row1[header] = f"example_{h_norm}_1"
            row2[header] = f"example_{h_norm}_2"

    rows.append(row1)
    rows.append(row2)
    return rows


def build_google_setup_md(
    project_config: Projec

...[TRUNCATED]...

```

## File: `tools/project_state_dump.py`
```text
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "PROJECT_STATE_DUMP.md"

EXCLUDE_DIRS = {
    ".git", ".venv", "venv", "__pycache__", ".mypy_cache",
    ".pytest_cache", "node_modules", "workdir", ".history"
}

INCLUDE_EXT = {
    ".py", ".html", ".js", ".css", ".json", ".md", ".txt",
    ".service", ".conf", ".sh"
}

MAX_FILE_CHARS = 6000


def should_skip(path: Path) -> bool:
    return any(part in EXCLUDE_DIRS for part in path.parts)


def tree_lines(root: Path) -> list[str]:
    lines = []
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if should_skip(rel):
            continue
        depth = len(rel.parts) - 1
        prefix = "  " * depth + ("- " if path.is_file() else "+ ")
        lines.append(prefix + str(rel))
    return lines


def file_summary(root: Path) -> list[str]:
    chunks = []
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if should_skip(rel) or not path.is_file():
            continue
        if path.suffix not in INCLUDE_EXT:
            continue

        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            text = f"[Could not read file: {exc}]"

        chunks.append(f"\n## File: `{rel}`\n")
        chunks.append("```text\n")
        chunks.append(text[:MAX_FILE_CHARS])
        if len(text) > MAX_FILE_CHARS:
            chunks.append("\n\n...[TRUNCATED]...\n")
        chunks.append("\n```\n")
    return chunks


def main() -> None:
    content = []
    content.append("# PROJECT STATE DUMP\n")
    content.append(f"Generated: {datetime.now().isoformat(timespec='seconds')}\n")
    content.append(f"Root: `{ROOT}`\n\n")

    content.append("## 1. Project tree\n\n")
    content.append("```text\n")
    content.extend(line + "\n" for line in tree_lines(ROOT))
    content.append("```\n\n")

    content.append("## 2. Key file contents\n")
    content.extend(file_summary(ROOT))

    OUT.write_text("".join(content), encoding="utf-8")
    print(f"Written: {OUT}")


if __name__ == "__main__":
    main()
```

## File: `tools/publish_to_docs.py`
```text
from __future__ import annotations

import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
OUTPUT_CURRENT_DIR = ROOT / "output" / "current"
OUTPUT_DOCS_DIR = OUTPUT_CURRENT_DIR / "docs"
DOCS_DIR = ROOT / "docs"


FILES_TO_COPY = [
    (OUTPUT_DOCS_DIR / "index.html", DOCS_DIR / "index.html"),
    (OUTPUT_DOCS_DIR / "viewer.html", DOCS_DIR / "viewer.html"),
    (OUTPUT_CURRENT_DIR / "codice.gs", DOCS_DIR / "codice.gs"),
]


PUBLIC_BASE_URL = "https://progettazionemauro.github.io/sheets.builder"


def main() -> None:
    missing = [src for src, _ in FILES_TO_COPY if not src.exists()]
    if missing:
        msg = "\n".join(f"- {p}" for p in missing)
        raise FileNotFoundError(
            "Missing generated files in output/current:\n"
            f"{msg}\n\n"
            "Run the final generation step first."
        )

    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    for src, dst in FILES_TO_COPY:
        shutil.copy2(src, dst)
        print(f"Copied: {src} -> {dst}")

    print("\nPublish-to-docs completed successfully.")
    print("\nNext steps:")
    print("1. git add docs/index.html docs/viewer.html docs/codice.gs")
    print('2. git commit -m "Update final generated app"')
    print("3. git push")
    print("\nPublic URLs:")
    print(f"- App ready page: {PUBLIC_BASE_URL}/app_ready.html")
    print(f"- CRUD app:       {PUBLIC_BASE_URL}/index.html")
    print(f"- Viewer:         {PUBLIC_BASE_URL}/viewer.html")


if __name__ == "__main__":
    main()
```

## File: `viewer.html`
```text
<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>HorrorMovie Viewer</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 12px; }
    .muted { color:#666; }

    table { border-collapse: collapse; width: 100%; }
    th, td {
      border:1px solid #e5e5e5;
      padding:8px;
      font-size: 13px;
      vertical-align: top;
      overflow-wrap:anywhere;
      white-space: pre-wrap;
    }

    thead th{
      position: sticky;
      top: 0;
      z-index: 2;
      background: #2f3b52;
      color: #fff;
      font-weight: 800;
    }

    tbody tr:nth-child(even){ background:#f6f8fb; }
    tbody tr:nth-child(odd){ background:#ffffff; }

    tbody tr.first-row {
      background: #fff3cd !important;
      outline: 2px solid #ffe69c;
      outline-offset: -2px;
    }

    a { color: #1155cc; text-decoration: underline; font-weight: 800; }

    td.rating { font-weight: 900; text-align:center; }
    td.rating-pessimo     { background:#8b0000 !important; color:#fff !important; }
    td.rating-mediocre    { background:#c0392b !important; color:#fff !important; }
    td.rating-medio       { background:#f39c12 !important; color:#111 !important; }
    td.rating-buono       { background:#f1c40f !important; color:#111 !important; }
    td.rating-ottimo      { background:#2ecc71 !important; color:#111 !important; }
    td.rating-capolavoro  { background:#1abc9c !important; color:#111 !important; }

    td.col-url {
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
      font-size:12px;
    }
  </style>
</head>
<body>

  <div class="muted">Viewer read-only (ultime righe) — tab <b>HorrorMovie</b></div>
  <div id="status" class="muted" style="margin:6px 0;">Caricamento…</div>
  <div id="tbl"></div>

<script>
  const qs = new URLSearchParams(location.search);
  const WEB_APP_URL = qs.get("webApp");
  const LIMIT = qs.get("limit") || "50";

  function jsonp(url) {
    return new Promise((resolve, reject) => {
      const cbName = "cb_" + Math.random().toString(36).slice(2);
      const script = document.createElement("script");

      const t = setTimeout(() => {
        cleanup();
        reject(new Error("Timeout JSONP"));
      }, 15000);

      function cleanup() {
        clearTimeout(t);
        try { delete window[cbName]; } catch (_) { window[cbName] = undefined; }
        script.remove();
      }

      window[cbName] = (data) => {
        cleanup();
        resolve(data);
      };

      const u = new URL(url);
      u.searchParams.set("cb", cbName);
      u.searchParams.set("_", Date.now().toString());

      script.src = u.toString();
      script.onerror = () => {
        cleanup();
        reject(new Error("JSONP load error"));
      };

      document.body.appendChild(script);
    });
  }

  function esc(s) {
    return String(s ?? "").replace(/[&<>"']/g, c => (
      {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]
    ));
  }

  function normHeader_(h) {
    return String(h ?? "").trim().toLowerCase().replace(/\s+/g, " ");
  }

  function findCol_(headers, keyword) {
    const key = String(keyword).toLowerCase();
    for (let i = 0; i < headers.length; i++) {
      const nh = normHeader_(headers[i]);
      if (nh === key) return i;
      if (nh.includes(key)) return i;
    }
    return -1;
  }

  function ratingClass_(val) {
    const v = String(val ?? "").trim().toLowerCase();
    if (!v) return "";
    if (v === "pessimo") return "rating-pessimo";
    if (v === "mediocre") return "rating-mediocre";
    if (v === "medio") return "rating-medio";
    if (v === "buono") return "rating-buono";
    if (v === "ottimo") return "rating-ottimo";
    if (v === "capolavoro") return "rating-capolavoro";
    return "";
  }

  async function load() {
    const status = document.getElementById("status");
    const tbl = document.getElementById("tbl");

    if (!WEB_APP_URL) {
      status.textContent = "Errore: manca parametro 'webApp' nell'URL.";
      return;
    }

    try {
      const u = new URL(WEB_APP_URL);
      u.searchParams.set("mode", "view");
      u.searchParams.set("limit", LIMIT);

      const resp = await jsonp(u.toString());
      if (!resp || resp.ok !== true) {
        status.textContent = "Errore: " + (resp?.error || "risposta non valida");
        return;
      }

      const headers = resp.headers || [];
      const rowsRaw = resp.rows || [];

      // più recente in alto
      const rows = rowsRaw.slice().reverse();

      const idxTitle  = findCol_(headers, "title");
      const idxLink   = findCol_(headers, "link");
      const idxUrl    = findCol_(headers, "url");
      const idxRating = findCol_(headers, "rating");

      status.textContent =
        `OK | cols: title=${idxTitle}, link=${idxLink}, url=${idxUrl}, rating=${idxRating} | headers=` +
        headers.map(h => `"${String(h)}"`).join(", ");

      let html = "<table><thead><tr>";
      for (const h of headers) html += `<th>${esc(h)}</th>`;
      html += "</tr></thead><tbody>";

      for (let rI = 0; rI < rows.length; rI++) {
        const r = rows[rI];

        let url = (idxUrl >= 0) ? String(r[idxUrl] ?? "").trim() : "";

        // fallback frontend: se l'utente ha scritto solo www.qualcosa
        if (/^www\./i.test(url)) {
          url = "https://" + url;
        }

        const urlOk = /^https?:\/\//i.test(url);

        const trClass = (rI === 0) ? "first-row" : "";
        html += `<tr class="${trClass}">`;

        for (let c = 0; c < headers.length; c++) {
          const cellVal = r[c];
          let content = esc(cellVal);

          // TITLE cliccabile usando la colonna url
          if (c === idxTitle && urlOk) {
            const text = String(cellVal ?? "").trim() || "open";
            content = `<a href="${esc(url)}" target="_blank" rel="noopener">${esc(text)}</a>`;
          }

          // LINK cliccabile anch'es

...[TRUNCATED]...

```

## File: `wsgi.py`
```text
from server import app

application = app

```
