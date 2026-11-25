# Sheet Builder / Djungo Builder

Build reusable CRUD web applications from Google Sheets URLs or exported spreadsheets.

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

## CHECKPOINT GS-125 — 2026-11-16

The current local development checkpoint includes:

- Public Google Sheets URL import and worksheet discovery,
  without requiring Google Drive/Sheets OAuth.
- Shared persistent Google Apps Script backend, deployed as
  version 15 on the existing deployment.
- Remote Viewer pagination, global search and sorting.
- Stable record IDs independent of physical spreadsheet rows.
- Display-safe handling of Google Sheets Date values in
  `view` and `getById`.
- Persistent partial-update behavior that skips unchanged
  cells, including cells formatted as dates or times.
- Real CRUD and cell-preservation regression checks passed.

Relevant files include `server.py`,
`generators/google_sheet_source.py`,
`generators/builder_generators.py`, `docs/generate.html`,
and `google/DjungoBackend.gs`.

**Release status:** local source changes still require curated
Git commit, GitHub synchronization, Hetzner staging deployment,
and post-deployment verification. Production is out of scope.

Historical sections above describe earlier project states and
should not be interpreted as the latest release checkpoint.

## Remote column filtering — GS-178 (2026-11-17)

The generated Viewer supports per-column Tabulator header filters
with server-side filtering across the complete Google Sheet,
not only the currently loaded page.

Global search, remote sorting and remote pagination remain available.
Column definitions derive dynamically from the spreadsheet headers;
no dataset-specific column names are hardcoded.

Architecture: Tabulator 6.4 -> Flask proxy -> persistent Google
Apps Script backend -> Google Sheets.

Release checkpoint:
- GAS existing web-app deployment: version 16.
- Source commit: `7468f9e`.
- GitHub and Hetzner staging synchronized.
- Staging runtime Viewer updated and browser-tested.
- Production unchanged.

Generated runtime HTML files are protected artifacts:
deploying the generator does not automatically replace an
already generated Viewer. GAS deployment is managed separately.

## Current development status — 2026-11-25

### Google Sheets workflow

Djungo supports Google Sheets URL import and an alternative
file-based import workflow.

The intended experience is:

Google Sheet -> Import -> Read-only Preview ->
Customize -> Activate -> Persistent CRUD application.

The spreadsheet remains the primary data source.

### Internationalization

English and Italian localization is implemented through
a shared JavaScript engine and JSON dictionaries:

- `docs/i18n/i18n.js`
- `docs/i18n/en.json`
- `docs/i18n/it.json`

The selected language is stored in browser localStorage.

Generate and Review have been localized and browser-tested.
Review also supports dynamically generated translations.

Localization of the generated Preview, CRUD interface and
Viewer remains under development.

Spreadsheet values, original column names and user-defined
labels are not translated.

### Navigation and persistent applications

Review provides simplified navigation with Home Djungo,
Save changes and Exit without saving.

The CRUD/Preview generator now includes Home Djungo.
Its presence has been verified in a persistent application.

Full browser testing of unsaved-change navigation safeguards
and all Review entry paths remains open.

Persistent application HTML is generated dynamically by
Flask using the current Python generator and the saved
application configuration.

### Release status

F44-F48E changes are implemented locally and have not yet
been declared synchronized with GitHub and Hetzner staging.

The deployed Google Apps Script project remains the
authoritative backend source. GAS deployment is separate
from the Flask/Git release process.

Protected runtime data and generated artifacts must not
be overwritten by deployment.

Production is excluded from the current release.
