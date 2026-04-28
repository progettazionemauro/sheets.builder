# Sheet Builder / Djungo Builder

Build reusable CRUD web apps starting from exported Google Sheets files.

The project generates a portable mini web application composed of:

- `index.html` — CRUD/admin frontend
- `viewer.html` — public/read-only viewer
- `codice.gs` — Google Apps Script backend

The guiding principle is portability: the generated files remain readable, reusable and owned by the user.

## Current architecture

Frontend:

- `docs/generate.html`
- `docs/review.html`
- `docs/app_ready.html`
- generated `index.html`
- generated `viewer.html`

Backend:

- Flask app in `server.py`
- WSGI entry point in `wsgi.py`
- Gunicorn + systemd on Hetzner
- nginx reverse proxy
- Python parser/generator pipeline

Live URL:

```text
https://builder.sgbh.org/generate.html