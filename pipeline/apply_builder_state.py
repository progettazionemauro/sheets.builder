from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OUTPUT_CURRENT_DIR = ROOT / "output" / "current"
TARGET_BUILDER_STATE = OUTPUT_CURRENT_DIR / "builder_state.json"


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage:\n"
            "  python pipeline/apply_builder_state.py <path_to_builder_state.json>"
        )

    source = Path(sys.argv[1]).expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(f"Builder state file not found: {source}")
    if not source.is_file():
        raise FileNotFoundError(f"Path is not a file: {source}")

    OUTPUT_CURRENT_DIR.mkdir(parents=True, exist_ok=True)

    shutil.copy2(source, TARGET_BUILDER_STATE)

    print("Builder state imported successfully.")
    print(f"Source: {source}")
    print(f"Target: {TARGET_BUILDER_STATE}")

    print("\nRebuilding generated files...")
    result = subprocess.run(
        [sys.executable, str(ROOT / "build_from_config.py")],
        cwd=ROOT,
    )
    if result.returncode != 0:
        raise SystemExit("Build failed after importing builder_state.json")

    print("\nDone.")
    print(f"Updated backend:  {OUTPUT_CURRENT_DIR / 'codice.gs'}")
    print(f"Updated frontend: {OUTPUT_CURRENT_DIR / 'docs' / 'index.html'}")
    print(f"Updated viewer:   {OUTPUT_CURRENT_DIR / 'docs' / 'viewer.html'}")


if __name__ == "__main__":
    main()