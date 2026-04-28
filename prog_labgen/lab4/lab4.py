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


# Разбиение строки по разделителям (через strcspn / strpbrk в Си)
def split_line(line: str, delimiters: str) -> List[str]:
    res = []
    cur = ""
    for ch in line:
        if ch in delimiters:
            res.append(cur)
            cur = ""
        else:
            cur += ch
    res.append(cur)
    return res


# Обработка пустых значений
def handle_empty(arr: List[str], allow: bool) -> List[str]:
    if allow:
        return arr
    return [x for x in arr if x != ""]


# Проверка элемента на соответсвие правилу select_rule
def select_element(s: str, variant: Variant) -> bool:
    if variant.select_rule == "digits":
        return bool(s) and all(c.isdigit() for c in s)
    if variant.select_rule == "alpha":
        return bool(s) and all(c.isalpha() for c in s)
    if variant.select_rule == "lower":
        return bool(s) and all(c.islower() for c in s)
    if variant.select_rule == "upper":
        return bool(s) and all(c.isupper() for c in s)
    if variant.select_rule == "prefix":
        return s.startswith(variant.pattern or "")
    if variant.select_rule == "substring":
        return (variant.pattern or "") in s
    return False


# Отбор элементов по правилу select_rule
def filter_elements(arr: List[str], variant: Variant) -> List[str]:
    return [x for x in arr if select_element(x, variant)]


# Сортировка элементов
def sort_elements(arr: List[str], variant: Variant) -> List[str]:
    return sorted(arr, reverse=(variant.sort_rule == "desc"))


# Отбор уникальных элементов
def unique_elements(arr: List[str], allow: bool) -> List[str]:
    if allow:
        return arr
    res = []
    for x in arr:
        if not res or res[-1] != x:
            res.append(x)
    return res


# Вывод дополнительной характеристики набора
def make_summary(arr: List[str], variant: Variant) -> str:
    if not arr:
        if variant.summary_rule == "count":
            return "summary: count=0"
        if variant.summary_rule == "maxlen":
            return "summary: maxlen=0"
        if variant.summary_rule == "minlen":
            return "summary: minlen=0"
        return "summary: first= last="

    if variant.summary_rule == "count":
        return f"summary: count={len(arr)}"
    if variant.summary_rule == "first_last":
        return f"summary: first={arr[0]} last={arr[-1]}"
    if variant.summary_rule == "maxlen":
        return f"summary: maxlen={max(len(x) for x in arr)}"
    if variant.summary_rule == "minlen":
        return f"summary: minlen={min(len(x) for x in arr)}"
    return "summary: count=0"


def normalize_output(text: str) -> str:
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


# Запуск всех этапов решения и возвращение результата
def solve(line: str, query: str, variant: Variant) -> SolveResult:
    arr = split_line(line, variant.delimiters)
    arr = handle_empty(arr, variant.allow_empty)
    arr = filter_elements(arr, variant)
    arr = sort_elements(arr, variant)
    arr = unique_elements(arr, variant.allow_duplicates)

    found = query in arr
    summary = make_summary(arr, variant)

    return SolveResult(arr, found, summary)

