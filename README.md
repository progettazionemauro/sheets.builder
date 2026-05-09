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