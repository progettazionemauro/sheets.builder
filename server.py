from __future__ import annotations

import json
import re
import uuid
import zipfile
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
from generators.google_sheet_source import (
    download_google_sheet_xlsx,
    list_google_sheet_tabs,
    parse_google_sheet_url,
)


ROOT = Path(__file__).resolve().parent
DOCS_DIR = ROOT / "docs"
WORKDIR = ROOT / "workdir" / "flask_sessions"
DATA_DIR = ROOT / "data"
APPS_REGISTRY_PATH = DATA_DIR / "apps_registry.json"
PERSISTENT_APPS_PATH = DATA_DIR / "persistent_apps.json"
PERSISTENT_BACKEND_PATH = DATA_DIR / "persistent_backend.json"

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

    # Mantiene coerenti schema generale e singoli campi.
    from copy import deepcopy

    fields = [deepcopy(field) for field in fields]

    for field in fields:
        name = field["name"]

        if field.get("type") == "enum" and name in enum_styles:
            field["enumStyles"] = deepcopy(enum_styles[name])


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


def load_persistent_apps() -> Dict[str, Any]:
    if not PERSISTENT_APPS_PATH.exists():
        return {
            "configVersion": 1,
            "apps": {},
        }

    raw = PERSISTENT_APPS_PATH.read_text(encoding="utf-8").strip()

    if not raw:
        return {
            "configVersion": 1,
            "apps": {},
        }

    registry = json.loads(raw)

    if registry.get("configVersion") != 1:
        raise ValueError("Unsupported persistent apps configVersion")

    if not isinstance(registry.get("apps"), dict):
        raise ValueError("Invalid persistent apps registry")

    return registry


def load_persistent_backend_config() -> Dict[str, str]:
    if not PERSISTENT_BACKEND_PATH.exists():
        raise FileNotFoundError(
            "Persistent backend configuration not found"
        )

    raw = PERSISTENT_BACKEND_PATH.read_text(encoding="utf-8").strip()

    if not raw:
        raise ValueError("Persistent backend configuration is empty")

    config = json.loads(raw)

    if config.get("configVersion") != 1:
        raise ValueError(
            "Unsupported persistent backend configVersion"
        )

    web_app_url = str(config.get("web_app_url") or "").strip()
    api_key = str(config.get("api_key") or "").strip()

    if not web_app_url:
        raise ValueError(
            "Persistent backend web_app_url is missing"
        )

    if not api_key:
        raise ValueError(
            "Persistent backend api_key is missing"
        )

    return {
        "web_app_url": web_app_url,
        "api_key": api_key,
    }


