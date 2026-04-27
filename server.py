from __future__ import annotations

import json
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

# =========================================================
# APPS CONFIG (slug -> hidden backend config)
# =========================================================
APP_CONFIGS = {
    "horror-movie": {
        "web_app_url": "https://script.google.com/macros/s/AKfycbzmP0437k6Mo5ebcAv3N2Kdx_ZG0IqCVnO3x28YKSrBJ2EclnShUgHJJ1s2NH2od0FQ/exec",
        "api_key": "CHANGE_ME_WRITE_KEY_2026",
    }
}

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
    safe_slug = secure_filename(slug)
    config = APP_CONFIGS.get(safe_slug)

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
        timeout=20,
    )

    resp.raise_for_status()

    return parse_apps_script_response(resp.text)


# =========================================================
# ROUTES
# =========================================================
@app.get("/")
def home():
    return redirect("/generate.html")


@app.get("/health")
def health():
    return jsonify({
        "ok": True,
        "service": "sheet-builder-flask",
    })


# ---------------------------------------------------------
# PARSE INPUT FILES
# ---------------------------------------------------------
@app.post("/api/parse")
def api_parse():
    try:
        xlsx_file = request.files.get("xlsx")
        html_file = request.files.get("html")
        sheet_name = (request.form.get("sheet_name") or "").strip()

        if not xlsx_file:
            return jsonify({"ok": False, "error": "Missing xlsx file"}), 400

        if not html_file:
            return jsonify({"ok": False, "error": "Missing html file"}), 400

        if not sheet_name:
            return jsonify({"ok": False, "error": "Missing sheet_name"}), 400

        session_dir = create_session_dir()

        input_dir = session_dir / "input"
        input_dir.mkdir(parents=True, exist_ok=True)

        xlsx_name = secure_filename(xlsx_file.filename or "input.xlsx")
        html_name = secure_filename(html_file.filename or "input.html")

        xlsx_path = input_dir / xlsx_name
        html_path = input_dir / html_name

        xlsx_file.save(xlsx_path)
        html_file.save(html_path)

        parsed_schema_path = session_dir / "parsed.schema.json"
        builder_state_path = session_dir / "builder_state.json"

        parsed_schema = build_schema_from_directory(
            input_dir=input_dir,
            output_json_path=parsed_schema_path,
            enum_field_name="rating",
            debug=True,
        )

        builder_state = build_builder_state(parsed_schema)

        builder_state["project"]["sheetName"] = sheet_name

        if not builder_state["project"].get("projectName"):
            builder_state["project"]["projectName"] = sheet_name

        if not builder_state["project"].get("projectSlug"):
            builder_state["project"]["projectSlug"] = (
                sheet_name.strip().lower().replace(" ", "-")
            )

        write_json(builder_state_path, builder_state)

        return jsonify({
            "ok": True,
            "session_id": session_dir.name,
            "builder_state": builder_state,
            "paths": {
                "parsed_schema": str(parsed_schema_path),
                "builder_state": str(builder_state_path),
            },
        })

    except Exception as exc:
        return jsonify({
            "ok": False,
            "error": str(exc),
        }), 500


# ---------------------------------------------------------
# GENERATE FINAL FILES
# ---------------------------------------------------------
@app.post("/api/generate")
def api_generate():
    try:
        payload = request.get_json(silent=True) or {}

        session_id = (payload.get("session_id") or "").strip()
        builder_state = payload.get("builder_state")

        if not session_id:
            return jsonify({
                "ok": False,
                "error": "Missing session_id",
            }), 400

        if not isinstance(builder_state, dict):
            return jsonify({
                "ok": False,
                "error": "Missing or invalid builder_state",
            }), 400

        session_dir = get_session_dir(session_id)

        approved_path = session_dir / "approved_configuration.json"
        write_json(approved_path, builder_state)

        project_config, fields_schema = builder_state_to_runtime_data(
            builder_state
        )

        generated = generate_all(project_config, fields_schema)

        generated_root = session_dir / "generated"
        generated_root.mkdir(parents=True, exist_ok=True)

        for relative_path, content in generated.items():
            target = generated_root / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")

        return jsonify({
            "ok": True,
            "session_id": session_id,
            "downloads": {
                "index_html": f"/api/download/{session_id}/index.html",
                "viewer_html": f"/api/download/{session_id}/viewer.html",
                "codice_gs": f"/api/download/{session_id}/codice.gs",
            },
            "generated_root": str(generated_root),
        })

    except Exception as exc:
        return jsonify({
            "ok": False,
            "error": str(exc),
        }), 500


# ---------------------------------------------------------
# DOWNLOAD GENERATED FILES
# ---------------------------------------------------------
@app.get("/api/download/<session_id>/<filename>")
def api_download(session_id: str, filename: str):
    try:
        session_dir = get_session_dir(session_id)
        generated_root = session_dir / "generated"

        mapping = {
            "index.html": generated_root / "docs" / "index.html",
            "viewer.html": generated_root / "docs" / "viewer.html",
            "codice.gs": generated_root / "codice.gs",
        }

        if filename not in mapping:
            return jsonify({
                "ok": False,
                "error": "Invalid filename",
            }), 400

        file_path = mapping[filename]

        if not file_path.exists():
            return jsonify({
                "ok": False,
                "error": "Generated file not found",
            }), 404

        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
        )

    except Exception as exc:
        return jsonify({
            "ok": False,
            "error": str(exc),
        }), 500


# ---------------------------------------------------------
# NEW PROXY ROUTE (SAFE CRUD)
# ---------------------------------------------------------
@app.route("/api/apps/<slug>/<mode>", methods=["GET", "POST"])
def api_app_proxy(slug: str, mode: str):
    try:
        params: Dict[str, Any] = {}

        if request.method == "GET":
            params.update(request.args.to_dict())

        else:
            if request.is_json:
                params.update(request.get_json(silent=True) or {})
            else:
                params.update(request.form.to_dict())

        data = call_apps_script_proxy(
            slug=slug,
            mode=mode,
            params=params,
        )

        return jsonify(data)

    except FileNotFoundError as exc:
        return jsonify({
            "ok": False,
            "error": str(exc),
        }), 404

    except ValueError as exc:
        return jsonify({
            "ok": False,
            "error": str(exc),
        }), 400

    except requests.RequestException as exc:
        return jsonify({
            "ok": False,
            "error": f"Apps Script request failed: {exc}",
        }), 502

    except Exception as exc:
        return jsonify({
            "ok": False,
            "error": str(exc),
        }), 500


# =========================================================
# MAIN
# =========================================================
if __name__ == "__main__":
    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000,
    )