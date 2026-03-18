from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from prog_labgen.base_module import BaseTask


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
    1: TaskSpec("Первый элемент, кратный M", ("M",), "Выведите индекс первого элемента массива, который делится на M без остатка. Если такого элемента нет, выведите -1.", first_multiple_index),
    2: TaskSpec("Последний элемент по модулю больше T", ("T",), "Выведите индекс последнего элемента массива, для которого |a[i]| > T. Если такого элемента нет, выведите -1.", last_abs_gt_index),
    3: TaskSpec("Количество элементов в диапазоне [A; B]", ("A", "B"), "Выведите количество элементов массива, удовлетворяющих A <= a[i] <= B.", count_in_range),
    4: TaskSpec("Сумма модулей на позициях с шагом K, начиная с P", ("P", "K_step"), "Посчитайте сумму |a[i]| по индексам P, P+K, P+2K, ... пока индекс меньше длины массива.", sum_abs_step),
    5: TaskSpec("Сумма элементов, делящихся на D", ("D",), "Посчитайте сумму всех элементов массива, которые делятся на D без остатка. Если таких элементов нет, выведите 0.", sum_divisible),
    6: TaskSpec("Количество элементов, которые по модулю меньше L", ("L",), "Посчитайте количество элементов массива, для которых |a[i]| < L.", count_abs_lt),
}


class Lab1Task(BaseTask):
    def __init__(
        self,
        student: str,
        n_max: int = 100,
        sep: str = " ",
        k: int = 3,
        tests_per_task: int = 5,
        fail_on_first_test: bool = True,
        compiler: str | None = None,
    ) -> None:
        super().__init__(student=student, fail_on_first_test=fail_on_first_test, compiler=compiler)
        self.n_max = n_max
        self.sep = sep
        self.k = k
        self.tests_per_task = tests_per_task
        self._variant: dict | None = None

    def _build_variant(self) -> dict:
        if self._variant is not None:
            return self._variant

        rnd = self.make_random()
        selected_tasks = rnd.sample(sorted(TASKS.keys()), self.k)
        params = {"N_max": self.n_max, "K": self.k}

        for task_id in selected_tasks:
            for param_name in TASKS[task_id].params:
                if param_name in {"M", "D", "L", "T", "P"}:
                    params[param_name] = rnd.randint(2, 12)
                elif param_name == "A":
                    params[param_name] = rnd.randint(0, int(self.n_max * 0.2))
                elif param_name == "B":
                    params[param_name] = rnd.randint(int(self.n_max * 0.8), self.n_max)
                elif param_name == "K_step":
                    params[param_name] = rnd.randint(1, 5)

        self._variant = {
            "student": self.student,
            "seed_hash": self.make_seed_hash(),
            "tasks": selected_tasks,
            "params": params,
        }
        return self._variant

    def _make_random_array(self, salt: str) -> list[int]:
        rnd = self.make_random(salt)
        size = rnd.randint(max(1, int(self.n_max * 0.1)), self.n_max)
        return [rnd.randint(-25, 25) for _ in range(size)]

    def _format_stdin(self, arr: list[int]) -> str:
        return self.sep.join(str(value) for value in arr) + "\n"

    def render_assignment(self) -> str:
        variant = self._build_variant()
        lines = [
            "Концепция варианта ЛР1",
            f"Студент: {variant['student']}",
            f"Seed hash: {variant['seed_hash']}",
            f"Nmax: {variant['params']['N_max']}",
            f"K: {variant['params']['K']}",
            "Программа должна читать массив целых чисел из stdin и печатать результаты всех назначенных подзадач по одному в строке.",
            "Назначенные подзадачи:",
        ]

        for index, task_id in enumerate(variant["tasks"], start=1):
            task = TASKS[task_id]
            param_values = ", ".join(
                f"{param}={variant['params'][param]}" for param in task.params
            )
            lines.append(f"{index}. {task.title} | {param_values}")
            lines.append(f"   {task.description}")

        return "\n".join(lines)

    def generate_tests(self) -> list[dict]:
        variant = self._build_variant()
        tests = []

        for test_index in range(1, self.tests_per_task + 1):
            arr = self._make_random_array(f"prog-test-{test_index}")
            expected_lines = []

            for task_id in variant["tasks"]:
                task = TASKS[task_id]
                args = [arr] + [variant["params"][param] for param in task.params]
                expected_lines.append(str(task.func(*args)))

            tests.append(
                {
                    "input_array": arr,
                    "stdin": self._format_stdin(arr),
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
