from __future__ import annotations

import argparse
import json
import shutil
import subprocess
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
    frontend_provider: str
    frontend_repo_name_suggested: str
    frontend_branch: str
    frontend_publish_dir: str
    frontend_entry_file: str
    frontend_viewer_file: str
    backend_provider: str
    backend_entry_file: str
    backend_sheet_name: str
    backend_name: str
    files: list[str]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DeployManifest":
        frontend = data["frontend"]
        backend = data["backend"]

        return cls(
            project_slug=data["projectSlug"],
            project_name=data["projectName"],
            frontend_provider=frontend["provider"],
            frontend_repo_name_suggested=frontend["repoNameSuggested"],
            frontend_branch=frontend["branch"],
            frontend_publish_dir=frontend["publishDir"],
            frontend_entry_file=frontend["entryFile"],
            frontend_viewer_file=frontend["viewerFile"],
            backend_provider=backend["provider"],
            backend_entry_file=backend["entryFile"],
            backend_sheet_name=backend["sheetName"],
            backend_name=backend["backendName"],
            files=list(data["files"]),
        )


# ============================================================
# HELPERS
# ============================================================

def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"File JSON mancante: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON non valido in: {path}") from exc


def ensure_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"File richiesto non trovato: {path}")
    if not path.is_file():
        raise FileNotFoundError(f"Percorso non valido (non è file): {path}")


def ensure_dir(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Directory richiesta non trovata: {path}")
    if not path.is_dir():
        raise FileNotFoundError(f"Percorso non valido (non è directory): {path}")


def extract_zip(zip_path: Path, extract_dir: Path, clean: bool = False) -> None:
    if not zip_path.exists():
        raise FileNotFoundError(f"ZIP non trovato: {zip_path}")

    if clean and extract_dir.exists():
        shutil.rmtree(extract_dir)

    extract_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_dir)


def validate_package(root: Path, manifest: DeployManifest) -> list[str]:
    missing: list[str] = []

    for rel_path in manifest.files:
        candidate = root / rel_path
        if not candidate.exists():
            missing.append(rel_path)

    return missing


def print_header(title: str) -> None:
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def print_kv(key: str, value: Any) -> None:
    print(f"{key:<28}: {value}")


def run_cmd(cmd: list[str], cwd: Path) -> None:
    print(f"\n$ {' '.join(cmd)}")
    subprocess.run(cmd, cwd=str(cwd), check=True)


def repo_has_git(path: Path) -> bool:
    return (path / ".git").exists()


# ============================================================
# CORE
# ============================================================

def inspect_package(extract_dir: Path) -> tuple[ProjectConfig, DeployManifest, dict[str, Any]]:
    project_config_path = extract_dir / "project.config.json"
    fields_schema_path = extract_dir / "fields.schema.json"
    deploy_manifest_path = extract_dir / "deploy.manifest.json"

    ensure_file(project_config_path)
    ensure_file(fields_schema_path)
    ensure_file(deploy_manifest_path)

    project_config_data = read_json(project_config_path)
    fields_schema_data = read_json(fields_schema_path)
    deploy_manifest_data = read_json(deploy_manifest_path)

    project_config = ProjectConfig.from_dict(project_config_data)
    deploy_manifest = DeployManifest.from_dict(deploy_manifest_data)

    return project_config, deploy_manifest, fields_schema_data


def print_summary(
    zip_path: Path,
    extract_dir: Path,
    project_config: ProjectConfig,
    deploy_manifest: DeployManifest,
    fields_schema: dict[str, Any],
    missing_files: list[str],
) -> None:
    print_header("ZIP PACKAGE SUMMARY")

    print_kv("ZIP sorgente", zip_path)
    print_kv("Cartella estrazione", extract_dir)
    print_kv("Project name", project_config.project_name)
    print_kv("Project slug", project_config.project_slug)
    print_kv("Backend name", project_config.backend_name)
    print_kv("Entity name", project_config.entity_name)
    print_kv("Sheet name", project_config.sheet_name)
    print_kv("Build marker", project_config.build_marker)
    print_kv("Generated at", project_config.generated_at)

    print_header("FRONTEND DEPLOY INFO")
    print_kv("Provider", deploy_manifest.frontend_provider)
    print_kv("Repo suggested", deploy_manifest.frontend_repo_name_suggested)
    print_kv("Branch", deploy_manifest.frontend_branch)
    print_kv("Publish dir", deploy_manifest.frontend_publish_dir)
    print_kv("Entry file", deploy_manifest.frontend_entry_file)
    print_kv("Viewer file", deploy_manifest.frontend_viewer_file)

    print_header("BACKEND DEPLOY INFO")
    print_kv("Provider", deploy_manifest.backend_provider)
    print_kv("Backend entry file", deploy_manifest.backend_entry_file)
    print_kv("Backend sheet name", deploy_manifest.backend_sheet_name)
    print_kv("Backend logical name", deploy_manifest.backend_name)

    print_header("SCHEMA SUMMARY")
    print_kv("Headers", fields_schema.get("headers", []))
    print_kv("Required on insert", fields_schema.get("requiredOnInsert", []))
    print_kv("Optional on insert", fields_schema.get("optionalOnInsert", []))
    print_kv("Computed", fields_schema.get("computed", []))
    print_kv("Visible in form", fields_schema.get("visibleInForm", []))
    print_kv("Visible in viewer", fields_schema.get("visibleInViewer", []))

    enums = fields_schema.get("enums", {})
    if enums:
        print_kv("Enum fields", list(enums.keys()))
    else:
        print_kv("Enum fields", "none")

    print_header("PACKAGE VALIDATION")
    if missing_files:
        print("ATTENZIONE: mancano i seguenti file dichiarati nel manifest:")
        for item in missing_files:
            print(f" - {item}")
    else:
        print("OK: tutti i file dichiarati nel manifest sono presenti.")


