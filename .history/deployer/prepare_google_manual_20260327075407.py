from __future__ import annotations

import argparse
import json
import shutil
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class ProjectConfig:
    project_name: str
    project_slug: str
    backend_name: str
    entity_name: str
    entity_label_lower: str
    sheet_name: str
    output_directory: str
    build_marker: str
    admin_password: str
    generated_at: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProjectConfig":
        return cls(
            project_name=data["projectName"],
            project_slug=data["projectSlug"],
            backend_name=data["backendName"],
            entity_name=data["entityName"],
            entity_label_lower=data["entityLabelLower"],
            sheet_name=data["sheetName"],
            output_directory=data["outputDirectory"],
            build_marker=data["buildMarker"],
            admin_password=data["adminPassword"],
            generated_at=data["generatedAt"],
        )


@dataclass
class DeployManifest:
    project_slug: str
    project_name: str
    backend_entry_file: str
    backend_sheet_name: str
    backend_name: str
    files: list[str]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DeployManifest":
        backend = data["backend"]
        return cls(
            project_slug=data["projectSlug"],
            project_name=data["projectName"],
            backend_entry_file=backend["entryFile"],
            backend_sheet_name=backend["sheetName"],
            backend_name=backend["backendName"],
            files=list(data["files"]),
        )


# ============================================================
# HELPERS
# ============================================================

def print_header(title: str) -> None:
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def print_kv(key: str, value: Any) -> None:
    print(f"{key:<28}: {value}")


def ensure_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"File richiesto non trovato: {path}")
    if not path.is_file():
        raise FileNotFoundError(f"Percorso non valido (non è file): {path}")


def read_json(path: Path) -> dict[str, Any]:
    ensure_file(path)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON non valido: {path}") from exc


def extract_zip(zip_path: Path, extract_dir: Path, clean: bool = False) -> None:
    if not zip_path.exists():
        raise FileNotFoundError(
            f"ZIP non trovato: {zip_path}\n"
            f"Controlla nome e percorso. Esempio corretto: examples/prova-film.zip"
        )

    if clean and extract_dir.exists():
        shutil.rmtree(extract_dir)

    extract_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_dir)


def write_text_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# ============================================================
# CORE LOGIC
# ============================================================

def inspect_package(extract_dir: Path) -> tuple[ProjectConfig, DeployManifest, dict[str, Any]]:
    project_config = ProjectConfig.from_dict(read_json(extract_dir / "project.config.json"))
    deploy_manifest = DeployManifest.from_dict(read_json(extract_dir / "deploy.manifest.json"))
    fields_schema = read_json(extract_dir / "fields.schema.json")
    return project_config, deploy_manifest, fields_schema


def build_example_rows(fields_schema: dict[str, Any]) -> list[dict[str, Any]]:
    headers = fields_schema.get("headers", [])
    computed = set(fields_schema.get("computed", []))
    enums = fields_schema.get("enums", {})

    rows: list[dict[str, Any]] = []

    row1: dict[str, Any] = {}
    row2: dict[str, Any] = {}

    for header in headers:
        if header in computed:
            if header == "id":
                row1[header] = 1
                row2[header] = 2
            else:
                row1[header] = ""
                row2[header] = ""
            continue

        h_norm = header.strip().lower().replace(" ", "_")

        if header in enums and enums[header]:
            row1[header] = enums[header][0]
            row2[header] = enums[header][-1]
        elif "title" in h_norm or "titolo" in h_norm:
            row1[header] = "Nosferatu"
            row2[header] = "Psycho"
        elif "date" in h_norm or "data" in h_norm:
            row1[header] = "04/03/1922"
            row2[header] = "16/06/1960"
        elif "year" in h_norm or "anno" in h_norm:
            row1[header] = 1922
            row2[header] = 1960
        elif "nation" in h_norm or "nazione" in h_norm:
            row1[header] = "Germania"
            row2[header] = "USA"
        elif "url" in h_norm:
            row1[header] = "https://example.org/nosferatu"
            row2[header] = "https://example.org/psycho"
        else:
            row1[header] = f"example_{h_norm}_1"
            row2[header] = f"example_{h_norm}_2"

    rows.append(row1)
    rows.append(row2)
    return rows


