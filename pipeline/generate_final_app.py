from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage:\n"
            "  python pipeline/generate_final_app.py <approved_configuration.json>"
        )

    source = Path(sys.argv[1]).expanduser().resolve()

    if not source.exists():
        raise FileNotFoundError(f"File not found: {source}")

    print("Generating final app from approved configuration...\n")

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "pipeline" / "apply_review_state.py"),
            str(source),
        ],
        cwd=ROOT,
    )

    if result.returncode != 0:
        raise SystemExit("Final app generation failed.")

    print("\nFinal app generated successfully.")
    print("\nFiles updated in:")
    print(ROOT / "output" / "current")


if __name__ == "__main__":
    main()