def save_persistent_apps(registry: Dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    write_json(PERSISTENT_APPS_PATH, registry)


def register_persistent_app(
    app_config: Dict[str, Any],
) -> Dict[str, Any]:
    requested_slug = slugify_app_name(app_config.get("appSlug"))

    if not requested_slug:
        raise ValueError("Missing appSlug")

    spreadsheet_id = str(app_config.get("spreadsheetId") or "").strip()
    sheet_id = str(app_config.get("sheetId", "")).strip()

    if not spreadsheet_id or not sheet_id:
        raise ValueError("Missing persistent sheet identity")

    registry = load_persistent_apps()
    apps = registry["apps"]

    matching_slugs = [
        slug
        for slug, config in apps.items()
        if (
            str(config.get("spreadsheetId") or "").strip(),
            str(config.get("sheetId", "")).strip(),
        ) == (spreadsheet_id, sheet_id)
    ]

    if len(matching_slugs) > 1:
        raise ValueError(
            "Duplicate persistent registrations for the same sheet"
        )

    if matching_slugs:
        app_slug = matching_slugs[0]
    else:
        app_slug = requested_slug

        if app_slug in apps:
            raise ValueError(
                f"App slug already belongs to another sheet: {app_slug}"
            )

    stored_config = dict(app_config)
    stored_config["appSlug"] = app_slug

    apps[app_slug] = stored_config
    save_persistent_apps(registry)

    return stored_config


def build_persistent_app_config(
    project_config: Dict[str, Any],
    fields_schema: Dict[str, Any],
) -> Dict[str, Any]:
    source = dict(project_config.get("source", {}) or {})

    if source.get("type") != "google_sheet":
        raise ValueError(
            "Persistent backend requires a Google Sheet source"
        )

    spreadsheet_id = str(source.get("spreadsheetId") or "").strip()
    sheet_id = str(source.get("sheetId", "")).strip()
    sheet_name = str(source.get("sheetName") or "").strip()

    if not spreadsheet_id:
        raise ValueError("Missing source spreadsheetId")

    if not sheet_id:
        raise ValueError("Missing source sheetId")

    if not sheet_name:
        raise ValueError("Missing source sheetName")

    try:
        sheet_id_value = int(sheet_id)
    except ValueError as exc:
        raise ValueError("Invalid source sheetId") from exc

    app_slug = slugify_app_name(
        project_config.get("projectSlug")
        or project_config.get("projectName")
    )

    return {
        "configVersion": 1,
        "appSlug": app_slug,
        "spreadsheetId": spreadsheet_id,
        "sheetId": sheet_id_value,
        "sheetName": sheet_name,
        "projectName": project_config.get("projectName", sheet_name),
        "entityName": project_config.get("entityName", sheet_name),
        "schema": fields_schema,
    }



def restore_saved_sheet_preferences(builder_state, registry):
    from copy import deepcopy

    state = deepcopy(builder_state)
    project = state.get("project", {})
    source = project.get("source", {})

    identity = (
        str(source.get("spreadsheetId", "")).strip(),
        str(source.get("sheetId", "")).strip(),
    )

    matches = [
        (slug, config)
        for slug, config in registry.get("apps", {}).items()
        if (
            str(config.get("spreadsheetId", "")).strip(),
            str(config.get("sheetId", "")).strip(),
        ) == identity
    ]

    if not matches:
        return state

    if len(matches) != 1:
        raise ValueError("Duplicate registered sheet identity")

    slug, config = matches[0]
    project["projectSlug"] = slug

    for key in ("projectName", "entityName"):
        if config.get(key):
            project[key] = config[key]

    saved_schema = config.get("schema", {})

    saved_fields = {
        field["name"]: field
        for field in saved_schema.get("fields", [])
    }

    presentation_keys = (
        "label",
        "sortType",
        "displayType",
        "visibleInViewer",
    )

    fresh_enums = state.get("enums", {})
    saved_enums = saved_schema.get("enums", {})
    saved_styles = saved_schema.get("enumStyles", {})

    for field in state.get("fields", []):
        name = field["name"]
        previous = saved_fields.get(name)

        if not previous:
            continue

        if previous.get("type") != field.get("type"):
            continue

        for key in presentation_keys:
            if key in previous:
                field[key] = deepcopy(previous[key])

        if not field.get("computed") and not field.get("locked"):
            for key in ("required", "visibleInForm"):
                if key in previous:
                    field[key] = deepcopy(previous[key])

        # Recupera i colori se l'enumeratore non e' cambiato.
        if (
            field.get("type") == "enum"
            and name in fresh_enums
            and name in saved_enums
            and fresh_enums[name] == saved_enums[name]
            and name in saved_styles
        ):
            state.setdefault("enumStyles", {})[name] = (
                deepcopy(saved_styles[name])
            )

    return state



# ---------------------------------------------------------
# UAT-F19 — PERSISTENT APPLICATION RENDERING
# ---------------------------------------------------------


# UAT-F37: persistent preview preferences

def sheet_identity_(source):
    return (
        str(source.get("spreadsheetId", "")).strip(),
        str(source.get("sheetId", "")).strip(),
    )


def preview_preferences_path(source):
    import hashlib

    identity = sheet_identity_(source)

    if not all(identity):
        raise ValueError("Missing sheet identity")

    key = hashlib.sha256(
        json.dumps(identity).encode("utf-8")
    ).hexdigest()

    return DATA_DIR / "preview_preferences" / (key + ".json")


def registered_sheet_slug(source, registry):
    identity = sheet_identity_(source)

    matches = [
        slug
        for slug, config in registry["apps"].items()
        if sheet_identity_(config) == identity
    ]

    if len(matches) > 1:
        raise ValueError("Duplicate registered sheet identity")

    return matches[0] if matches else None


def restore_all_sheet_preferences(state):
    source = state["project"]["source"]
    registry = load_persistent_apps()

    if registered_sheet_slug(source, registry):
        return restore_saved_sheet_preferences(
            state, registry
        )

    path = preview_preferences_path(source)

    if not path.is_file():
        return state

    config = json.loads(
        path.read_text(encoding="utf-8")
    )

    return restore_saved_sheet_preferences(
        state,
        {"apps": {config["appSlug"]: config}},
    )


def prepare_preview_preferences(state):
    source = state["project"]["source"]
    registry = load_persistent_apps()
    slug = registered_sheet_slug(source, registry)

    if slug:
        current = get_persistent_builder_state(
            slug, registry=registry
        )

        if current.get("enums", {}) != state.get("enums", {}):
            raise ValueError(
                "Spreadsheet enumerations have changed. "
                "Review the application structure first."
            )

        merged = merge_persistent_preferences(
            current, state
        )

        project, schema = builder_state_to_runtime_data(
            merged
        )

        config = dict(registry["apps"][slug])
        config["schema"] = schema
        config["projectName"] = project["projectName"]
        config["entityName"] = project["entityName"]

        registry["apps"][slug] = config

        return "active", registry

    project, schema = builder_state_to_runtime_data(state)

    return "draft", build_persistent_app_config(
        project, schema
    )


def commit_preview_preferences(state, pending):
    kind, data = pending

    if kind == "active":
        save_persistent_apps(data)
    else:
        write_json(
            preview_preferences_path(
                state["project"]["source"]
            ),
            data,
        )


def get_persistent_builder_state(slug, registry=None):
    from copy import deepcopy

    if registry is None:
        registry = load_persistent_apps()
    config = registry["apps"].get(slug)

    if config is None:
        raise FileNotFoundError("Application not found")

    schema = config.get("schema")

    if not isinstance(schema, dict):
        raise ValueError("Invalid application schema")

    sheet_name = config["sheetName"]

    return {
        "project": {
            "projectName": config.get("projectName") or sheet_name,
            "entityName": config.get("entityName") or sheet_name,
            "projectSlug": slug,
            "sheetName": sheet_name,
            "source": {
                "type": "google_sheet",
                "spreadsheetId": config["spreadsheetId"],
                "sheetId": str(config["sheetId"]),
                "sheetName": sheet_name,
            },
        },
        "fields": deepcopy(schema["fields"]),
        "constraints": deepcopy(schema.get("constraints", {})),
        "enums": deepcopy(schema.get("enums", {})),
        "enumStyles": deepcopy(schema.get("enumStyles", {})),
    }


@app.get("/api/configuration/<slug>")
def api_persistent_configuration(slug):
    try:
        response = jsonify({
            "ok": True,
            "builder_state": get_persistent_builder_state(slug),
        })

        response.headers["Cache-Control"] = "no-store"
        return response

    except FileNotFoundError:
        return jsonify({
            "ok": False,
            "error": "Application not found",
        }), 404



def merge_persistent_preferences(current, proposed):
    from copy import deepcopy

    if not isinstance(proposed, dict):
        raise ValueError("Invalid configuration")

    result = deepcopy(current)

    old_project = current["project"]
    new_project = proposed.get("project", {})

    old_source = old_project["source"]
    new_source = new_project.get("source", {})

    for key in ("spreadsheetId", "sheetId"):
        if str(old_source[key]) != str(new_source.get(key)):
            raise ValueError("Spreadsheet identity cannot be changed")

    if old_project["projectSlug"] != new_project.get("projectSlug"):
        raise ValueError("Application identity cannot be changed")

    incoming = proposed.get("fields")

    if not isinstance(incoming, list):
        raise ValueError("Missing fields")

    by_name = {
        field["name"]: field
        for field in incoming
    }

    expected = {
        field["name"]
        for field in result["fields"]
    }

    if len(by_name) != len(incoming) or set(by_name) != expected:
        raise ValueError("Spreadsheet structure cannot be changed here")

    for field in result["fields"]:
        candidate = by_name[field["name"]]

        if candidate.get("type") != field.get("type"):
            raise ValueError("Field type cannot be changed here")

        if "label" in candidate:
            value = candidate["label"]

            if not isinstance(value, str):
                raise ValueError("Invalid display label")

            field["label"] = value

        allowed = {
            "sortType": (
                "auto", "string", "number",
                "date_it", "datetime_it"
            ),
            "displayType": ("text", "link", "image"),
        }

        for key, values in allowed.items():
            if key in candidate:
                if candidate[key] not in values:
                    raise ValueError("Invalid field preference")
                field[key] = candidate[key]

        boolean_keys = ["visibleInViewer"]

        if not field.get("computed") and not field.get("locked"):
            boolean_keys += ["required", "visibleInForm"]

        for key in boolean_keys:
            if key in candidate:
                if not isinstance(candidate[key], bool):
                    raise ValueError("Invalid boolean preference")
                field[key] = candidate[key]

    styles = proposed.get("enumStyles", {})

    if not isinstance(styles, dict):
        raise ValueError("Invalid enum styles")

    for field in result["fields"]:
        name = field["name"]

        if field.get("type") == "enum" and name in styles:
            result.setdefault("enumStyles", {})[name] = (
                deepcopy(styles[name])
            )

    for key in ("projectName", "entityName"):
        value = new_project.get(key)

        if isinstance(value, str) and value.strip():
            result["project"][key] = value

    for field in result["fields"]:
        name = field["name"]

        if (
            field.get("type") == "enum"
            and name in result.get("enumStyles", {})
        ):
            field["enumStyles"] = deepcopy(
                result["enumStyles"][name]
            )

    return result


@app.post("/api/configuration/<slug>")
def api_save_persistent_configuration(slug):
    try:
        registry = load_persistent_apps()

        current = get_persistent_builder_state(
            slug, registry=registry
        )

        payload = request.get_json(silent=True) or {}

        state = merge_persistent_preferences(
            current,
            payload.get("builder_state"),
        )

        project, schema = builder_state_to_runtime_data(state)

        config = dict(registry["apps"][slug])

        config["schema"] = schema
        config["projectName"] = project["projectName"]
        config["entityName"] = project["entityName"]

        registry["apps"][slug] = config

        save_persistent_apps(registry)

        return jsonify({
            "ok": True,
            "app_slug": slug,
            "builder_state": state,
        })

    except FileNotFoundError:
        return jsonify({
            "ok": False,
            "error": "Application not found",
        }), 404

    except (ValueError, TypeError, KeyError, AttributeError) as exc:
        return jsonify({
            "ok": False,
            "error": str(exc),
        }), 400


@app.get("/application/<slug>/<filename>")
def render_persistent_application(slug, filename):
    from flask import Response
    from generators.builder_generators import (
        generate_index_html,
        generate_viewer_html,
    )

    try:
        if filename not in ("index.html", "viewer.html"):
            return jsonify({
                "ok": False,
                "error": "Invalid application filename",
            }), 400

        state = get_persistent_builder_state(slug)

        project, schema = builder_state_to_runtime_data(state)

        generator = (
            generate_index_html
            if filename == "index.html"
            else generate_viewer_html
        )

        html = generator(project, schema)

        response = Response(
            html,
            content_type="text/html; charset=utf-8",
        )

        response.headers["Cache-Control"] = "no-store"
        return response

    except FileNotFoundError:
        return jsonify({
            "ok": False,
            "error": "Application not found",
        }), 404


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


def process_builder_input(
    session_dir: Path,
    input_dir: Path,
    sheet_name: str,
    xlsx_sheet_name: str | None = None,
) -> tuple[Dict[str, Any], Path, Path]:
    parsed_schema_path = session_dir / "parsed.schema.json"
    builder_state_path = session_dir / "builder_state.json"

    effective_xlsx_sheet_name = xlsx_sheet_name or sheet_name

    parsed_schema = build_schema_from_directory(
        input_dir=input_dir,
        output_json_path=parsed_schema_path,
        enum_field_name="rating",
        sheet_name=effective_xlsx_sheet_name,
        debug=True,
    )

    builder_state = build_builder_state(parsed_schema)

    project_slug = slugify_app_name(sheet_name)

    builder_state["project"]["sheetName"] = sheet_name
    builder_state["project"]["projectName"] = sheet_name
    builder_state["project"]["projectSlug"] = project_slug
    builder_state["project"]["backendName"] = f"{project_slug}-backend"

    write_json(builder_state_path, builder_state)

    return builder_state, parsed_schema_path, builder_state_path


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
    *,
    activation_config=None,
) -> Dict[str, Any]:
    if mode not in ALL_PROXY_MODES:
        raise ValueError(f"Invalid mode: {mode}")

    safe_slug = slugify_app_name(slug)

    # Routing persistente:
    # appSlug -> spreadsheetId + sheetId + schema
    persistent_registry = load_persistent_apps()
    persistent_config = (
        activation_config
        if activation_config is not None
        else persistent_registry.get("apps", {}).get(safe_slug)
    )

    # Le app persistenti condividono un unico backend GAS.
    # Le app non ancora migrate continuano a usare
    # il routing per-app presente in apps_registry.json.
    if persistent_config:
        config = load_persistent_backend_config()
    else:
        config = get_app_config(safe_slug)

    outbound = {
        "mode": mode,
        "cb": "djungoProxy",
    }

    # Parametri tecnici controllati esclusivamente dal server.
    reserved_params = {
        "mode",
        "apiKey",
        "webApp",
        "cb",
        "_",
        "appSlug",
        "spreadsheetId",
        "sheetId",
    }

    for key, value in params.items():
        if key in reserved_params:
            continue
        outbound[key] = value

    # Se l'app possiede la configurazione persistente B1,
    # Flask aggiunge il routing tecnico verso il Sheet.
    #
    # Le app precedenti, non ancora migrate a B1/B2,
    # continuano invece a usare il comportamento esistente.
    if persistent_config:
        outbound["appSlug"] = safe_slug
        outbound["spreadsheetId"] = persistent_config["spreadsheetId"]
        outbound["sheetId"] = str(persistent_config["sheetId"])

    if mode in PROTECTED_MODES:
        outbound["apiKey"] = config["api_key"]

    resp = requests.get(
        config["web_app_url"],
        params=outbound,
        timeout=45,
    )

    resp.raise_for_status()

    return parse_apps_script_response(resp.text)


