from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from prog_labgen.base_module import BaseTask, rand_int, rand_int_array, rand_sample


STANDARD_DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
LEADING_ZERO_WIDTH = 4

class NumberSystem:
    def encode(self, value: int) -> str:
        raise NotImplementedError

    def encode_with_leading_zeros(self, value: int) -> str:
        return self.encode(value)

    def get_format(self) -> str:
        raise NotImplementedError

    def render_description(self) -> list[str]:
        raise NotImplementedError


class PositionalNumberSystem(NumberSystem):
    def __init__(self, base: int) -> None:
        if base < 2:
            raise ValueError("base must be greater than or equal to 2")
        self.base = base

    def encode(self, value: int) -> str:
        sign = "-" if value < 0 else ""
        digits = self._digits(value)

        if self._is_standard():
            return sign + "".join(STANDARD_DIGITS[digit] for digit in digits)

        return sign + ":".join(str(digit) for digit in digits)

    def encode_with_leading_zeros(self, value: int) -> str:
        sign = "-" if value < 0 else ""
        digits = self._digits(value)

        if self._is_standard():
            encoded = "".join(STANDARD_DIGITS[digit] for digit in digits)
            return sign + encoded.rjust(LEADING_ZERO_WIDTH, "0")

        return sign + ":".join(str(digit).rjust(LEADING_ZERO_WIDTH, "0") for digit in digits)

    def get_format(self) -> str:
        if self._is_standard():
            return "standard"
        return "tokenized"

    def render_description(self) -> list[str]:
        if self._is_standard():
            return [
                f"Основание системы счисления: {self.base}.",
                "Числа во входном массиве и результаты вывода записываются в этой системе счисления.",
                "Для цифр используются символы 0-9 и A-Z.",
            ]

        return [
            f"Основание системы счисления: {self.base}.",
            "Числа во входном массиве и результаты вывода записываются в системе счисления с этим основанием.",
            "Так как основание больше 36, для записи числа нельзя использовать обычный набор символов 0-9A-Z:",
            "его не хватает для всех возможных разрядов. Поэтому используется токенизированная запись.",
            f"В такой записи каждый разряд числа записывается отдельным десятичным числом от 0 до {self.base - 1},",
            "а соседние разряды разделяются символом ':'.",
            f"Например, десятичное число {self.base + 5} записывается как 1:5, т.к.",
            f"{self.base + 5} = 1 * {self.base} + 5.",
            f"Таким же образом десятичное число 123456 записывается как {self.encode(123456)}.",
            f"Отрицательное число -{self.base + 5} записывается как -1:5.",
            "Во входных данных могут встретиться ведущие нули в разрядах, например 0001:0005.",
            "Такое число нужно понимать так же, как 1:5. В ответе ведущие нули выводить не нужно.",
        ]

    def _is_standard(self) -> bool:
        return self.base <= len(STANDARD_DIGITS)

    def _digits(self, value: int) -> list[int]:
        if value == 0:
            return [0]

        current = abs(value)
        digits: list[int] = []

        while current > 0:
            digits.append(current % self.base)
            current //= self.base

        digits.reverse()
        return digits


def make_number_system(kind: str, base: int | None = None) -> NumberSystem:
    if kind == "positional":
        if base is None:
            raise ValueError("base is required for positional number system")
        return PositionalNumberSystem(base)

    raise ValueError(f"unknown number system: {kind}")


@dataclass(frozen=True)
class TaskSpec:
    title: str
    params: tuple[str, ...]
    description: str
    func: Callable[..., int]


def first_multiple_index(arr: list[int], m: int) -> int:
    if m == 0:
        return -1
    for index, value in enumerate(arr):
        if value % m == 0:
            return index
    return -1


def last_abs_gt_index(arr: list[int], t: int) -> int:
    for index in range(len(arr) - 1, -1, -1):
        if abs(arr[index]) > t:
            return index
    return -1


def count_in_range(arr: list[int], a: int, b: int) -> int:
    if a > b:
        return 0
    return sum(1 for value in arr if a <= value <= b)


def sum_abs_step(arr: list[int], p: int, k_step: int) -> int:
    if p >= len(arr) or k_step < 1:
        return 0
    return sum(abs(arr[index]) for index in range(p, len(arr), k_step))


def sum_divisible(arr: list[int], d: int) -> int:
    if d == 0:
        return 0
    return sum(value for value in arr if value % d == 0)


def count_abs_lt(arr: list[int], limit: int) -> int:
    return sum(1 for value in arr if abs(value) < limit)


