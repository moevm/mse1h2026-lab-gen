from __future__ import annotations

import shutil
from dataclasses import dataclass
from typing import Any, List

from prog_labgen.base_module.base_task import BaseTask


@dataclass(frozen=True)
class Limits:
    line_max: int = 10000
    element_max: int = 200
    word_max: int = 64


@dataclass(frozen=True)
class Variant:
    seed: str
    seed_hash: int
    delimiters: str
    allow_empty: bool
    allow_duplicates: bool
    select_rule: str
    sort_rule: str
    summary_rule: str
    pattern: str | None
    limits: Limits


@dataclass(frozen=True)
class SolveResult:
    elements: List[str]
    found: bool
    summary: str

    def render_output(self) -> str:
        if not self.elements:
            first = "empty"
        else:
            first = " ".join(self.elements)

        second = "exists" if self.found else "doesn't exist"

        return "\n".join([first, second, self.summary])