# =========================================================
# ROUTES
# =========================================================

# UAT-F44: shared language resources.
@app.get("/i18n/<filename>")
def djungo_i18n_resource(filename):
    from flask import abort, send_from_directory

    allowed = {"i18n.js", "en.json", "it.json"}

    if filename not in allowed:
        abort(404)

    response = send_from_directory(
        DOCS_DIR / "i18n",
        filename,
    )

    response.headers["Cache-Control"] = "no-cache"
    return response


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

        builder_state, parsed_schema_path, builder_state_path = process_builder_input(
            session_dir=session_dir,
            input_dir=input_dir,
            sheet_name=sheet_name,
        )

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
# IMPORT FROM GOOGLE SHEET
# ---------------------------------------------------------

@app.get("/api/google-sheet/tabs")
def api_google_sheet_tabs():
    url = (request.args.get("url") or "").strip()

    try:
        spreadsheet_id, _ = parse_google_sheet_url(url)
        tabs = list_google_sheet_tabs(url)

        return jsonify({
            "ok": True,
            "spreadsheet_id": spreadsheet_id,
            "tabs": tabs,
        })

    except ValueError as exc:
        return jsonify({
            "ok": False,
            "error": str(exc),
        }), 400

    except requests.RequestException:
        return jsonify({
            "ok": False,
            "error": "Unable to retrieve Google Sheets metadata",
        }), 502