TASKS: dict[int, TaskSpec] = {
    1: TaskSpec("Первый элемент, кратный M", ("M",), "Выведите индекс первого элемента массива, который делится на M без остатка.\n Если такого элемента нет, выведите -1.", first_multiple_index),
    2: TaskSpec("Последний элемент по модулю больше T", ("T",), "Выведите индекс последнего элемента массива, для которого |a[i]| > T.\n Если такого элемента нет, выведите -1.", last_abs_gt_index),
    3: TaskSpec("Количество элементов в диапазоне [A; B]", ("A", "B"), "Выведите количество элементов массива, удовлетворяющих A <= a[i] <= B.", count_in_range),
    4: TaskSpec("Сумма модулей на позициях с шагом K, начиная с P", ("P", "K_step"), "Посчитайте сумму |a[i]| по индексам P, P+K, P+2K, ...\n пока индекс меньше длины массива.", sum_abs_step),
    5: TaskSpec("Сумма элементов, делящихся на D", ("D",), "Посчитайте сумму всех элементов массива, которые делятся на D без остатка.\n Если таких элементов нет, выведите 0.", sum_divisible),
    6: TaskSpec("Количество элементов, которые по модулю меньше L", ("L",), "Посчитайте количество элементов массива, для которых |a[i]| < L.", count_abs_lt),
}

DISPLAY_NAMES = {
    "K_step": "K",
}


