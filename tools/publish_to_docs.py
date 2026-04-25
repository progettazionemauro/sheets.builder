from __future__ import annotations

import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
OUTPUT_CURRENT_DIR = ROOT / "output" / "current"
OUTPUT_DOCS_DIR = OUTPUT_CURRENT_DIR / "docs"
DOCS_DIR = ROOT / "docs"


FILES_TO_COPY = [
    (OUTPUT_DOCS_DIR / "index.html", DOCS_DIR / "index.html"),
    (OUTPUT_DOCS_DIR / "viewer.html", DOCS_DIR / "viewer.html"),
    (OUTPUT_CURRENT_DIR / "codice.gs", DOCS_DIR / "codice.gs"),
]


PUBLIC_BASE_URL = "https://progettazionemauro.github.io/sheets.builder"


def main() -> None:
    missing = [src for src, _ in FILES_TO_COPY if not src.exists()]
    if missing:
        msg = "\n".join(f"- {p}" for p in missing)
        raise FileNotFoundError(
            "Missing generated files in output/current:\n"
            f"{msg}\n\n"
            "Run the final generation step first."
        )

    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    for src, dst in FILES_TO_COPY:
        shutil.copy2(src, dst)
        print(f"Copied: {src} -> {dst}")

    print("\nPublish-to-docs completed successfully.")
    print("\nNext steps:")
    print("1. git add docs/index.html docs/viewer.html docs/codice.gs")
    print('2. git commit -m "Update final generated app"')
    print("3. git push")
    print("\nPublic URLs:")
    print(f"- App ready page: {PUBLIC_BASE_URL}/app_ready.html")
    print(f"- CRUD app:       {PUBLIC_BASE_URL}/index.html")
    print(f"- Viewer:         {PUBLIC_BASE_URL}/viewer.html")


if __name__ == "__main__":
    main()