def deploy_frontend(
    extract_dir: Path,
    repo_dir: Path,
    commit_message: str,
) -> None:
    docs_src = extract_dir / "docs"
    docs_dst = repo_dir / "docs"

    ensure_dir(docs_src)

    if not repo_has_git(repo_dir):
        raise RuntimeError(
            f"La cartella target non sembra un repository git valido: {repo_dir}"
        )

    if docs_dst.exists():
        shutil.rmtree(docs_dst)

    shutil.copytree(docs_src, docs_dst)

    run_cmd(["git", "add", "."], cwd=repo_dir)
    run_cmd(["git", "commit", "-m", commit_message], cwd=repo_dir)
    run_cmd(["git", "push"], cwd=repo_dir)


def build_pages_url(github_username: str, repo_name: str) -> str:
    return f"https://{github_username}.github.io/{repo_name}/"


# ============================================================
# CLI
# ============================================================

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Legge uno ZIP generato dal builder e prepara i flussi di deploy."
    )
    parser.add_argument(
        "zip_path",
        type=Path,
        help="Percorso dello ZIP generato dal builder.",
    )
    parser.add_argument(
        "--workdir",
        type=Path,
        default=Path("workdir"),
        help="Cartella di estrazione e lavoro. Default: ./workdir",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Pulisce la cartella di lavoro prima dell'estrazione.",
    )
    parser.add_argument(
        "--frontend-repo-dir",
        type=Path,
        help="Cartella locale del repository frontend GitHub Pages.",
    )
    parser.add_argument(
        "--github-username",
        type=str,
        help="Username GitHub, usato per costruire l'URL finale Pages.",
    )
    parser.add_argument(
        "--run-frontend-deploy",
        action="store_true",
        help="Se presente, copia docs/ nel repo target ed esegue git add/commit/push.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    zip_path = args.zip_path.expanduser().resolve()
    workdir = args.workdir.expanduser().resolve()

    try:
        extract_zip(zip_path, workdir, clean=args.clean)
        project_config, deploy_manifest, fields_schema = inspect_package(workdir)
        missing_files = validate_package(workdir, deploy_manifest)

        print_summary(
            zip_path=zip_path,
            extract_dir=workdir,
            project_config=project_config,
            deploy_manifest=deploy_manifest,
            fields_schema=fields_schema,
            missing_files=missing_files,
        )

        if args.run_frontend_deploy:
            if missing_files:
                raise RuntimeError("Impossibile fare deploy frontend: package non valido.")

            if not args.frontend_repo_dir:
                raise RuntimeError("Manca --frontend-repo-dir")

            repo_dir = args.frontend_repo_dir.expanduser().resolve()
            commit_message = f"Deploy frontend from zip: {project_config.project_slug}"

            print_header("FRONTEND DEPLOY START")
            deploy_frontend(
                extract_dir=workdir,
                repo_dir=repo_dir,
                commit_message=commit_message,
            )

            print_header("FRONTEND DEPLOY DONE")
            print_kv("Repo locale", repo_dir)

            if args.github_username:
                pages_url = build_pages_url(
                    github_username=args.github_username,
                    repo_name=deploy_manifest.frontend_repo_name_suggested,
                )
                print_kv("Pages URL atteso", pages_url)

        else:
            print_header("NEXT STEPS")
            print("1. Flusso GitHub Pages: puoi eseguirlo con --run-frontend-deploy")
            print("2. Flusso GAS/clasp: sarà il passo successivo")
            print("3. Questo script è il punto di partenza dell'orchestratore locale.")

        return 0

    except subprocess.CalledProcessError as exc:
        print_header("ERRORE COMMAND")
        print(f"Comando fallito con exit code {exc.returncode}")
        return 2

    except Exception as exc:
        print_header("ERRORE")
        print(str(exc))
        return 1


if __name__ == "__main__":
    sys.exit(main())