from __future__ import annotations

import subprocess
import sys


LABS = ("lab1", "lab2", "lab3", "lab4")


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "main.py", *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )


def test_init_smoke_for_all_labs() -> None:
    for lab in LABS:
        result = run_cli(lab, "--seed", "smoke-seed", "--mode", "init")

        assert result.returncode == 0, result.stdout
        assert "Traceback" not in result.stdout
        assert "Seed:" in result.stdout


def test_dry_run_smoke_for_all_labs() -> None:
    for lab in LABS:
        result = run_cli(lab, "--seed", "smoke-seed", "--mode", "dry-run")

        assert result.returncode == 0, result.stdout
        assert "Traceback" not in result.stdout
        assert '"assignment"' in result.stdout
        assert '"tests"' in result.stdout


def test_invalid_cli_args_do_not_traceback() -> None:
    cases = (
        ("lab1", "--seed", "smoke-seed", "--mode", "init", "--k", "600"),
        ("lab3", "--seed", "smoke-seed", "--mode", "init", "--word-max", "1"),
        ("lab4", "--seed", "smoke-seed", "--mode", "init", "--word-max", "1"),
    )

    for args in cases:
        result = run_cli(*args)

        assert result.returncode != 0
        assert "Traceback" not in result.stdout