@app.post("/api/google-sheet/import")
def api_google_sheet_import():
    try:
        xlsx_file = request.files.get("xlsx")
        zip_file = request.files.get("web_export")
        google_sheet_url = (request.form.get("google_sheet_url") or "").strip()

        spreadsheet_id = (request.form.get("spreadsheet_id") or "").strip()
        spreadsheet_name = (request.form.get("spreadsheet_name") or "").strip()
        sheet_id = (request.form.get("sheet_id") or "").strip()
        sheet_name = (request.form.get("sheet_name") or "").strip()

        if google_sheet_url:
            if xlsx_file or zip_file:
                return jsonify({
                    "ok": False,
                    "error": "Choose URL import or file upload, not both",
                }), 400

            url_xlsx, url_spreadsheet_id, url_gid = (
                download_google_sheet_xlsx(google_sheet_url)
            )

            if spreadsheet_id and spreadsheet_id != url_spreadsheet_id:
                return jsonify({
                    "ok": False,
                    "error": "Spreadsheet ID does not match URL",
                }), 400

            spreadsheet_id = url_spreadsheet_id
            if not sheet_id:
                sheet_id = url_gid or ""

            tabs = list_google_sheet_tabs(google_sheet_url)
            selected_tab = next(
                (tab for tab in tabs if tab["sheetId"] == sheet_id),
                None,
            )

            if not selected_tab or selected_tab["sheetName"] != sheet_name:
                return jsonify({
                    "ok": False,
                    "error": "Sheet name and gid do not match",
                }), 400
        else:
            if not xlsx_file:
                return jsonify({"ok": False, "error": "Missing xlsx file"}), 400

            if not zip_file:
                return jsonify({"ok": False, "error": "Missing web_export file"}), 400

        if not spreadsheet_id:
            return jsonify({"ok": False, "error": "Missing spreadsheet_id"}), 400

        if not sheet_id:
            return jsonify({"ok": False, "error": "Missing sheet_id"}), 400

        if not sheet_name:
            return jsonify({"ok": False, "error": "Missing sheet_name"}), 400

        session_dir = create_session_dir()

        input_dir = session_dir / "input"
        input_dir.mkdir(parents=True, exist_ok=True)

        xlsx_path = input_dir / "input.xlsx"
        zip_path = session_dir / "google-web-export.zip"

        if google_sheet_url:
            xlsx_path.write_bytes(url_xlsx)
        else:
            xlsx_file.save(xlsx_path)
            zip_file.save(zip_path)

        if zip_file:
            extract_dir = session_dir / "web_export"
            extract_dir.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(zip_path, "r") as archive:
                for member in archive.infolist():
                    member_path = Path(member.filename)

                    if member_path.is_absolute() or ".." in member_path.parts:
                        raise ValueError(
                            f"Unsafe ZIP member path: {member.filename}"
                        )

                    target_path = extract_dir / member_path

                    if member.is_dir():
                        target_path.mkdir(parents=True, exist_ok=True)
                        continue

                    target_path.parent.mkdir(parents=True, exist_ok=True)

                    with archive.open(member, "r") as source:
                        with target_path.open("wb") as target:
                            target.write(source.read())

            html_candidates = [
                path
                for path in extract_dir.rglob("*.html")
                if path.stem == sheet_name
            ]

            if len(html_candidates) != 1:
                raise ValueError(
                    "Could not uniquely identify HTML for selected sheet "
                    f"{sheet_name!r}; found {len(html_candidates)} matches"
                )

            selected_html = html_candidates[0]
            html_path = input_dir / "input.html"
            html_path.write_bytes(selected_html.read_bytes())

        from openpyxl import load_workbook

        wb = load_workbook(
            filename=xlsx_path,
            read_only=True,
            data_only=False,
        )

        try:
            if sheet_name in wb.sheetnames:
                xlsx_sheet_name = sheet_name
            elif sheet_name[:31] in wb.sheetnames:
                xlsx_sheet_name = sheet_name[:31]
            else:
                raise ValueError(
                    "Could not identify selected sheet inside XLSX. "
                    f"Google sheet name: {sheet_name!r}; "
                    f"XLSX worksheets: {wb.sheetnames!r}"
                )
        finally:
            wb.close()

        builder_state, parsed_schema_path, builder_state_path = process_builder_input(
            session_dir=session_dir,
            input_dir=input_dir,
            sheet_name=sheet_name,
            xlsx_sheet_name=xlsx_sheet_name,
        )

        builder_state["project"]["source"] = {
            "type": "google_sheet",
            "spreadsheetId": spreadsheet_id,
            "spreadsheetName": spreadsheet_name,
            "sheetId": sheet_id,
            "sheetName": sheet_name,
        }

        builder_state = restore_all_sheet_preferences(
            builder_state
        )

        write_json(builder_state_path, builder_state)

        # Configurazione autorevole della sessione Preview.
        write_json(
            session_dir / "preview_configuration.json",
            builder_state,
        )

        # UAT-F07: origine dati dell'anteprima nella sessione.
        write_json(
            session_dir / "preview_source.json",
            {"xlsx_sheet_name": xlsx_sheet_name},
        )

        return jsonify({
            "ok": True,
            "session_id": session_dir.name,
            "builder_state": builder_state,
            "google_source": {
                "spreadsheet_id": spreadsheet_id,
                "spreadsheet_name": spreadsheet_name,
                "sheet_id": sheet_id,
                "sheet_name": sheet_name,
            },
            "paths": {
                "parsed_schema": str(parsed_schema_path),
                "builder_state": str(builder_state_path),
            },
        })

    except zipfile.BadZipFile:
        return jsonify({
            "ok": False,
            "error": "Invalid Google web export ZIP",
        }), 400

    except Exception as exc:
        return jsonify({
            "ok": False,
            "error": str(exc),
        }), 500


