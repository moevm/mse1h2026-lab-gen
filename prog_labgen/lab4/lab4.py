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


class Lab4Task(BaseTask):
    def __init__(
        self,
        seed: str,
        line_max: int = 10000,
        element_max: int = 200,
        word_max: int = 64,
        tests_count: int = 10,
        fail_on_first_test: bool = True,
        compiler: str | None = None,
    ) -> None:
        super().__init__(seed=seed,
                         fail_on_first_test=fail_on_first_test,
                         compiler=compiler)
        self.limits = Limits(line_max=line_max, element_max=element_max, word_max=word_max)
        self.tests_count = max(1, tests_count)
        self._variant: Variant | None = None

    def _build_variant(self) -> Variant:
        if self._variant is not None:
            return self._variant

        rng = self.make_random()

        # разделители: непустое подмножество { ' ', '\t', ',', ';' }
        delimiters_pool = [' ', '\t', ',', ';']
        k = rng.randint(1, len(delimiters_pool))
        delimiters = "".join(rng.sample(delimiters_pool, k))

        select_rule = rng.choice([
            "digits", "alpha", "lower", "upper", "prefix", "substring"
        ])

        pattern = None
        if select_rule in ("prefix", "substring"):
            pattern = "".join(rng.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(3))

        self._variant = Variant(
            seed=self.seed,
            seed_hash=self.make_seed_hash(),
            delimiters=delimiters,
            allow_empty=rng.choice([True, False]),
            allow_duplicates=rng.choice([True, False]),
            select_rule=select_rule,
            sort_rule=rng.choice(["asc", "desc"]),
            summary_rule=rng.choice(["count", "first_last", "maxlen", "minlen"]),
            pattern=pattern,
            limits=self.limits,
        )
        return self._variant

    def render_assignment(self) -> str:
        v = self._build_variant()
        lines = [
            "Лабораторная работа 4",
            f"Seed: {v.seed}",
            f"Seed hash: {v.seed_hash}",
            f"LineMax: {v.limits.line_max}",
            f"ElementMax: {v.limits.element_max}",
            f"WordMax: {v.limits.word_max}",
            "Напишите программу на языке Си, которая читает строку элементов, ",
            "обрабатывает её и выводит результат, используя функции стандартной библиотеки.",
            "На вход программе подаются:",
            "- строка с элементами",
            "- строка-запрос",
            "Общие требования:",
            "- считать строку элементов и строку-запрос через fgets",
            "- разделить строку на элементы по следующим разделителям",
            f"(сами разделители удаляются): {repr(v.delimiters)},",
            "для поиска разделителей используйте strcspn или strpbrk",
            f"- после разделения строки пустые элементы необходимо {'сохранить' if v.allow_empty else 'удалить'}",
            f"- среди оставшихся элементов выполнить отбор по правилу:",
            f"\t{_describe_select_rule(v)}",
            f"Отсортировать оставшиеся элементы по правилу:",
            f"\t{_describe_sort_rule(v)}",
            f"- если образовались одинаковые элементы, то нужно оставить {'все' if v.allow_duplicates else 'только один'} из них",
            "- определить наличие строки-запроса среди выбранных элементов через bsearch,",
            "используя strcmp для сравнения элементов",
            "В качестве ответа нужно вывести:",
            "- полученные после обработки элементы в одну строку через пробел,",
            "при их отсутствии вывести 'empty'",
            "- вывести результат поиска строки-запроса среди элементов: exists/doesn't exist",
            f"- вывести {_describe_summary_rule(v)} в следующем формате: '{_describe_summary_format(v)}'",
        ]
        return "\n".join(lines)

    def generate_tests(self) -> list[dict[str, Any]]:
        variant = self._build_variant()
        tests: list[dict[str, Any]] = []
        rng = self.make_random("testgen")

        # специфичные тесты для текущего варианта (покрывают все правила)
        rule_tests = self._generate_rule_specific_tests(variant, rng)

        if len(rule_tests) > self.tests_count:
            rule_tests = rule_tests[:self.tests_count]

        for i, (elements, query) in enumerate(rule_tests, start=1):
            # собираем строку, вставляя разделители и иногда создавая пустые элементы
            line = self._join_elements_with_delimiters(elements, variant, rng)
            stdin_data = f"{line}\n{query}\n"
            expected = normalize_output(solve(line, query, variant).render_output()) + "\n"
            tests.append({
                "input_text": stdin_data,
                "stdin": stdin_data,
                "expected_stdout": expected,
                "test_id": f"rule_{i}"
            })

        # случайные тесты (заполняем оставшиеся слоты до tests_count)
        remaining = self.tests_count - len(tests)
        for i in range(1, remaining + 1):
            stdin_data, expected = self._generate_random_test(variant, rng)
            tests.append({
                "input_text": stdin_data,
                "stdin": stdin_data,
                "expected_stdout": expected,
                "test_id": f"random_{i}"
            })

        return tests


    def _join_elements_with_delimiters(self, elements: List[str], variant: Variant, rng) -> str:
        """Собирает строку из элементов, вставляя разделители из variant.delimiters."""
        if not elements:
            return ""
        
        sep = list(variant.delimiters)
        parts = []
        for i, el in enumerate(elements):
            parts.append(el)
            if i < len(elements) - 1:
                # случайный разделитель (иногда несколько подряд для пустых элементов)
                if variant.allow_empty and rng.random() < 0.3:
                    parts.append(rng.choice(sep) * rng.randint(1, 3))
                else:
                    parts.append(rng.choice(sep))
        
        return "".join(parts)


    def _generate_rule_specific_tests(self, variant: Variant, rng) -> list[tuple[list[str], str]]:
        """Генерирует тесты, специфичные для правил текущего варианта."""
        tests = []

        def generate_elements(count: int, with_empty: bool = False) -> list[str]:
            """Генерирует список элементов с заданными характеристиками."""
            elements = []
            for _ in range(count):
                length = rng.randint(1, variant.limits.word_max)
                kind = rng.choice(["alpha", "digit", "mixed"])
                if kind == "alpha":
                    chars = [rng.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(length)]
                elif kind == "digit":
                    chars = [rng.choice("0123456789") for _ in range(length)]
                else:
                    pool = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
                    chars = [rng.choice(pool) for _ in range(length)]
                elements.append("".join(chars))
            
            if with_empty:
                for _ in range(rng.randint(1, 3)):
                    pos = rng.randint(0, len(elements))
                    elements.insert(pos, "")
            
            return elements

        def generate_elements_for_rule(rule: str, count: int) -> list[str]:
            """Генерирует элементы, подходящие под правило отбора."""
            elements = []
            pattern = variant.pattern or "".join(rng.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(3))
            
            for i in range(count):
                if rule == "digits":
                    length = rng.randint(1, variant.limits.word_max)
                    elements.append("".join(rng.choice("0123456789") for _ in range(length)))
                elif rule == "alpha":
                    length = rng.randint(1, variant.limits.word_max)
                    elements.append("".join(rng.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(length)))
                elif rule == "lower":
                    length = rng.randint(1, variant.limits.word_max)
                    elements.append("".join(rng.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(length)))
                elif rule == "upper":
                    length = rng.randint(1, variant.limits.word_max)
                    elements.append("".join(rng.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(length)))
                elif rule == "prefix":
                    suffix_len = rng.randint(0, variant.limits.word_max - len(pattern))
                    suffix = "".join(rng.choice("abcdefghijklmnopqrstuvwxyz0123456789") for _ in range(suffix_len))
                    elements.append(pattern + suffix)
                elif rule == "substring":
                    prefix_len = rng.randint(0, variant.limits.word_max - len(pattern))
                    suffix_len = rng.randint(0, variant.limits.word_max - len(pattern) - prefix_len)
                    prefix = "".join(rng.choice("abcdefghijklmnopqrstuvwxyz0123456789") for _ in range(prefix_len))
                    suffix = "".join(rng.choice("abcdefghijklmnopqrstuvwxyz0123456789") for _ in range(suffix_len))
                    elements.append(prefix + pattern + suffix)
            
            return elements

        matching_elements = generate_elements_for_rule(variant.select_rule, 3)
        non_matching = generate_elements(2)
        non_matching = [e for e in non_matching if not select_element(e, variant)]
        all_elements = matching_elements[:2] + non_matching + matching_elements[2:]
        query = rng.choice(matching_elements)
        tests.append((all_elements, query))

        matching = generate_elements_for_rule(variant.select_rule, 3)
        non_matching_query = generate_elements(1)
        while select_element(non_matching_query[0], variant):
            non_matching_query = generate_elements(1)
        tests.append((matching + non_matching_query, non_matching_query[0]))

        if variant.allow_empty:
            elements_with_empty = generate_elements(3, with_empty=True)
            if elements_with_empty:
                query = rng.choice([e for e in elements_with_empty if e != ""]) if any(e != "" for e in elements_with_empty) else ""
                tests.append((elements_with_empty, query))
        else:
            mixed = generate_elements(2, with_empty=True)
            matching = generate_elements_for_rule(variant.select_rule, 2)
            all_mixed = mixed + matching
            query = rng.choice(matching) if matching else "test"
            tests.append((all_mixed, query))

        base_elements = generate_elements_for_rule(variant.select_rule, 2)
        if base_elements:
            duplicated = base_elements + base_elements
            tests.append((duplicated, base_elements[0]))

        unsorted = generate_elements_for_rule(variant.select_rule, 5)
        if unsorted:
            rng.shuffle(unsorted)
            query = unsorted[0] if unsorted else "test"
            tests.append((unsorted, query))

        tests.append(([], "anything"))

        single = generate_elements_for_rule(variant.select_rule, 1)
        if single:
            tests.append((single, single[0]))
        else:
            tests.append((["solitary"], "solitary"))

        present = generate_elements_for_rule(variant.select_rule, 3)
        absent_query = "nonexistent_query_xyz"
        tests.append((present, absent_query))

        return tests

    def _generate_random_test(self, variant: Variant, rng) -> tuple[str, str]:
        """Создаёт случайный вход (строка элементов + запрос) и возвращает (stdin, expected_stdout)."""
        n = rng.randint(0, min(10, variant.limits.element_max))
        elements = []
        
        for _ in range(n):
            length = rng.randint(0, variant.limits.word_max)
            kind = rng.choice(["alpha", "digit", "mixed", "rule_specific"])
            
            if kind == "alpha":
                chars = [rng.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(length)]
            elif kind == "digit":
                chars = [rng.choice("0123456789") for _ in range(length)]
            elif kind == "mixed":
                pool = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
                chars = [rng.choice(pool) for _ in range(length)]
            else:  # rule_specific — генерируем так, чтобы иногда подходило под правило
                if variant.select_rule == "digits":
                    chars = [rng.choice("0123456789") for _ in range(length)]
                elif variant.select_rule == "alpha":
                    chars = [rng.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(length)]
                elif variant.select_rule == "lower":
                    chars = [rng.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(length)]
                elif variant.select_rule == "upper":
                    chars = [rng.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(length)]
                elif variant.select_rule == "prefix" and variant.pattern:
                    suffix_len = max(0, length - len(variant.pattern))
                    chars = list(variant.pattern) + [rng.choice("abcdefghijklmnopqrstuvwxyz0123456789") for _ in range(suffix_len)]
                elif variant.select_rule == "substring" and variant.pattern:
                    prefix_len = rng.randint(0, max(0, length - len(variant.pattern)))
                    suffix_len = max(0, length - len(variant.pattern) - prefix_len)
                    chars = (
                        [rng.choice("abcdefghijklmnopqrstuvwxyz0123456789") for _ in range(prefix_len)] +
                        list(variant.pattern) +
                        [rng.choice("abcdefghijklmnopqrstuvwxyz0123456789") for _ in range(suffix_len)]
                    )
                else:
                    pool = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
                    chars = [rng.choice(pool) for _ in range(length)]
            
            elements.append("".join(chars))
        
        # Собираем строку с разделителями
        line = self._join_elements_with_delimiters(elements, variant, rng)
        line = line[:variant.limits.line_max]
        
        # Генерируем запрос
        matching_elements = [e for e in elements if select_element(e, variant)]
        if matching_elements and rng.random() < 0.7:
            query = rng.choice(matching_elements)
        elif elements and rng.random() < 0.5:
            query = rng.choice(elements)
        else:
            query = "".join(rng.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(rng.randint(0, 5)))
        
        stdin_data = f"{line}\n{query}\n"
        expected = normalize_output(solve(line, query, variant).render_output()) + "\n"
        return stdin_data, expected

    def check(self, solution_path: str) -> tuple[bool, str]:
        is_stdlib_used, info = self._check_stdlib_usage(solution_path)
        if (not is_stdlib_used):
            return False, info

        binary_path, compile_error = self.compile_c_solution(
            solution_path,
            output_name="lab4_solution",
        )
        if compile_error is not None or binary_path is None:
            return False, f"Ошибка компиляции решения:\n{compile_error}"

        total_tests = 0
        passed_tests = 0
        messages: list[str] = []

        try:
            for index, test_case in enumerate(self.generate_tests(), start=1):
                total_tests += 1
                obtained, runtime_error = self.run_binary(binary_path, test_case["stdin"])

                if runtime_error is not None:
                    messages.append(
                        f"Тест {index}: FAIL\n"
                        f"Вход:\n{test_case['input_text']}\n"
                        f"Ошибка выполнения:\n{runtime_error}"
                    )
                    if self.fail_on_first_test:
                        break
                    continue

                # нормализуем строки перед сравнением
                expected = test_case["expected_stdout"]
                actual = (normalize_output(obtained or "")) + "\n"

                if actual == expected:
                    passed_tests += 1
                    messages.append(f"Тест {index}: OK")
                    continue

                messages.append(
                    f"Тест {index}: FAIL\n"
                    f"Вход:\n{test_case['input_text']}\n"
                    f"Ожидалось:\n{expected}\n"
                    f"Получено:\n{actual}"
                )
                if self.fail_on_first_test:
                    break
        finally:
            # очистка временной папки
            if binary_path is not None and binary_path.exists():
                binary_path.unlink()
            try:
                binary_path.parent.rmdir()
            except OSError:
                pass
            shutil.rmtree(str(binary_path.parent), ignore_errors=True)

        summary = f"Итог: {passed_tests}/{total_tests} тестов пройдено"
        all_passed = passed_tests == total_tests
        footer = "Все тесты пройдены" if all_passed else "Есть ошибки"
        return all_passed, "\n".join(messages + [summary, footer])

    def _check_stdlib_usage(self, solution_path: str) -> tuple[bool, str]:
        # Функции, которые должны присутствовать обязательно
        required = [
            "fgets",
            "strcmp",
            "qsort",
            "bsearch",
        ]
        
        # Группы функций, где нужно использовать хотя бы одну из группы
        alternative_groups = [
            ["strcspn", "strpbrk"],  # хотя бы одна для поиска разделителей
        ]

        with open(solution_path, "r", encoding="utf-8") as f:
            code = f.read()

        missing = []
        
        # Проверяем обязательные функции
        for req in required:
            if req not in code:
                missing.append(req)
        
        # Проверяем альтернативные группы
        for group in alternative_groups:
            if not any(func in code for func in group):
                missing.append(f"{' или '.join(group)}")

        if missing:
            return False, f"Не используются требуемые функции stdlib: {missing}"

        return True, ""


