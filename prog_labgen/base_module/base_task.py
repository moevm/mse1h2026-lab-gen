from __future__ import annotations

import hashlib
import json
import random
import subprocess
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class BaseTask(ABC):
    def __init__(
        self,
        student: str,
        fail_on_first_test: bool = True,
        compiler: str | None = None,
    ) -> None:
        self.student = student
        self.fail_on_first_test = fail_on_first_test
        self.compiler = compiler or "gcc"

    def make_seed_hash(self, salt: str = "") -> int:
        payload = self.student if not salt else f"{self.student}:{salt}"
        return int(hashlib.md5(payload.encode("utf-8")).hexdigest(), 16)

    def make_random(self, salt: str = "") -> random.Random:
        return random.Random(self.make_seed_hash(salt))

    def init_task(self) -> str:
        return self.render_assignment()

    def dry_run(self) -> str:
        return json.dumps(
            {
                "assignment": self.render_assignment(),
                "tests": self.generate_tests(),
            },
            ensure_ascii=False,
            indent=2,
        )

    @staticmethod
    def normalize_output(output: str) -> str:
        return output.replace("\r\n", "\n").strip()

    def compile_c_solution(
        self,
        solution_path: str,
        output_name: str = "prog",
        extra_flags: tuple[str, ...] = (),
    ) -> tuple[Path | None, str | None]:
        source_path = Path(solution_path)
        if not source_path.exists():
            return None, f"Solution file not found: {solution_path}"

        build_dir = Path(tempfile.mkdtemp(prefix="build-"))
        local_source = build_dir / "solution.c"
        output_path = build_dir / output_name
        local_source.write_bytes(source_path.read_bytes())

        cmd = [self.compiler, str(local_source), "-o", str(output_path), *extra_flags]
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
            )
        except FileNotFoundError:
            return None, f"Compiler '{self.compiler}' not found in PATH."

        if result.returncode != 0:
            error_text = result.stdout.strip() or "Compiler exited with a non-zero code without diagnostics."
            return None, error_text

        return output_path, None

    @staticmethod
    def run_binary(binary_path: Path, stdin_data: str) -> tuple[str | None, str | None]:
        result = subprocess.run(
            [str(binary_path)],
            input=stdin_data,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            combined = (result.stderr + result.stdout).strip()
            return None, f"Program exited with code {result.returncode}.\n{combined}"

        combined_output = result.stdout
        if result.stderr:
            combined_output += result.stderr
        return combined_output, None

    @abstractmethod
    def render_assignment(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def generate_tests(self) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def check(self, solution_path: str) -> tuple[bool, str]:
        raise NotImplementedError