# ---------------------------------------------------------
# GENERATE FINAL FILES
# ---------------------------------------------------------


# ---------------------------------------------------------
# UAT-F07 — READ-ONLY PREVIEW DATA
# ---------------------------------------------------------

def read_preview_data(xlsx_path, sheet_name, limit=50):
    from openpyxl import load_workbook
    from datetime import date, datetime, time

    wb = load_workbook(
        xlsx_path,
        read_only=True,
        data_only=True,
    )

    def normalize(value):
        if isinstance(value, (date, datetime, time)):
            return value.isoformat()
        if value is None:
            return ""
        if isinstance(value, (str, int, float, bool)):
            return value
        return str(value)

    try:
        ws = wb[sheet_name]
        iterator = ws.iter_rows(values_only=True)
        headers = [
            str(v).strip() if v is not None else ""
            for v in next(iterator, ())
        ]

        while headers and not headers[-1]:
            headers.pop()

        if not headers:
            raise ValueError("No headers found")

        rows = []
        total = 0

        for raw in iterator:
            row = raw[:len(headers)]

            if not any(v is not None and v != "" for v in row):
                continue

            total += 1

            if len(rows) < limit:
                rows.append([normalize(v) for v in row])

        return {
            "ok": True,
            "preview": True,
            "headers": headers,
            "rows": rows,
            "totalRows": total,
            "previewRows": len(rows),
            "truncated": total > len(rows),
        }

    finally:
        wb.close()


