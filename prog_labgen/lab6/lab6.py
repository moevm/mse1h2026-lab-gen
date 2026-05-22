from __future__ import annotations

from typing import Any

from prog_labgen.base_module import BaseTask


class Lab6Task(BaseTask):
    def __init__(self, seed: str, tests_count: int = 5, fail_on_first_test: bool = True, compiler: str | None = None) -> None:
        super().__init__(seed=seed, fail_on_first_test=fail_on_first_test, compiler=compiler)
        self.tests_count = tests_count

    def render_assignment(self) -> str:
        return f"Концепция варианта ЛР6\nSeed: {self.seed}"

    def generate_tests(self) -> list[dict[str, Any]]:
        return []

    def check(self, solution_path: str) -> tuple[bool, str]:
        return False, "Lab6 checker is not implemented yet"
