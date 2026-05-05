from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "main.py"
ARGS = argparse.Namespace(cc=None)


@dataclass(frozen=True)
class ExampleCase:
    label: str
    lab: str
    seed: str
    solution_path: Path
    expected_pass: bool
    command_kind: str = "main"


CASES: tuple[ExampleCase, ...] = (
    ExampleCase(
        label="lab1 good",
        lab="lab1",
        seed="Басыров",
        solution_path=ROOT / "examples" / "lab1_solution_good.c",
        expected_pass=True,
    ),
    ExampleCase(
        label="lab1 bad",
        lab="lab1",
        seed="Басыров",
        solution_path=ROOT / "examples" / "lab1_solution_bad.c",
        expected_pass=False,
    ),
    ExampleCase(
        label="lab2 good",
        lab="lab2",
        seed="example-lab2",
        solution_path=ROOT / "examples" / "lab2_solution_good.txt",
        expected_pass=True,
        command_kind="lab2_text",
    ),
    ExampleCase(
        label="lab2 bad",
        lab="lab2",
        seed="example-lab2",
        solution_path=ROOT / "examples" / "lab2_solution_bad.txt",
        expected_pass=False,
        command_kind="lab2_text",
    ),
    ExampleCase(
        label="lab3 good",
        lab="lab3",
        seed="example-lab3",
        solution_path=ROOT / "examples" / "lab3_solution_good.c",
        expected_pass=True,
    ),
    ExampleCase(
        label="lab3 bad",
        lab="lab3",
        seed="example-lab3",
        solution_path=ROOT / "examples" / "lab3_solution_bad.c",
        expected_pass=False,
    ),
    ExampleCase(
        label="lab4 good",
        lab="lab4",
        seed="2",
        solution_path=ROOT / "examples" / "lab4_solution_good.c",
        expected_pass=True,
    ),
    ExampleCase(
        label="lab4 bad",
        lab="lab4",
        seed="2",
        solution_path=ROOT / "examples" / "lab4_solution_bad.c",
        expected_pass=False,
    ),
)


def build_command(case: ExampleCase) -> list[str]:
    if case.command_kind == "lab2_text":
        return [
            sys.executable,
            "-m",
            "prog_labgen.lab2.lab2_cli",
            "--blob-file",
            str(case.solution_path),
            "--seed",
            case.seed,
            "--mode",
            "check",
        ]

    command = [
        sys.executable,
        str(MAIN),
        case.lab,
        "--seed",
        case.seed,
        "--mode",
        "check",
        "--solution",
        str(case.solution_path),
    ]
    if ARGS.cc is not None:
        command.extend(["--cc", ARGS.cc])
    return command


def detect_pass(case: ExampleCase, result: subprocess.CompletedProcess[str]) -> bool:
    output = (result.stdout or "").replace("\r\n", "\n").replace("\r", "\n")

    if case.command_kind == "lab2_text":
        first_line = next((line.strip() for line in output.splitlines() if line.strip()), "")
        if first_line == "OK":
            return True
        if first_line == "FAIL":
            return False
        return result.returncode == 0

    if "Passed: True" in output:
        return True
    if "Passed: False" in output:
        return False
    return result.returncode == 0


def run_case(case: ExampleCase) -> tuple[str, bool]:
    if not case.solution_path.exists():
        return f"{case.label}: SKIP (missing {case.solution_path.name})", True
    if ARGS.cc is None and shutil.which("gcc") is None:
        return f"{case.label}: SKIP (gcc not found in PATH; pass --cc to enable checks)", True

    result = subprocess.run(
        build_command(case),
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    passed = detect_pass(case, result)
    if passed == case.expected_pass:
        return f"{case.label}: OK", True

    return (
        f"{case.label}: FAIL\n"
        f"Expected pass={case.expected_pass}, got pass={passed}.\n"
        f"Output:\n{result.stdout.strip()}",
        False,
    )


def main() -> int:
    all_ok = True
    for case in CASES:
        message, ok = run_case(case)
        print(message)
        all_ok = all_ok and ok
    return 0 if all_ok else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cc", type=str, default=None)
    ARGS = parser.parse_args()
    raise SystemExit(main())