@app.get("/api/preview/<session_id>/data")
def api_preview_data(session_id):
    import json

    if not session_id or len(session_id) > 128:
        return jsonify({"ok": False, "error": "Invalid session"}), 400

    if not all(c.isalnum() or c in "-_" for c in session_id):
        return jsonify({"ok": False, "error": "Invalid session"}), 400

    session_dir = get_session_dir(session_id)
    manifest = session_dir / "preview_source.json"
    xlsx_path = session_dir / "input" / "input.xlsx"

    if not manifest.is_file() or not xlsx_path.is_file():
        return jsonify({
            "ok": False,
            "error": "Preview unavailable. Import the sheet again.",
        }), 404

    try:
        source = json.loads(manifest.read_text(encoding="utf-8"))

        return jsonify(read_preview_data(
            xlsx_path,
            source["xlsx_sheet_name"],
        ))

    except Exception:
        return jsonify({
            "ok": False,
            "error": "Could not read preview data",
        }), 500


@app.get("/api/session/<session_id>")
def api_get_session(session_id: str):
    try:
        safe_session_id = secure_filename(session_id)

        if not safe_session_id or safe_session_id != session_id:
            return jsonify({
                "ok": False,
                "error": "Invalid session_id",
            }), 400

        session_dir = get_session_dir(session_id)
        builder_state_path = session_dir / "builder_state.json"

        if not builder_state_path.exists():
            return jsonify({
                "ok": False,
                "error": "Builder state not found",
            }), 404

        builder_state = json.loads(
            builder_state_path.read_text(encoding="utf-8")
        )

        return jsonify({
            "ok": True,
            "session_id": session_id,
            "builder_state": builder_state,
        })

    except FileNotFoundError as exc:
        return jsonify({
            "ok": False,
            "error": str(exc),
        }), 404

    except Exception as exc:
        return jsonify({
            "ok": False,
            "error": str(exc),
        }), 500



# ---------------------------------------------------------
# UAT-F08 — ISOLATED APPLICATION PREVIEW
# ---------------------------------------------------------

def preview_session_dir(session_id):
    if not session_id or len(session_id) > 128:
        raise ValueError("Invalid session ID")

    if not all(c.isalnum() or c in "-_" for c in session_id):
        raise ValueError("Invalid session ID")

    return get_session_dir(session_id)



