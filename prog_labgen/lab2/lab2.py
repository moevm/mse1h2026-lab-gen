from __future__ import annotations
import shutil
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass


from prog_labgen.base_module import BaseTask, add_common_cli_args, get_common_cli_args
from prog_labgen.base_module import CLIParser


CORE_FUNCTIONS = [
    "palindrome_check",
    "interleave_ends",
    "reverse_segment",
    "shift_left",
    "swap_pairs",
    "even_odd_reorder",
]


@dataclass(frozen=True)
class Variant:
    student: str
    seed_hash: int
    Nmax: int
    K: int
    core_functions: List[Dict[str, Any]]
    main_stub: str


def _generate_core_params(rng, core, Nmax, K, main_stub) -> Dict[str, Any]:
    if core == "palindrome_check":
        return {
            "name": "is_palindrome",
            "module": f"task_{main_stub}{hex(rng.randint(10**8, 10**9 - 1))[2:][:4]}",
            "params": {},
        }
    elif core == "reverse_segment":
        A = rng.randint(0, Nmax - 1)
        B = rng.randint(0, Nmax - 1)
        if A > B:
            A, B = B, A
        return {
            "name": "reverse_segment",
            "module": f"task_{main_stub}{hex(rng.randint(10**8, 10**9 - 1))[2:][:4]}",
            "params": {"A": A, "B": B},
        }
    elif core == "shift_left":
        T = rng.randint(1, 10)
        return {
            "name": "shift_left",
            "module": f"task_{main_stub}{hex(rng.randint(10**8, 10**9 - 1))[2:][:4]}",
            "params": {"T": T},
        }
    else:
        return {
            "name": core.replace("_", ""),
            "module": f"task_{main_stub}{hex(rng.randint(10**8, 10**9 - 1))[2:][:4]}",
            "params": {},
        }


