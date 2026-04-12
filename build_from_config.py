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