# UAT-F41: application activation independent of HTML generation.

def verify_activation_backend(config):
    slug = config["appSlug"]

    response = call_apps_script_proxy(
        slug,
        "meta",
        {},
        activation_config=config,
    )

    if not isinstance(response, dict) or response.get("ok") is not True:
        raise ValueError(
            "Backend unavailable for this spreadsheet. "
            "Your preview and saved configuration remain available."
        )

    if (
        sheet_identity_(response) != sheet_identity_(config)
        or response.get("appSlug") != slug
    ):
        raise ValueError(
            "Backend identity mismatch. "
            "Application not activated."
        )

    return response


@app.route(
    "/api/preview/<session_id>/activation",
    methods=["GET", "POST"],
)
def api_preview_activation(session_id):
    try:
        session_dir = preview_session_dir(session_id)

        path = session_dir / "preview_configuration.json"

        if not path.is_file():
            return jsonify({
                "ok": False,
                "error": "Reimport the spreadsheet before activation",
            }), 404

        # La configurazione proviene dal server,
        # non da un payload modificabile nel browser.
        state = json.loads(
            path.read_text(encoding="utf-8")
        )

        source = state["project"]["source"]
        registry = load_persistent_apps()
        existing = registered_sheet_slug(source, registry)

        if request.method == "GET":
            response = jsonify({
                "ok": True,
                "registered": existing is not None,
                "app_slug": existing,
            })

            response.headers["Cache-Control"] = "no-store"
            return response

        # Apertura senza rigenerazione o nuova registrazione.
        if existing:
            return jsonify({
                "ok": True,
                "app_slug": existing,
                "already_registered": True,
            })

        fields = state.get("fields", [])

        if (
            not fields
            or str(fields[0].get("name", "")).lower() != "id"
            or fields[0].get("type") != "int"
        ):
            raise ValueError(
                "The first column must contain integer record IDs."
            )

        project, schema = builder_state_to_runtime_data(state)
        config = build_persistent_app_config(project, schema)

        slug = config["appSlug"]

        if slug in registry["apps"]:
            raise ValueError(
                "Application name already belongs to another sheet."
            )

        # Nessuna registrazione prima della verifica del backend.
        verify_activation_backend(config)

        registered = register_persistent_app(config)

        return jsonify({
            "ok": True,
            "app_slug": registered["appSlug"],
            "already_registered": False,
        })

    except FileNotFoundError:
        return jsonify({
            "ok": False,
            "error": "Preview or backend configuration unavailable",
        }), 404

    except (ValueError, TypeError, KeyError) as exc:
        return jsonify({
            "ok": False,
            "error": str(exc),
        }), 400

    except requests.RequestException:
        return jsonify({
            "ok": False,
            "error": "Cannot reach the configured Apps Script backend",
        }), 502


@app.post("/api/preview/<session_id>/generate")
def api_preview_generate(session_id):
    try:
        session_dir = preview_session_dir(session_id)

        if not (
            (session_dir / "preview_source.json").is_file()
            and (session_dir / "input" / "input.xlsx").is_file()
        ):
            return jsonify({
                "ok": False,
                "error": "Import the spreadsheet before generating a preview",
            }), 404

        payload = request.get_json(silent=True) or {}
        builder_state = payload.get("builder_state")

        if not isinstance(builder_state, dict):
            return jsonify({
                "ok": False,
                "error": "Missing or invalid builder_state",
            }), 400

        save_preferences = payload.get(
            "save_preferences", False
        )

        if not isinstance(save_preferences, bool):
            raise ValueError("Invalid save_preferences")

        pending = None

        canonical_path = (
            session_dir / "preview_configuration.json"
        )

        if save_preferences:
            if not canonical_path.is_file():
                return jsonify({
                    "ok": False,
                    "error": "Import the sheet again before saving",
                }), 409

            current = json.loads(
                canonical_path.read_text(encoding="utf-8")
            )

            builder_state = merge_persistent_preferences(
                current, builder_state
            )

            pending = prepare_preview_preferences(
                builder_state
            )

        project_config, fields_schema = builder_state_to_runtime_data(
            builder_state
        )

        generated = generate_all(
            project_config,
            fields_schema,
            include_gas=False,
        )

        preview_root = session_dir / "preview" / "docs"

        filenames = ("index.html", "viewer.html")

        for filename in filenames:
            if f"docs/{filename}" not in generated:
                raise ValueError("Missing generated preview file")

        preview_root.mkdir(parents=True, exist_ok=True)

        for filename in filenames:
            target = preview_root / filename
            target.write_text(
                generated[f"docs/{filename}"],
                encoding="utf-8",
            )

        if pending is not None:
            commit_preview_preferences(
                builder_state, pending
            )

            write_json(
                canonical_path, builder_state
            )

        return jsonify({
            "ok": True,
            "preview": True,
            "session_id": session_id,
            "preferences_saved": pending is not None,
            "builder_state": builder_state,
            "preview_url": f"/preview/{session_id}/index.html",
        })

    except ValueError as exc:
        return jsonify({
            "ok": False,
            "error": str(exc),
        }), 400

    except Exception:
        return jsonify({
            "ok": False,
            "error": "Preview generation failed",
        }), 500


