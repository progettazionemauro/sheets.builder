from __future__ import annotations

import json
from pathlib import Path

from generators.builder_generators import generate_all
from generators.schema_validators import validate_schema_f


ROOT = Path(__file__).resolve().parent
OUTPUT_PROJECT_DIR = ROOT / "output_project"

project_config_path = OUTPUT_PROJECT_DIR / "project.config.json"
fields_schema_path = OUTPUT_PROJECT_DIR / "fields.schema.json"


def main() -> None:
    if not project_config_path.exists():
        raise FileNotFoundError(f"Missing file: {project_config_path}")

    if not fields_schema_path.exists():
        raise FileNotFoundError(f"Missing file: {fields_schema_path}")

    project_config = json.loads(project_config_path.read_text(encoding="utf-8"))
    fields_schema = json.loads(fields_schema_path.read_text(encoding="utf-8"))

    errors = validate_schema(fields_schema)
    if errors:
        joined = "\n- ".join(errors)
        raise ValueError(f"Schema validation failed:\n- {joined}")

    generated = generate_all(project_config, fields_schema)

    for relative_path, content in generated.items():
        target = OUTPUT_PROJECT_DIR / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    # aggiorna anche un deploy.manifest.json minimo se manca
    deploy_manifest_path = OUTPUT_PROJECT_DIR / "deploy.manifest.json"
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
    print(f"Output directory: {OUTPUT_PROJECT_DIR}")


if __name__ == "__main__":
    main()