from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

WORKDIR = ROOT / "workdir"
EXAMPLES_DIR = ROOT / "examples"
PROJECT_CONFIG_PATH = WORKDIR / "project.config.json"
FIELDS_SCHEMA_PATH = WORKDIR / "fields.schema.json"


def ensure_default_project_config() -> dict:
    """
    Se project.config.json non esiste in workdir, ne crea uno minimale.
    Se esiste già, lo lascia invariato.
    """
    if PROJECT_CONFIG_PATH.exists():
        return json.loads(PROJECT_CONFIG_PATH.read_text(encoding="utf-8"))

    config = {
        "projectName": "Imported Sheet Project",
        "projectSlug": "imported-sheet-project",
        "backendName": "imported-sheet-backend",
        "entityName": "ImportedItem",
        "entityLabelLower": "item",
        "sheetName": "Sheet1",
        "outputDirectory": str(WORKDIR),
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


def find_single_example_dir() -> Path:
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
        input_dir = find_single_example_dir()
    else:
        input_dir = Path(sys.argv[1])

    ensure_default_project_config()

    run_step(
        [
            sys.executable,
            str(ROOT / "pipeline" / "build_schema_from_bundl.py"),
            str(input_dir),
        ],
        "STEP 1 - Build fields.schema.json from examples basket",
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
    print(f"Output:   {WORKDIR}")
    print(f"Frontend: {WORKDIR / 'docs' / 'index.html'}")
    print(f"Viewer:   {WORKDIR / 'docs' / 'viewer.html'}")
    print(f"Backend:  {WORKDIR / 'codice.gs'}")


if __name__ == "__main__":
    main()