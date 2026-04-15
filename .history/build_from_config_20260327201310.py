from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from generators.builder_generators import generate_all
from generators.schema_validators import validate_schema_for_product


ROOT = Path(__file__).resolve().parent
WORKDIR = ROOT / "workdir"


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def ensure_manifest(project_config: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "projectSlug": project_config["projectSlug"],
        "frontend": {
            "publish": "github-pages",
            "docsDir": "docs"
        },
        "backend": {
            "publish": "manual-google-apps-script",
            "sheetName": project_config["sheetName"],
            "entryPoint": "doGet"
        },
        "artifacts": [
            "codice.gs",
            "docs/index.html",
            "docs/viewer.html",
            "project.config.json",
            "fields.schema.json",
            "deploy.manifest.json"
        ]
    }


def main() -> None:
    project_config_path = WORKDIR / "project.config.json"
    fields_schema_path = WORKDIR / "fields.schema.json"

    if not project_config_path.exists():
        raise FileNotFoundError(f"Missing file: {project_config_path}")

    if not fields_schema_path.exists():
        raise FileNotFoundError(f"Missing file: {fields_schema_path}")

    project_config = load_json(project_config_path)
    fields_schema = load_json(fields_schema_path)

    errors = validate_schema_for_product(fields_schema)
    if errors:
      joined = "\n- ".join(errors)
      raise ValueError(f"Schema validation failed:\n- {joined}")

    generated = generate_all(project_config, fields_schema)

    for rel_path, content in generated.items():
        write_text(WORKDIR / rel_path, content)

    manifest_path = WORKDIR / "deploy.manifest.json"
    if not manifest_path.exists():
        write_text(
            manifest_path,
            json.dumps(ensure_manifest(project_config), ensure_ascii=False, indent=2)
        )

    print("Build completed successfully.")
    print(f"Output directory: {WORKDIR}")


if __name__ == "__main__":
    main()