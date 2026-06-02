from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SESSIONS_DIR = ROOT / "workdir" / "flask_sessions"


def latest_builder_state() -> Path:
    files = sorted(
        SESSIONS_DIR.glob("*/builder_state.json"),
        key=lambda p: p.stat().st_mtime,
    )

    if not files:
        raise SystemExit(f"No builder_state.json found in {SESSIONS_DIR}")

    return files[-1]


def exists_label(path: Path) -> str:
    return "OK" if path.exists() else "MISSING"


def main() -> None:
    builder_state_path = latest_builder_state()
    session_dir = builder_state_path.parent
    session_id = session_dir.name

    data = json.loads(builder_state_path.read_text(encoding="utf-8"))
    project = data.get("project", {})

    generated_dir = session_dir / "generated"

    files = {
        "codice.gs": generated_dir / "codice.gs",
        "index.html": generated_dir / "docs" / "index.html",
        "viewer.html": generated_dir / "docs" / "viewer.html",
        "builder_state.json": builder_state_path,
        "parsed.schema.json": session_dir / "parsed.schema.json",
    }

    print()
    print("=== DJUNGO CURRENT SESSION ===")
    print()
    print(f"Project root: {ROOT}")
    print(f"Session ID:   {session_id}")
    print(f"Session dir:  {session_dir}")
    print()
    print("Project:")
    print(f"  sheetName:   {project.get('sheetName', '')}")
    print(f"  projectSlug: {project.get('projectSlug', '')}")
    print(f"  projectName: {project.get('projectName', '')}")
    print(f"  backendName: {project.get('backendName', '')}")
    print()
    print("Generated files:")
    for label, path in files.items():
        print(f"  {exists_label(path):7} {label:18} {path}")

    print()
    print("Useful URLs:")
    print(f"  app_ready: http://127.0.0.1:5000/app_ready.html?session_id={session_id}")
    print(f"  index:     http://127.0.0.1:5000/run/{session_id}/index.html?app={project.get('projectSlug', '')}&debug=1")
    print(f"  viewer:    http://127.0.0.1:5000/run/{session_id}/viewer.html?app={project.get('projectSlug', '')}&limit=50&embedded=1")
    print(f"  gas:       http://127.0.0.1:5000/run/{session_id}/codice.gs")
    print()


if __name__ == "__main__":
    main()