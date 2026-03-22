from pathlib import Path
from typing import List, Tuple


def parse_student_solution_blob(text: str) -> List[Tuple[str, str]]:
    if not text.strip():
        return []

    lines = [line.rstrip("\n") for line in text.splitlines()]
    result: List[Tuple[str, str]] = []
    current_name: str | None = None
    current_lines: List[str] = []

    i = 0
    while i < len(lines):
        line = lines[i]
        i += 1

        if not line.strip():
            continue

        if line.startswith("### "):
            if current_name is not None:
                result.append((current_name, "\n".join(current_lines)))
            current_name = line[4:].strip()
            current_lines = []
            continue

        if current_name is not None:
            current_lines.append(line)

    if current_name is not None:
        result.append((current_name, "\n".join(current_lines)))

    return result


def write_solution_to_dir(entries: List[Tuple[str, str]], target_dir: Path) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)

    for name, content in entries:
        name = name.strip()
        if not name:
            continue

        filepath = target_dir / name
        if not filepath.parent.exists():
            filepath.parent.mkdir(parents=True, exist_ok=True)

        if content.strip():
            filepath.write_text(content, encoding="utf-8", errors="replace")
        else:
            print(f"WARNING: file {name} is empty")