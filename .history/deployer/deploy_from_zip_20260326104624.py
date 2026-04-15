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


def run_cmd_capture(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    print(f"\n$ {' '.join(cmd)}")
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        check=True,
        text=True,
        capture_output=True,
    )


def tool_exists(name: str) -> bool:
    return shutil.which(name) is not None


def repo_has_git(path: Path) -> bool:
    return (path / ".git").exists()


def remote_exists(repo_dir: Path, remote_name: str = "origin") -> bool:
    result = subprocess.run(
        ["git", "remote"],
        cwd=str(repo_dir),
        text=True,
        capture_output=True,
        check=True,
    )
    remotes = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return remote_name in remotes


def build_pages_url(github_username: str, repo_name: str) -> str:
    return f"https://{github_username}.github.io/{repo_name}/"


# ============================================================
# PACKAGE INSPECTION
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


# ============================================================
# FRONTEND PREP / DEPLOY
# ============================================================

def copy_docs_from_package(extract_dir: Path, repo_dir: Path) -> None:
    docs_src = extract_dir / "docs"
    docs_dst = repo_dir / "docs"

    ensure_dir(docs_src)
    repo_dir.mkdir(parents=True, exist_ok=True)

    if docs_dst.exists():
        shutil.rmtree(docs_dst)

    shutil.copytree(docs_src, docs_dst)


def init_git_repo_if_needed(repo_dir: Path) -> None:
    repo_dir.mkdir(parents=True, exist_ok=True)
    if not repo_has_git(repo_dir):
        run_cmd(["git", "init"], cwd=repo_dir)


def prepare_frontend_repo(extract_dir: Path, repo_dir: Path, commit_message: str) -> None:
    init_git_repo_if_needed(repo_dir)
    copy_docs_from_package(extract_dir, repo_dir)

    run_cmd(["git", "add", "."], cwd=repo_dir)

    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(repo_dir),
        text=True,
        capture_output=True,
        check=True,
    )

    if status.stdout.strip():
        run_cmd(["git", "commit", "-m", commit_message], cwd=repo_dir)
    else:
        print("\nNessuna modifica da committare nel repo frontend.")


def configure_remote_and_push(
    repo_dir: Path,
    github_username: str,
    repo_name: str,
    branch: str = "main",
) -> None:
    remote_url = f"https://github.com/{github_username}/{repo_name}.git"

    if remote_exists(repo_dir, "origin"):
        run_cmd(["git", "remote", "set-url", "origin", remote_url], cwd=repo_dir)
    else:
        run_cmd(["git", "remote", "add", "origin", remote_url], cwd=repo_dir)

    run_cmd(["git", "branch", "-M", branch], cwd=repo_dir)
    run_cmd(["git", "push", "-u", "origin", branch], cwd=repo_dir)


def create_github_repo_with_gh(repo_dir: Path, repo_name: str, public: bool = True) -> None:
    if not tool_exists("gh"):
        raise RuntimeError("GitHub CLI 'gh' non trovato nel PATH.")

    visibility_flag = "--public" if public else "--private"
    run_cmd(
        ["gh", "repo", "create", repo_name, visibility_flag, "--source", ".", "--remote", "origin", "--push"],
        cwd=repo_dir,
    )


def manual_pause_for_repo_creation(github_username: str, repo_name: str) -> None:
    print_header("AZIONE MANUALE RICHIESTA")
    print("Crea ora una nuova repository su GitHub con questi dati:")
    print_kv("Owner", github_username)
    print_kv("Repository", repo_name)
    print("\nQuando hai terminato la creazione della repo remota, premi INVIO per continuare...")
    input()


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
        help="Username GitHub, usato per creare URL e remote.",
    )
    parser.add_argument(
        "--prepare-frontend-repo",
        action="store_true",
        help="Prepara il repo locale frontend copiando docs/ e facendo commit locale.",
    )
    parser.add_argument(
        "--frontend-mode",
        choices=["manual", "gh"],
        help="Modalità deploy frontend: manual = pausa guidata, gh = usa GitHub CLI.",
    )
    parser.add_argument(
        "--private-repo",
        action="store_true",
        help="Se usi --frontend-mode gh, crea la repo come privata invece che pubblica.",
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

        if args.prepare_frontend_repo:
            if missing_files:
                raise RuntimeError("Impossibile procedere: package non valido.")

            if not args.frontend_repo_dir:
                raise RuntimeError("Manca --frontend-repo-dir")

            repo_dir = args.frontend_repo_dir.expanduser().resolve()
            commit_message = f"Deploy frontend from zip: {project_config.project_slug}"

            print_header("PREPARE FRONTEND REPO")
            prepare_frontend_repo(
                extract_dir=workdir,
                repo_dir=repo_dir,
                commit_message=commit_message,
            )
            print_kv("Repo locale frontend", repo_dir)

            if args.frontend_mode:
                if not args.github_username:
                    raise RuntimeError("Manca --github-username")

                repo_name = deploy_manifest.frontend_repo_name_suggested

                print_header("FRONTEND REMOTE FLOW")

                if args.frontend_mode == "manual":
                    manual_pause_for_repo_creation(args.github_username, repo_name)
                    configure_remote_and_push(
                        repo_dir=repo_dir,
                        github_username=args.github_username,
                        repo_name=repo_name,
                        branch=deploy_manifest.frontend_branch,
                    )

                elif args.frontend_mode == "gh":
                    create_github_repo_with_gh(
                        repo_dir=repo_dir,
                        repo_name=repo_name,
                        public=not args.private_repo,
                    )

                pages_url = build_pages_url(
                    github_username=args.github_username,
                    repo_name=repo_name,
                )

                print_header("FRONTEND FLOW DONE")
                print_kv("Pages URL atteso", pages_url)
                print("Ricordati di impostare GitHub Pages su:")
                print("Settings -> Pages -> Deploy from a branch -> main -> /docs")

        else:
            print_header("NEXT STEPS")
            print("1. Usa --prepare-frontend-repo per copiare docs/ in un repo locale.")
            print("2. Aggiungi --frontend-mode manual oppure --frontend-mode gh per spingere verso GitHub.")
            print("3. Il flusso GAS/clasp sarà il passo successivo.")

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