@app.get("/preview/<session_id>/<filename>")
def serve_preview(session_id, filename):
    try:
        session_dir = preview_session_dir(session_id)

        if filename not in ("index.html", "viewer.html"):
            return jsonify({
                "ok": False,
                "error": "Invalid preview filename",
            }), 400

        target = session_dir / "preview" / "docs" / filename

        if not target.is_file():
            return jsonify({
                "ok": False,
                "error": "Preview not found",
            }), 404

        response = send_file(target, as_attachment=False)
        response.headers["Cache-Control"] = "no-store"
        return response

    except ValueError:
        return jsonify({
            "ok": False,
            "error": "Invalid session",
        }), 400


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

        source = dict(project_config.get("source", {}) or {})

        registered_app_slug = None

        if source.get("type") == "google_sheet":
            persistent_app_config = build_persistent_app_config(
                project_config,
                fields_schema,
            )

            persistent_config_path = (
                session_dir / "persistent" / "app_config.json"
            )
            write_json(
                persistent_config_path,
                persistent_app_config,
            )

            registered_config = register_persistent_app(
                persistent_app_config
            )
            registered_app_slug = registered_config["appSlug"]

        generated = generate_all(
            project_config,
            fields_schema,
            include_gas=source.get("type") != "google_sheet",
        )

        generated_root = session_dir / "generated"
        generated_root.mkdir(parents=True, exist_ok=True)

        for relative_path, content in generated.items():
            target = generated_root / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")

        # Also publish generated runtime files to the Flask static folder.
        # This makes the updated CRUD/viewer immediately visible in the browser.
        for relative_path, content in generated.items():
            target = ROOT / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")

        return jsonify({
            "ok": True,
            "session_id": session_id,
            "app_slug": registered_app_slug,
            "downloads": {
                "index_html": f"/api/download/{session_id}/index.html",
                "viewer_html": f"/api/download/{session_id}/viewer.html",
                "codice_gs": (
                    f"/api/download/{session_id}/codice.gs"
                    if "codice.gs" in generated else None
                ),
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

@app.get("/run/<session_id>/<filename>")
def run_generated_app(session_id: str, filename: str):
    try:
        session_dir = get_session_dir(session_id)
        generated_root = session_dir / "generated"

        mapping = {
            "index.html": generated_root / "docs" / "index.html",
            "viewer.html": generated_root / "docs" / "viewer.html",
        }

        if filename not in mapping:
            return jsonify({"ok": False, "error": "Invalid filename"}), 400

        file_path = mapping[filename]
        if not file_path.exists():
            return jsonify({"ok": False, "error": "Generated file not found"}), 404

        return send_file(file_path, as_attachment=False)

    except Exception as exc:
        return jsonify({
            "ok": False,
            "error": str(exc),
        }), 500


# ---------------------------------------------------------
# NEW PROXY ROUTE (SAFE CRUD)
# ---------------------------------------------------------
@app.post("/api/apps/register")
def api_register_app():
    try:
        payload = request.get_json(silent=True) or {}

        slug = (payload.get("slug") or "").strip()
        web_app_url = (payload.get("web_app_url") or "").strip()
        api_key = (payload.get("api_key") or "").strip()

        if not slug:
            return jsonify({"ok": False, "error": "Missing slug"}), 400

        if not web_app_url:
            return jsonify({"ok": False, "error": "Missing web_app_url"}), 400

        if not api_key:
            return jsonify({"ok": False, "error": "Missing api_key"}), 400

        safe_slug = slugify_app_name(slug)
        config = register_app_config(
            slug=safe_slug,
            web_app_url=web_app_url,
            api_key=api_key,
        )

        return jsonify({
            "ok": True,
            "slug": safe_slug,
            "registered": True,
            "web_app_url_present": bool(config.get("web_app_url")),
            "api_key_present": bool(config.get("api_key")),
        })

    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500

@app.route("/api/apps/<slug>/<mode>", methods=["GET", "POST"])
def api_app_proxy(slug: str, mode: str):
    try:
        # B2.5b — serve persistent schema directly from Flask.
        #
        # Per le app persistenti lo schema applicativo è già
        # registrato in persistent_apps.json: non serve chiamare GAS.
        if mode == "schema":
            safe_slug = slugify_app_name(slug)

            persistent_registry = load_persistent_apps()
            persistent_config = persistent_registry.get("apps", {}).get(safe_slug)

            if persistent_config:
                schema = persistent_config.get("schema")

                if not isinstance(schema, dict):
                    raise ValueError(
                        f"Invalid persistent schema for app: {safe_slug}"
                    )

                return jsonify({
                    "ok": True,
                    "appSlug": safe_slug,
                    **schema,
                })

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