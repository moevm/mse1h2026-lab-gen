import re
from pathlib import Path
from typing import List, Tuple


HEADER_RE = re.compile(r"^###\s*(.*?)\s*###\s*$")
LEGACY_HEADER_RE = re.compile(r"^###\s+(.*?)\s*$")


def parse_student_solution_blob(text: str) -> List[Tuple[str, str]]:
    if not text.strip():
        return []

    result: List[Tuple[str, str]] = []
    current_name: str | None = None
    current_lines: List[str] = []

    for raw_line in text.splitlines():
        header_match = HEADER_RE.match(raw_line)
        legacy_match = LEGACY_HEADER_RE.match(raw_line) if header_match is None else None

        if header_match or legacy_match:
            if current_name is not None:
                result.append((current_name, "\n".join(current_lines)))
            current_name = (header_match or legacy_match).group(1).strip()
            current_lines = []
            continue

        if current_name is not None:
            current_lines.append(raw_line)

    if current_name is not None:
        result.append((current_name, "\n".join(current_lines)))

    return result


def write_solution_to_dir(entries: List[Tuple[str, str]], target_dir: Path) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)

    for name, content in entries:
        clean_name = name.strip()
        if not clean_name:
            continue

        filepath = target_dir / clean_name
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(content, encoding="utf-8", errors="replace")