class Lab1Task(BaseTask):
    def __init__(
        self,
        seed: str,
        n_max: int = 100,
        sep: str = " ",
        k: int = 3,
        tests_per_task: int = 5,
        random_base: bool = False,
        base_min: int = 10,
        base_max: int = 10,
        number_system_kind: str = "positional",
        fail_on_first_test: bool = True,
        compiler: str | None = None,
    ) -> None:
        if random_base and n_max < 6:
            raise ValueError("n_max must be at least 6 for random-base mode")

        super().__init__(seed=seed, fail_on_first_test=fail_on_first_test, compiler=compiler)
        self.n_max = n_max
        self.sep = sep
        self.k = k
        self.tests_per_task = tests_per_task
        self.random_base = random_base
        self.base_min = base_min
        self.base_max = base_max
        self.number_system_kind = number_system_kind
        self._variant: dict | None = None

    def _build_variant(self) -> dict:
        if self._variant is not None:
            return self._variant

        rnd = self.make_random()
        selected_tasks = rand_sample(rnd, sorted(TASKS.keys()), self.k)

        base = 10
        if self.random_base:
            base_rnd = self.make_random("lab1-number-system-base")
            base = rand_int(base_rnd, self.base_min, self.base_max)

        number_system = make_number_system(self.number_system_kind, base)
        params = {"N_max": self.n_max, "K": self.k, "BASE": base}

        for task_id in selected_tasks:
            for param_name in TASKS[task_id].params:
                if param_name in {"M", "D", "L", "T", "P"}:
                    params[param_name] = rand_int(rnd, 2, 12)
                elif param_name == "A":
                    params[param_name] = rand_int(rnd, 0, int(self.n_max * 0.2))
                elif param_name == "B":
                    params[param_name] = rand_int(rnd, int(self.n_max * 0.8), self.n_max)
                elif param_name == "K_step":
                    params[param_name] = rand_int(rnd, 1, 5)

        self._variant = {
            "seed": self.seed,
            "seed_hash": self.make_seed_hash(),
            "tasks": selected_tasks,
            "params": params,
            "number_system": {
                "kind": self.number_system_kind,
                "base": base,
                "format": number_system.get_format(),
                "random_base": self.random_base,
            },
        }
        return self._variant

    def _make_random_array(self, salt: str) -> list[int]:
        rnd = self.make_random(salt)

        return rand_int_array(
            rnd,
            size_min=max(1, int(self.n_max * 0.1)),
            size_max=self.n_max,
            value_min=-25,
            value_max=25,
        )

    def _make_number_system(self) -> NumberSystem:
        number_info = self._build_variant()["number_system"]
        return make_number_system(number_info["kind"], number_info["base"])

    def _format_number(self, value: int) -> str:
        return self._make_number_system().encode(value)

    def _format_input_number(self, value: int, leading_zeros: bool = False) -> str:
        number_system = self._make_number_system()
        if leading_zeros:
            return number_system.encode_with_leading_zeros(value)
        return number_system.encode(value)

    def _format_stdin(self, arr: list[int], leading_zeros: bool = False) -> str:
        return self.sep.join(self._format_input_number(value, leading_zeros=leading_zeros) for value in arr) + "\n"

    def _make_random_base_test_array_parts(self, salt: str) -> tuple[list[int], list[int], list[int]]:
        rnd = self.make_random(salt)
        base = self._build_variant()["number_system"]["base"]
        value_limit = max(25, base * 2)

        boundary_values = [0, 123456]
        half_size_max = max(2, (self.n_max - len(boundary_values)) // 2)
        half_size_min = max(2, min(half_size_max, int(self.n_max * 0.1)))

        first_half = rand_int_array(
            rnd,
            size_min=half_size_min,
            size_max=half_size_max,
            value_min=-value_limit,
            value_max=value_limit,
        )

        first_half[0] = base + 5
        first_half[1] = -(base + 5)

        second_half = list(first_half)
        return first_half, second_half, boundary_values

    def _format_random_base_stdin(
        self,
        first_half: list[int],
        second_half: list[int],
        boundary_values: list[int],
    ) -> str:
        tokens = []

        tokens.extend(self._format_input_number(value) for value in first_half)
        tokens.extend(self._format_input_number(value, leading_zeros=True) for value in second_half)
        tokens.extend(self._format_input_number(value, leading_zeros=True) for value in boundary_values)

        return self.sep.join(tokens) + "\n"

    def render_assignment(self) -> str:
        variant = self._build_variant()
        lines = [
            "Концепция варианта ЛР1",
            f"Seed: {variant['seed']}",
            f"Seed hash: {variant['seed_hash']}",
            f"Nmax: {variant['params']['N_max']}",
            f"Кол-во подзадач: {variant['params']['K']}",
        ]

        if variant["number_system"]["random_base"]:
            lines.extend(
                make_number_system(
                    variant["number_system"]["kind"],
                    variant["number_system"]["base"],
                ).render_description()
            )

        lines.extend(
            [
                "   Реализуйте программу, которая должна считать массив целых чисел и",
                "напечатать результаты выполнения назначенных подзадач по одному в строке.",
                "   Назначенные подзадачи:",
            ]
        )

        for index, task_id in enumerate(variant["tasks"], start=1):
            task = TASKS[task_id]
            param_values = ", ".join(
                f"{DISPLAY_NAMES.get(param, param)}={variant['params'][param]}"
                for param in task.params
            )
            lines.append(f"{index}. {task.title} ({param_values})")
            lines.append(f" {task.description}")

        return "\n".join(lines)

    def generate_tests(self) -> list[dict]:
        variant = self._build_variant()
        tests = []

        for test_index in range(1, self.tests_per_task + 1):
            if self.random_base:
                first_half, second_half, boundary_values = self._make_random_base_test_array_parts(
                    f"prog-test-{test_index}"
                )
                arr = first_half + second_half + boundary_values
                stdin = self._format_random_base_stdin(first_half, second_half, boundary_values)
                leading_zeros = True
            else:
                arr = self._make_random_array(f"prog-test-{test_index}")
                stdin = self._format_stdin(arr)
                leading_zeros = False

            expected_lines = []

            for task_id in variant["tasks"]:
                task = TASKS[task_id]
                args = [arr] + [variant["params"][param] for param in task.params]
                expected_lines.append(self._format_number(task.func(*args)))

            tests.append(
                {
                    "input_array": arr,
                    "number_base": variant["number_system"]["base"],
                    "number_format": variant["number_system"]["format"],
                    "leading_zeros_input": leading_zeros,
                    "stdin": stdin,
                    "expected_stdout": "\n".join(expected_lines) + "\n",
                }
            )

        return tests

    def check(self, solution_path: str) -> tuple[bool, str]:
        binary_path, compile_error = self.compile_c_solution(solution_path)
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
                        f"Вход: {test_case['input_array']}\n"
                        f"Ошибка выполнения:\n{runtime_error}"
                    )
                    if self.fail_on_first_test:
                        break
                    continue

                expected = test_case["expected_stdout"]
                actual = obtained or ""

                if actual == expected:
                    passed_tests += 1
                    messages.append(f"Тест {index}: OK")
                    continue

                messages.append(
                    f"Тест {index}: FAIL\n"
                    f"Вход: {test_case['input_array']}\n"
                    f"Ожидалось:\n{test_case['expected_stdout']}"
                    f"Получено:\n{obtained}"
                )
                if self.fail_on_first_test:
                    break
        finally:
            if binary_path.exists():
                binary_path.unlink()
            try:
                binary_path.parent.rmdir()
            except OSError:
                pass

        summary = f"Итог: {passed_tests}/{total_tests} тестов пройдено"
        all_passed = passed_tests == total_tests
        footer = "Все тесты пройдены" if all_passed else "Есть ошибки"
        return all_passed, "\n".join(messages + [summary, footer])