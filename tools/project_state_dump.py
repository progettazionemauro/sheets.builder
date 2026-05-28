from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "PROJECT_STATE_DUMP.md"

EXCLUDE_DIRS = {
    ".git", ".venv", "venv", "__pycache__", ".mypy_cache",
    ".pytest_cache", "node_modules", "workdir", ".history"
}

INCLUDE_EXT = {
    ".py", ".html", ".js", ".css", ".json", ".md", ".txt",
    ".service", ".conf", ".sh"
}

MAX_FILE_CHARS = 6000


def should_skip(path: Path) -> bool:
    return any(part in EXCLUDE_DIRS for part in path.parts)


def tree_lines(root: Path) -> list[str]:
    lines = []
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if should_skip(rel):
            continue
        depth = len(rel.parts) - 1
        prefix = "  " * depth + ("- " if path.is_file() else "+ ")
        lines.append(prefix + str(rel))
    return lines


def file_summary(root: Path) -> list[str]:
    chunks = []
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if should_skip(rel) or not path.is_file():
            continue
        if path.suffix not in INCLUDE_EXT:
            continue

        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            text = f"[Could not read file: {exc}]"

        chunks.append(f"\n## File: `{rel}`\n")
        chunks.append("```text\n")
        chunks.append(text[:MAX_FILE_CHARS])
        if len(text) > MAX_FILE_CHARS:
            chunks.append("\n\n...[TRUNCATED]...\n")
        chunks.append("\n```\n")
    return chunks


def main() -> None:
    content = []
    content.append("# PROJECT STATE DUMP\n")
    content.append(f"Generated: {datetime.now().isoformat(timespec='seconds')}\n")
    content.append(f"Root: `{ROOT}`\n\n")

    content.append("## 1. Project tree\n\n")
    content.append("```text\n")
    content.extend(line + "\n" for line in tree_lines(ROOT))
    content.append("```\n\n")

    content.append("## 2. Key file contents\n")
    content.extend(file_summary(ROOT))

    OUT.write_text("".join(content), encoding="utf-8")
    print(f"Written: {OUT}")


if __name__ == "__main__":
    main()