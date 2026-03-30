from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib import error, request


API_BASE = "https://api.github.com"


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
    frontend_repo_name_suggested: str
    frontend_branch: str
    frontend_publish_dir: str
    frontend_entry_file: str
    frontend_viewer_file: str
    files: list[str]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DeployManifest":
        frontend = data["frontend"]
        return cls(
            project_slug=data["projectSlug"],
            project_name=data["projectName"],
            frontend_repo_name_suggested=frontend["repoNameSuggested"],
            frontend_branch=frontend["branch"],
            frontend_publish_dir=frontend["publishDir"],
            frontend_entry_file=frontend["entryFile"],
            frontend_viewer_file=frontend["viewerFile"],
            files=list(data["files"]),
        )


# ============================================================
# GENERIC HELPERS
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
            f"Controlla nome e percorso. Esempio: examples/prova-film.zip"
        )

    if clean and extract_dir.exists():
        shutil.rmtree(extract_dir)

    extract_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_dir)


def collect_frontend_files(root: Path, publish_dir: str) -> list[Path]:
    base = root / publish_dir
    if not base.exists():
        raise FileNotFoundError(f"Directory frontend non trovata nel package: {base}")

    files: list[Path] = []
    for path in base.rglob("*"):
        if path.is_file():
            files.append(path)
    return sorted(files)


def build_pages_url(owner: str, repo: str) -> str:
    return f"https://{owner}.github.io/{repo}/"


# ============================================================
# GITHUB REST CLIENT
# ============================================================

class GitHubApi:
    def __init__(self, token: str):
        self.token = token.strip()
        if not self.token:
            raise ValueError("Token GitHub vuoto")

    def _request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
        expected_status: tuple[int, ...] = (200,),
    ) -> dict[str, Any] | None:
        url = f"{API_BASE}{path}"
        data = None

        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "sheet-builder-deployer",
        }

        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = request.Request(url=url, data=data, headers=headers, method=method)

        try:
            with request.urlopen(req) as resp:
                raw = resp.read().decode("utf-8")
                if resp.status not in expected_status:
                    raise RuntimeError(f"HTTP inatteso {resp.status}: {raw}")
                return json.loads(raw) if raw else None

        except error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"GitHub API error {exc.code} su {method} {path}\n{raw}"
            ) from exc

    def get_authenticated_user(self) -> dict[str, Any]:
        return self._request("GET", "/user", expected_status=(200,)) or {}

    def get_repo(self, owner: str, repo: str) -> dict[str, Any] | None:
        try:
            return self._request("GET", f"/repos/{owner}/{repo}", expected_status=(200,))
        except RuntimeError as exc:
            if "GitHub API error 404" in str(exc):
                return None
            raise

    def create_user_repo(self, repo_name: str, private: bool = False, description: str = "") -> dict[str, Any]:
        body = {
            "name": repo_name,
            "private": private,
            "description": description,
            "auto_init": False,
        }
        return self._request("POST", "/user/repos", body=body, expected_status=(201,)) or {}

    def get_file_sha(self, owner: str, repo: str, path: str) -> str | None:
        try:
            data = self._request("GET", f"/repos/{owner}/{repo}/contents/{path}", expected_status=(200,))
            if not data:
                return None
            return data.get("sha")
        except RuntimeError as exc:
            if "GitHub API error 404" in str(exc):
                return None
            raise

    def create_or_update_file(
        self,
        owner: str,
        repo: str,
        repo_path: str,
        content_bytes: bytes,
        message: str,
        branch: str,
    ) -> dict[str, Any]:
        b64 = base64.b64encode(content_bytes).decode("ascii")
        body: dict[str, Any] = {
            "message": message,
            "content": b64,
            "branch": branch,
        }

        sha = self.get_file_sha(owner, repo, repo_path)
        if sha:
            body["sha"] = sha

        return self._request(
            "PUT",
            f"/repos/{owner}/{repo}/contents/{repo_path}",
            body=body,
            expected_status=(200, 201),
        ) or {}

    def get_pages(self, owner: str, repo: str) -> dict[str, Any] | None:
        try:
            return self._request("GET", f"/repos/{owner}/{repo}/pages", expected_status=(200,))
        except RuntimeError as exc:
            if "GitHub API error 404" in str(exc):
                return None
            raise

    def create_pages(self, owner: str, repo: str, branch: str, path: str) -> dict[str, Any]:
        body = {
            "build_type": "legacy",
            "source": {
                "branch": branch,
                "path": path,
            },
        }
        return self._request(
            "POST",
            f"/repos/{owner}/{repo}/pages",
            body=body,
            expected_status=(201,),
        ) or {}

    def update_pages(self, owner: str, repo: str, branch: str, path: str) -> dict[str, Any]:
        body = {
            "build_type": "legacy",
            "source": {
                "branch": branch,
                "path": path,
            },
        }
        return self._request(
            "PUT",
            f"/repos/{owner}/{repo}/pages",
            body=body,
            expected_status=(204,),
        ) or {}

    def ensure_pages(self, owner: str, repo: str, branch: str, path: str) -> None:
        site = self.get_pages(owner, repo)
        if site is None:
            self.create_pages(owner, repo, branch, path)
        else:
            self.update_pages(owner, repo, branch, path)


