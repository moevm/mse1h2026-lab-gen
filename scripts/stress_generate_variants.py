from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "main.py"
DEFAULT_LABS = ("lab1", "lab2", "lab3", "lab4")
DEFAULT_MODES = ("init", "dry-run")
DEFAULT_SEED_FILE = ROOT / "scripts" / "seed_to_check.txt"
FORBIDDEN_MARKERS = ("Traceback", "None", "TODO", "<undefined>")
REQUIRED_DRY_RUN_KEYS = ("assignment",)
OPTIONAL_TEST_INPUT_KEYS = ("stdin", "input_text")


@dataclass(frozen=True)
class CheckFailure:
    lab: str
    seed: str
    mode: str
    command: list[str]
    reason: str
    output: str


def read_seed_file(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def build_seeds(seed_file: Path, generated_count: int) -> list[str]:
    seeds = read_seed_file(seed_file)
    seeds.extend(f"ci-seed-{index:04d}" for index in range(generated_count))
    return list(dict.fromkeys(seeds))


def build_command(runner: str, lab: str, seed: str, mode: str) -> list[str]:
    if runner == "labgen":
        return ["labgen", lab, "--seed", seed, "--mode", mode]
    return [sys.executable, str(MAIN), lab, "--seed", seed, "--mode", mode]


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )


def validate_output(
    lab: str,
    seed: str,
    mode: str,
    command: list[str],
    result: subprocess.CompletedProcess[str],
) -> CheckFailure | None:
    output = result.stdout or ""
    if result.returncode != 0:
        return CheckFailure(lab, seed, mode, command, "non-zero exit code", output)
    if not output.strip():
        return CheckFailure(lab, seed, mode, command, "empty output", output)

    for marker in FORBIDDEN_MARKERS:
        if marker in output:
            return CheckFailure(
                lab,
                seed,
                mode,
                command,
                f"forbidden marker found: {marker}",
                output,
            )

    if mode == "dry-run":
        json_failure = validate_json_dry_run(lab, seed, mode, command, output)
        if json_failure is not None:
            return json_failure

    return None


def validate_json_dry_run(
    lab: str,
    seed: str,
    mode: str,
    command: list[str],
    output: str,
) -> CheckFailure | None:
    stripped = output.strip()
    if not stripped.startswith("{"):
        return None

    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError as exc:
        return CheckFailure(
            lab,
            seed,
            mode,
            command,
            f"dry-run output looks like JSON but is invalid: {exc}",
            output,
        )

    if not isinstance(payload, dict):
        return CheckFailure(lab, seed, mode, command, "dry-run JSON is not an object", output)

    for key in REQUIRED_DRY_RUN_KEYS:
        if key not in payload:
            return CheckFailure(
                lab,
                seed,
                mode,
                command,
                f"dry-run JSON misses required key: {key}",
                output,
            )

    tests = payload.get("tests")
    if tests is None:
        return None
    if not isinstance(tests, list) or not tests:
        return CheckFailure(lab, seed, mode, command, "dry-run JSON has empty tests", output)

    for index, test in enumerate(tests):
        if not isinstance(test, dict):
            return CheckFailure(
                lab,
                seed,
                mode,
                command,
                f"dry-run test #{index} is not an object",
                output,
            )
        if not any(key in test for key in OPTIONAL_TEST_INPUT_KEYS):
            return CheckFailure(
                lab,
                seed,
                mode,
                command,
                f"dry-run test #{index} has no input field",
                output,
            )
        if "expected_stdout" not in test:
            return CheckFailure(
                lab,
                seed,
                mode,
                command,
                f"dry-run test #{index} has no expected_stdout",
                output,
            )

    return None


def check_determinism(
    lab: str,
    seed: str,
    mode: str,
    command: list[str],
    first_output: str,
) -> CheckFailure | None:
    second = run_command(command)
    if second.returncode != 0:
        return CheckFailure(
            lab,
            seed,
            mode,
            command,
            "determinism rerun returned non-zero exit code",
            second.stdout or "",
        )
    if second.stdout != first_output:
        return CheckFailure(
            lab,
            seed,
            mode,
            command,
            "same seed produced different output",
            second.stdout or "",
        )
    return None


def format_failure(failure: CheckFailure) -> str:
    command = " ".join(failure.command)
    output = failure.output.strip()
    return (
        "FAILED\n"
        f"lab={failure.lab}\n"
        f"seed={failure.seed}\n"
        f"mode={failure.mode}\n"
        f"reason={failure.reason}\n\n"
        "Reproduce:\n"
        f"{command}\n\n"
        "Output:\n"
        f"{output}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Stress-check lab generation on many seeds."
    )
    parser.add_argument("--labs", nargs="+", default=list(DEFAULT_LABS))
    parser.add_argument("--modes", nargs="+", default=list(DEFAULT_MODES))
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--seed-file", type=Path, default=DEFAULT_SEED_FILE)
    parser.add_argument("--runner", choices=("main", "labgen"), default="main")
    parser.add_argument("--no-determinism", action="store_true")
    parser.add_argument("--min-unique-init", type=int, default=2)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    seeds = build_seeds(args.seed_file, args.count)
    total = len(args.labs) * len(args.modes) * len(seeds)
    failures: list[CheckFailure] = []
    init_digests: dict[str, set[str]] = {lab: set() for lab in args.labs}
    init_commands: dict[str, list[str]] = {}

    print(
        f"Checking {len(args.labs)} labs, {len(args.modes)} modes, "
        f"{len(seeds)} seeds ({total} commands)"
    )

    checked = 0
    for lab in args.labs:
        for seed in seeds:
            for mode in args.modes:
                command = build_command(args.runner, lab, seed, mode)
                result = run_command(command)
                failure = validate_output(lab, seed, mode, command, result)
                if failure is None and not args.no_determinism:
                    failure = check_determinism(
                        lab,
                        seed,
                        mode,
                        command,
                        result.stdout or "",
                    )
                if failure is None and mode == "init":
                    digest = hashlib.sha256((result.stdout or "").encode()).hexdigest()
                    init_digests[lab].add(digest)
                    init_commands.setdefault(lab, command)

                checked += 1
                if failure is None:
                    continue

                failures.append(failure)
                print(format_failure(failure))

    if args.min_unique_init > 1 and len(seeds) >= args.min_unique_init:
        for lab, digests in init_digests.items():
            if len(digests) >= args.min_unique_init:
                continue
            command = init_commands.get(
                lab,
                build_command(args.runner, lab, seeds[0], "init"),
            )
            failure = CheckFailure(
                lab=lab,
                seed=",".join(seeds[: min(5, len(seeds))]),
                mode="init",
                command=command,
                reason=(
                    f"not enough unique init outputs: "
                    f"{len(digests)} < {args.min_unique_init}"
                ),
                output="",
            )
            failures.append(failure)
            print(format_failure(failure))

    if failures:
        print(f"Stress generation failed: {len(failures)} failures of {checked} checks")
        return 1

    print(f"Stress generation passed: {checked} checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