class Lab2Task(BaseTask):
    def __init__(
        self,
        student: str,
        Nmax: int = 100,
        K: int = 3,
        **kwargs,
    ) -> None:
        super().__init__(student=student, **kwargs)
        self.Nmax = Nmax
        self.K = K
        self._variant: Variant | None = None


    def _build_variant(self) -> Variant:
        if self._variant:
            return self._variant


        rng = self.make_random("lab2")
        chosen = rng.sample(CORE_FUNCTIONS, min(self.K, len(CORE_FUNCTIONS)))
        core_data = [
            _generate_core_params(rng, core, self.Nmax, self.K, self.student)
            for core in chosen
        ]
        self._variant = Variant(
            student=self.student,
            seed_hash=self.make_seed_hash("lab2"),
            Nmax=self.Nmax,
            K=self.K,
            core_functions=core_data,
            main_stub=self.student,
        )
        return self._variant


    def render_assignment(self) -> str:
        v = self._build_variant()
        lines = [
            "Концепция варианта 2‑й лабораторной",
            f"Студент: {v.student}",
            f"Seed hash: {v.seed_hash}",
            f"N_max: {v.Nmax}",
            f"K: {v.K}",
            "Напишите многофайловый проект на языке С, выделив каждую подзадачу в отдельный модуль.",
            "На вход подаётся массив целых чисел. Размер массива не больше N_max, числа разделены пробелами, строка заканчивается символом перевода строки.",
            "Программа должна последовательно вычислить все K подзадач и вывести результаты в заданном порядке, каждый результат с новой строки.",
            "Для каждой подзадачи должны быть созданы: отдельный .c файл и отдельный .h файл.",
            "Главный файл должен подключать все необходимые заголовочные файлы и вызывать все назначенные функции.",
            "Проект должен собираться через Makefile. Ошибкой считается дублирование кода.",
            "Core‑функции для данного варианта:",
        ]
        for core in v.core_functions:
            params = " ".join(f"{k}={v}" for k, v in core['params'].items()) if core['params'] else "(без параметров)"
            lines.append(f"  - {core['name']} (модуль: {core['module']}, параметры: {params})")
        return "\n".join(lines)


    def _simulate_step(self, arr: List[int], v: Variant, step_idx: int) -> Tuple[List[int], str | None]:
        result_arr = arr[:]
        output = None

        for core in v.core_functions:
            name = core["name"]
            params = core["params"]

            if name == "reverse_segment":
                A = params.get("A", 0)
                B = params.get("B", len(result_arr) - 1)
                if 0 <= A < len(result_arr) and 0 <= B < len(result_arr) and A < B:
                    result_arr = result_arr[:A] + result_arr[A:B+1][::-1] + result_arr[B+1:]

            elif name == "shift_left":
                T = params.get("T", 1)
                if len(result_arr) > 0:
                    T %= len(result_arr)
                    result_arr = result_arr[T:] + result_arr[:T]

            elif name == "even_odd_reorder":
                even = [x for x in result_arr if x % 2 == 0]
                odd = [x for x in result_arr if x % 2 != 0]
                result_arr = even + odd

            elif name == "swap_pairs":
                new_arr = []
                for i in range(0, len(result_arr), 2):
                    if i + 1 < len(result_arr):
                        new_arr.append(result_arr[i + 1])
                        new_arr.append(result_arr[i])
                    else:
                        new_arr.append(result_arr[i])
                result_arr = new_arr

            elif name == "is_palindrome":
                if step_idx == 1:
                    left = 0
                    right = len(result_arr) - 1
                    is_pal = True
                    while left < right:
                        if result_arr[left] != result_arr[right]:
                            is_pal = False
                            break
                        left += 1
                        right -= 1
                    output = "YES" if is_pal else "NO"

        return result_arr, output


    def _format_array(self, arr: List[int]) -> str:
        return " ".join(map(str, arr)) if arr else "EMPTY"


    def generate_tests(self) -> List[Dict[str, Any]]:
        v = self._build_variant()
        tests = []

        fixed_inputs = [
            [1, 2, 3, 4, 5, 6],
            [10, 20, 30, 40],
            [1, 1, 1, 1],
            [1, 2, 3],
            [],
        ]

        for idx, inp in enumerate(fixed_inputs, start=1):
            if len(inp) > v.Nmax:
                inp = inp[:v.Nmax]
            arr = inp[:]

            step_results = []
            for step in range(v.K):
                result_arr, output = self._simulate_step(arr, v, step)
                if output is not None:
                    step_results.append(output)
                else:
                    step_results.append(self._format_array(result_arr))
                arr = result_arr

            expected = "\n".join(step_results) + "\n"

            tests.append({
                "id": f"fixed_{idx}",
                "stdin": " ".join(map(str, inp)) + "\n",
                "expected_stdout": expected,
            })

        rng = self.make_random("tests")
        while len(tests) < 10:
            size = rng.randint(0, min(v.Nmax, 20))
            inp = [rng.randint(-100, 100) for _ in range(size)]
            arr = inp[:]

            step_results = []
            for step in range(v.K):
                result_arr, output = self._simulate_step(arr, v, step)
                if output is not None:
                    step_results.append(output)
                else:
                    step_results.append(self._format_array(result_arr))
                arr = result_arr

            expected = "\n".join(step_results) + "\n"

            tests.append({
                "id": f"random_{len(tests)}",
                "stdin": " ".join(map(str, inp)) + "\n",
                "expected_stdout": expected,
            })

        return tests


    def check(self, solution_path: str) -> tuple[bool, str]:
        v = self._build_variant()
        build_dir = Path(solution_path)

        make_result = subprocess.run(
            ["make", "-C", build_dir, "lab2_solution"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        if make_result.returncode != 0:
            error_text = (make_result.stderr + make_result.stdout).strip()
            return False, f"Ошибка сборки через Makefile:\n{error_text}"

        binary_path = build_dir / "lab2_solution"
        if not binary_path.exists():
            return False, "Makefile не создал исполняемый файл lab2_solution."

        total = 0
        passed = 0
        messages = []

        try:
            for idx, test in enumerate(self.generate_tests(), start=1):
                total += 1
                obtained, runtime_error = self.run_binary(binary_path, test["stdin"])
                if runtime_error:
                    messages.append(
                        f"Тест {idx} ({test['id']}): FAIL\n"
                        f"Вход:\n{test['stdin']}\n"
                        f"Ошибка выполнения:\n{runtime_error}"
                    )
                    if self.fail_on_first_test:
                        break
                    continue

                expected = test["expected_stdout"]
                actual = (obtained or "").replace("\r\n", "\n").replace("\r", "\n")
                expected = expected.replace("\r\n", "\n").replace("\r", "\n")
                if actual == expected:
                    passed += 1
                    messages.append(f"Тест {idx} ({test['id']}): OK")
                else:
                    lines = [
                        f"Тест {idx} ({test['id']}): FAIL",
                        f"Вход:",
                        test["stdin"],
                        "Ожидалось:",
                        expected,
                        "Получено:",
                        actual,
                    ]
                    messages.append("\n".join(lines))
                    if self.fail_on_first_test:
                        break
        finally:
            if binary_path and binary_path.exists():
                binary_path.unlink()

        ok = passed == total
        summary = f"Итог: {passed}/{total} тестов пройдено"
        footer = "Все тесты пройдены!" if ok else "Есть ошибки"
        return ok, "\n".join(messages + [summary, footer])