# ============================================================
# PACKAGE LOADING
# ============================================================

def inspect_package(extract_dir: Path) -> tuple[ProjectConfig, DeployManifest]:
    project_config = ProjectConfig.from_dict(read_json(extract_dir / "project.config.json"))
    deploy_manifest = DeployManifest.from_dict(read_json(extract_dir / "deploy.manifest.json"))
    return project_config, deploy_manifest


# ============================================================
# FRONTEND REST DEPLOY
# ============================================================

def deploy_frontend_via_rest(
    zip_path: Path,
    workdir: Path,
    github_token: str,
    owner_override: str | None,
    repo_override: str | None,
    clean: bool,
    private_repo: bool,
) -> None:
    extract_zip(zip_path, workdir, clean=clean)
    project_config, manifest = inspect_package(workdir)

    api = GitHubApi(github_token)
    auth_user = api.get_authenticated_user()
    owner = owner_override or auth_user["login"]
    repo_name = repo_override or manifest.frontend_repo_name_suggested

    print_header("PACKAGE")
    print_kv("ZIP sorgente", zip_path)
    print_kv("Cartella estrazione", workdir)
    print_kv("Project slug", project_config.project_slug)
    print_kv("Repo target", f"{owner}/{repo_name}")
    print_kv("Branch", manifest.frontend_branch)
    print_kv("Publish dir", manifest.frontend_publish_dir)

    print_header("REPOSITORY")
    existing = api.get_repo(owner, repo_name)
    if existing is None:
        if owner != auth_user["login"]:
            raise RuntimeError(
                "Creazione repo in organization non ancora supportata in questo primo script.\n"
                "Per ora usa il tuo account personale oppure estendiamo lo script al caso org."
            )
        api.create_user_repo(
            repo_name=repo_name,
            private=private_repo,
            description=f"Generated by Sheets Builder for {project_config.project_name}",
        )
        print(f"Repo creata: {owner}/{repo_name}")
    else:
        print(f"Repo già esistente: {owner}/{repo_name}")

    print_header("UPLOAD FILES")
    frontend_files = collect_frontend_files(workdir, manifest.frontend_publish_dir)
    for file_path in frontend_files:
      rel = file_path.relative_to(workdir).as_posix()
      content = file_path.read_bytes()
      api.create_or_update_file(
          owner=owner,
          repo=repo_name,
          repo_path=rel,
          content_bytes=content,
          message=f"Update {rel} from builder package",
          branch=manifest.frontend_branch,
      )
      print(f"Uploaded: {rel}")

    print_header("CONFIGURE GITHUB PAGES")
    api.ensure_pages(
        owner=owner,
        repo=repo_name,
        branch=manifest.frontend_branch,
        path=f"/{manifest.frontend_publish_dir}",
    )
    print("GitHub Pages configurato su main + /docs")

    print_header("DONE")
    print_kv("Repository", f"{owner}/{repo_name}")
    print_kv("Pages URL atteso", build_pages_url(owner, repo_name))
    print("Nota: la prima pubblicazione può richiedere un breve tempo di propagazione.")


# ============================================================
# CLI
# ============================================================

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Deploy frontend cross-platform via GitHub REST API."
    )
    parser.add_argument("zip_path", type=Path, help="Percorso dello ZIP generato dal builder.")
    parser.add_argument(
        "--workdir",
        type=Path,
        default=Path("workdir_rest"),
        help="Cartella di estrazione temporanea. Default: ./workdir_rest",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Pulisce la cartella di lavoro prima dell'estrazione.",
    )
    parser.add_argument(
        "--github-token",
        type=str,
        default=os.getenv("GITHUB_TOKEN", "").strip(),
        help="Token GitHub. In alternativa usa la variabile d'ambiente GITHUB_TOKEN.",
    )
    parser.add_argument(
        "--github-owner",
        type=str,
        help="Owner GitHub target. Se omesso, usa l'utente autenticato.",
    )
    parser.add_argument(
        "--repo-name",
        type=str,
        help="Nome repo da usare. Se omesso, usa quello suggerito dal manifest.",
    )
    parser.add_argument(
        "--private-repo",
        action="store_true",
        help="Crea la repo come privata. Default: pubblica.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        if not args.github_token:
            raise RuntimeError(
                "Token GitHub mancante.\n"
                "Passalo con --github-token oppure imposta GITHUB_TOKEN nell'ambiente."
            )

        deploy_frontend_via_rest(
            zip_path=args.zip_path.expanduser().resolve(),
            workdir=args.workdir.expanduser().resolve(),
            github_token=args.github_token,
            owner_override=args.github_owner,
            repo_override=args.repo_name,
            clean=args.clean,
            private_repo=args.private_repo,
        )
        return 0

    except Exception as exc:
        print_header("ERRORE")
        print(str(exc))
        return 1


if __name__ == "__main__":
    sys.exit(main())