def _describe_select_rule(variant: Variant) -> str:
    if variant.select_rule == "digits":
        return "Выбрать только те элементы, каждый символ которых является цифрой"
    if variant.select_rule == "alpha":
        return "Выбрать только те элементы, каждый символ которых является буквой"
    if variant.select_rule == "lower":
        return "Выбрать только те буквенные элементы, каждый символ которых находится в нижнем регистре"
    if variant.select_rule == "upper":
        return "Выбрать только те буквенные элементы, каждый символ которых находится в верхнем регистре"
    if variant.select_rule == "prefix":
        if variant.pattern:
            return f"Выбрать только те элементы, которые начинаются с префикса {variant.pattern}"
    if variant.select_rule == "substring":
        if variant.pattern:
            return f"Выбрать только те элементы, которые содержат заданную подстроку {variant.pattern}"
    return ""

def _describe_sort_rule(variant: Variant) -> str:
    if variant.sort_rule == "asc":
        return "Отсортировать выбранные элементы лексикографически по возрастанию"
    if variant.sort_rule == "desc":
        return "Отсортировать выбранные элементы лексикографически по убыванию"
    return ""

def _describe_summary_rule(variant: Variant) -> str:
    if variant.summary_rule == "count":
        return "количество элементов, полученное после отбора"
    if variant.summary_rule == "maxlen":
        return "длину самого длинного элемента в отобранном наборе"
    if variant.summary_rule == "minlen":
        return "длину самого короткого элемента в отобранном наборе"
    if variant.summary_rule == "first_last":
        return "первый и последний элементы в отобранном наборе"

def _describe_summary_format(variant: Variant) -> str:
    if variant.summary_rule == "count":
        return "summary: count=<число>"
    if variant.summary_rule == "maxlen":
        return "summary: maxlen=<число>"
    if variant.summary_rule == "minlen":
        return "summary: minlen=<число>"
    if variant.summary_rule == "first_last":
        return "summary: first=<элемент> last=<элемент>"