from __future__ import annotations

import json
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, Optional

from generators.import_from_html import import_visuals_from_html
from generators.import_from_sheet import save_schema_from_xlsx
from generators.merge_schema import merge_schema_with_visuals


ROOT = Path(__file__).resolve().parent.parent
WORKDIR = ROOT / "workdir"


def extract_bundle(zip_path: str | Path) -> Dict[str, Optional[Path]]:
    """
    Bundle semplice e piatto:
    - un .xlsx obbligatorio
    - un .html opzionale
    - un .css opzionale

    Tutti in root nello zip.
    """
    zip_path = Path(zip_path)
    if not zip_path.exists():
        raise FileNotFoundError(f"ZIP not found: {zip_path}")

    temp_dir = Path(tempfile.mkdtemp(prefix="sheet_bundle_"))

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(temp_dir)

    root_files = [p for p in temp_dir.iterdir() if p.is_file()]

    xlsx_files = [p for p in root_files if p.suffix.lower() == ".xlsx"]
    html_files = [p for p in root_files if p.suffix.lower() == ".html"]
    css_files = [p for p in root_files if p.suffix.lower() == ".css"]

    if not xlsx_files:
        raise FileNotFoundError("No .xlsx file found in bundle root")

    return {
        "dir": temp_dir,
        "xlsx": xlsx_files[0],
        "html": html_files[0] if html_files else None,
        "css": css_files[0] if css_files else None,
    }


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def build_schema_from_bundle(
    bundle_zip_path: str | Path,
    output_json_path: str | Path,
    enum_field_name: str = "rating",
    debug: bool = False,
) -> dict:
    paths = extract_bundle(bundle_zip_path)

    try:
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
            print("\nBUNDLE PATHS")
            print(paths)

            print("\nFINAL ENUMS")
            print(final_schema.get("enums", {}))

            print("\nFINAL ENUM STYLES")
            print(final_schema.get("enumStyles", {}))

        return final_schema

    finally:
        shutil.rmtree(paths["dir"], ignore_errors=True)


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit(
            "Usage:\n"
            "  python pipeline/build_schema_from_bundle.py /path/to/bundle.zip\n"
            "  python pipeline/build_schema_from_bundle.py /path/to/bundle.zip rating"
        )

    zip_path = sys.argv[1]
    enum_field_name = sys.argv[2] if len(sys.argv) > 2 else "rating"

    output_json = WORKDIR / "fields.schema.json"

    schema = build_schema_from_bundle(
        bundle_zip_path=zip_path,
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