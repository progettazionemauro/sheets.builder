from __future__ import annotations

import json
from pathlib import Path

from generators.builder_generators import generate_all
from generators.schema_validators import validate_schema_for_product


ROOT = Path(__file__).resolve().parent
OUTPUT_CURRENT_DIR = ROOT / "output" / "current"

PROJECT_CONFIG_PATH = OUTPUT_CURRENT_DIR / "project.config.json"
FIELDS_SCHEMA_PATH = OUTPUT_CURRENT_DIR / "fields.schema.json"


def main() -> None:
    if not PROJECT_CONFIG_PATH.exists():
        raise FileNotFoundError(f"Missing file: {PROJECT_CONFIG_PATH}")

    if not FIELDS_SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Missing file: {FIELDS_SCHEMA_PATH}")

    project_config = json.loads(PROJECT_CONFIG_PATH.read_text(encoding="utf-8"))
    fields_schema = json.loads(FIELDS_SCHEMA_PATH.read_text(encoding="utf-8"))

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
    print(f"Output directory: {OUTPUT_CURRENT_DIR}")


if __name__ == "__main__":
    main()