def build_google_setup_md(
    project_config: ProjectConfig,
    deploy_manifest: DeployManifest,
    fields_schema: dict[str, Any],
    codice_gs_filename: str,
) -> str:
    headers = fields_schema.get("headers", [])
    example_rows = build_example_rows(fields_schema)

    headers_line = ", ".join(headers)
    example_block = json.dumps(example_rows, ensure_ascii=False, indent=2)

    # indent JSON block for markdown
    example_block_indented = example_block.replace("\n", "\n    ")

    return f"""# Google Apps Script setup guide

## Project summary
- Project name: {project_config.project_name}
- Project slug: {project_config.project_slug}
- Backend logical name: {project_config.backend_name}
- Sheet name: {project_config.sheet_name}

## Files prepared
- {codice_gs_filename}

## Suggested Google flow

### 1. Create the Google Sheet
Create a new Google Sheet and rename the main tab exactly as:

    {project_config.sheet_name}

### 2. Create the header row
Insert these headers in row 1, from column A onward:

    {headers_line}

### 3. Optional example rows
You can insert these example rows manually:

    {example_block_indented}

### 4. Create a new Apps Script project
Suggested project name:

    {project_config.project_name} Backend

### 5. Replace script content
Open:

    {codice_gs_filename}

Copy everything into Apps Script editor.

### 6. Deploy as Web App
- Deploy → New deployment
- Type: Web app
- Execute as: Me
- Access: Anyone

Then copy the /exec URL.

### 7. Connect frontend
Paste the /exec URL into your frontend.

## Notes
- No clasp required
- No Google API required
- Fully manual but controlled setup
"""


def prepare_google_manual(
    zip_path: Path,
    extract_dir: Path,
    output_dir: Path,
    clean: bool,
) -> None:
    extract_zip(zip_path, extract_dir, clean=clean)
    project_config, deploy_manifest, fields_schema = inspect_package(extract_dir)

    codice_src = extract_dir / deploy_manifest.backend_entry_file
    ensure_file(codice_src)

    if clean and output_dir.exists():
        shutil.rmtree(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    codice_dst = output_dir / "codice.gs"
    shutil.copy2(codice_src, codice_dst)

    shutil.copy2(extract_dir / "fields.schema.json", output_dir / "fields.schema.json")
    shutil.copy2(extract_dir / "project.config.json", output_dir / "project.config.json")
    shutil.copy2(extract_dir / "deploy.manifest.json", output_dir / "deploy.manifest.json")

    google_setup_md = build_google_setup_md(
        project_config=project_config,
        deploy_manifest=deploy_manifest,
        fields_schema=fields_schema,
        codice_gs_filename="codice.gs",
    )

    write_text_file(output_dir / "google_setup.md", google_setup_md)

    print_header("GOOGLE MANUAL PACKAGE READY")
    print_kv("ZIP sorgente", zip_path)
    print_kv("Output dir", output_dir)
    print_kv("codice.gs", codice_dst)
    print_kv("Sheet name", project_config.sheet_name)

    print_header("NEXT STEPS")
    print("1. Apri google_setup.md")
    print("2. Crea il foglio Google")
    print("3. Inserisci header")
    print("4. Incolla codice.gs in Apps Script")
    print("5. Deploy Web App")
    print("6. Copia URL /exec")


# ============================================================
# CLI
# ============================================================

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare manual Google Apps Script package.")
    parser.add_argument("zip_path", type=Path)
    parser.add_argument("--extract-dir", type=Path, default=Path("workdir_google"))
    parser.add_argument("--output-dir", type=Path, default=Path("gas_ready"))
    parser.add_argument("--clean", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        prepare_google_manual(
            zip_path=args.zip_path.resolve(),
            extract_dir=args.extract_dir.resolve(),
            output_dir=args.output_dir.resolve(),
            clean=args.clean,
        )
        return 0

    except Exception as exc:
        print_header("ERRORE")
        print(str(exc))
        return 1


if __name__ == "__main__":
    sys.exit(main())