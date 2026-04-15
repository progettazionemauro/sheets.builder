from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import json
from typing import Dict, Optional

from generators.import_from_html import import_visuals_from_html
from generators.import_from_sheet import save_schema_from_xlsx
from generators.merge_schema import merge_schema_with_visuals


OUTPUT_CURRENT_DIR = ROOT / "output" / "current"
EXAMPLES_DIR = ROOT / "examples"


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def find_input_files(input_dir: str | Path) -> Dict[str, Optional[Path]]:
    input_dir = Path(input_dir)
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    xlsx_files = sorted(input_dir.rglob("*.xlsx"))
    html_files = sorted(input_dir.rglob("*.html"))
    css_files = sorted(input_dir.rglob("*.css"))

    if not xlsx_files:
        raise FileNotFoundError(
            f"Missing required .xlsx file inside: {input_dir}"
        )

    if not html_files:
        print(f"WARNING: no .html file found inside {input_dir}. Visual enrichment will be skipped.")

    if not css_files:
        print(f"WARNING: no .css file found inside {input_dir}. This is not blocking.")

    return {
        "input_dir": input_dir,
        "xlsx": xlsx_files[0],
        "html": html_files[0] if html_files else None,
        "css": css_files[0] if css_files else None,
    }


def build_schema_from_directory(
    input_dir: str | Path,
    output_json_path: str | Path,
    enum_field_name: str = "rating",
    debug: bool = False,
) -> dict:
    paths = find_input_files(input_dir)

    sheet_schema = save_schema_from_xlsx(
        xlsx_path=paths["xlsx"],
        output_json_path=None,
        sheet_name=None,
        header_row=1,
        sample_row=2,
        debug=debug,
    )

    final_schema = sheet_schema

    if paths["html"] is not None:
        html_visuals = import_visuals_from_html(
            html_path=paths["html"],
            enum_field_name=enum_field_name,
            debug=debug,
        )

        final_schema = merge_schema_with_visuals(
            sheet_schema=sheet_schema,
            html_visuals=html_visuals,
        )

    output_json_path = Path(output_json_path)
    write_json(output_json_path, final_schema)

    if debug:
        print("\nINPUT PATHS")
        print(paths)

        print("\nFINAL ENUMS")
        print(final_schema.get("enums", {}))

        print("\nFINAL ENUM STYLES")
        print(final_schema.get("enumStyles", {}))

    return final_schema


def main() -> None:
    if len(sys.argv) == 1:
        candidate_dirs = [p for p in EXAMPLES_DIR.iterdir() if p.is_dir()]
        if not candidate_dirs:
            raise SystemExit(
                f"No subdirectories found inside examples/: {EXAMPLES_DIR}"
            )
        if len(candidate_dirs) > 1:
            raise SystemExit(
                "More than one subdirectory found inside examples/. "
                "Pass the desired input directory explicitly."
            )
        input_dir = candidate_dirs[0]
        enum_field_name = "rating"

    elif len(sys.argv) == 2:
        input_dir = Path(sys.argv[1])
        enum_field_name = "rating"

    else:
        input_dir = Path(sys.argv[1])
        enum_field_name = sys.argv[2]

    output_json = OUTPUT_CURRENT_DIR / "fields.schema.json"

    schema = build_schema_from_directory(
        input_dir=input_dir,
        output_json_path=output_json,
        enum_field_name=enum_field_name,
        debug=True,
    )

    print("\nSchema generated successfully.")
    print("Output:", output_json)
    print("Headers:", schema.get("headers", []))
    print("Enums:", schema.get("enums", {}))


if __name__ == "__main__":
    main()