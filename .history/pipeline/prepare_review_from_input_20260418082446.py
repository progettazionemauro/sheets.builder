from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.build_schema_from_input import build_schema_from_directory
from app.builder_state import build_builder_state


OUTPUT_CURRENT_DIR = ROOT / "output" / "current"
EXAMPLES_DIR = ROOT / "examples"


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def find_single_input_dir() -> Path:
    candidate_dirs = [p for p in EXAMPLES_DIR.iterdir() if p.is_dir()]
    if not candidate_dirs:
        raise SystemExit(f"No subdirectories found inside examples/: {EXAMPLES_DIR}")
    if len(candidate_dirs) > 1:
        raise SystemExit(
            "More than one subdirectory found inside examples/. "
            "Pass the desired input directory explicitly."
        )
    return candidate_dirs[0]


def main() -> None:
    if len(sys.argv) == 1:
        input_dir = find_single_input_dir()
        enum_field_name = "rating"
    elif len(sys.argv) == 2:
        input_dir = Path(sys.argv[1])
        enum_field_name = "rating"
    elif len(sys.argv) == 3:
        input_dir = Path(sys.argv[1])
        enum_field_name = sys.argv[2]
    else:
        raise SystemExit(
            "Usage:\n"
            "  python pipeline/prepare_review_from_input.py <input_dir> [enum_field_name]\n\n"
            "Example:\n"
            "  python pipeline/prepare_review_from_input.py examples/case_001\n"
            "  python pipeline/prepare_review_from_input.py examples/case_001 rating"
        )

    OUTPUT_CURRENT_DIR.mkdir(parents=True, exist_ok=True)

    parsed_schema_path = OUTPUT_CURRENT_DIR / "parsed.schema.json"
    builder_state_path = OUTPUT_CURRENT_DIR / "builder_state.json"

    parsed_schema = build_schema_from_directory(
        input_dir=input_dir,
        output_json_path=parsed_schema_path,
        enum_field_name=enum_field_name,
        debug=True,
    )

    builder_state = build_builder_state(parsed_schema)
    write_json(builder_state_path, builder_state)

    print("\nReview preparation completed successfully.")
    print(f"Input directory:      {input_dir}")
    print(f"Parsed schema output: {parsed_schema_path}")
    print(f"Builder state output: {builder_state_path}")
    print("\nNext step:")
    print("1. Open docs/review.html")
    print("2. Load output/current/builder_state.json")
    print("3. Review fields and enum styles")
    print("4. Export reviewed_configuration.json")
    print("5. Apply it with pipeline/apply_review_state.py")


if __name__ == "__main__":
    main()