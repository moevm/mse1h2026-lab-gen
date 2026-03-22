from __future__ import annotations
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
    test_size: int


def _generate_core_params(rng, core, arr_size, K, main_stub) -> Dict[str, Any]:
    if core == "palindrome_check":
        return {
            "name": "is_palindrome",
            "module": f"task_{main_stub}{hex(rng.randint(10**8, 10**9 - 1))[2:][:4]}",
            "params": {},
        }
    elif core == "reverse_segment":
        if arr_size > 0:
            A = rng.randint(0, arr_size - 1)
            B = rng.randint(A, arr_size - 1)
        else:
            A = B = 0
        return {
            "name": "reverse_segment",
            "module": f"task_{main_stub}{hex(rng.randint(10**8, 10**9 - 1))[2:][:4]}",
            "params": {"A": A, "B": B},
        }
    elif core == "shift_left":
        T = rng.randint(1, max(1, arr_size)) if arr_size > 0 else 1
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
        
        test_size = rng.randint(1, self.Nmax)
        
        chosen = rng.sample(CORE_FUNCTIONS, min(self.K, len(CORE_FUNCTIONS)))
        core_data = [
            _generate_core_params(rng, core, test_size, self.K, self.student)
            for core in chosen
        ]
        self._variant = Variant(
            student=self.student,
            seed_hash=self.make_seed_hash("lab2"),
            Nmax=self.Nmax,
            K=self.K,
            core_functions=core_data,
            main_stub=self.student,
            test_size=test_size,
        )
        return self._variant


    def render_assignment(self) -> str:
        v = self._build_variant()
        lines = [
            "Концепция варианта 2‑й лабораторной",
            f"Студент: {v.student}",
            f"Seed hash: {v.seed_hash}",
            f"Nmax: {v.Nmax}",
            f"K: {v.K}",
            "Напишите многофайловый проект на языке Си, выделив каждую подзадачу в отдельный модуль.",
            "На вход подаётся массив целых чисел. Размер массива не больше Nmax, числа разделены пробелами, строка заканчивается символом перевода строки.",
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


    def _simulate_step(self, arr: List[int], core: Dict[str, Any]) -> Tuple[List[str], List[int]]:
        arr = arr[:]
        outputs = []

        name = core["name"]
        params = core.get("params", {})

        if name == "reverse_segment":
            A = params.get("A", 0)
            B = params.get("B", len(arr) - 1)
            if 0 <= A < len(arr) and 0 <= B < len(arr) and A <= B:
                result = arr[:]
                result[A:B+1] = result[A:B+1][::-1]
                arr = result
            outputs.append(" ".join(map(str, arr)) if arr else "")

        elif name == "shift_left":
            T = params.get("T", 1)
            if len(arr) > 0:
                T = T % len(arr)
                arr = arr[T:] + arr[:T]
            outputs.append(" ".join(map(str, arr)) if arr else "")

        elif name == "even_odd_reorder":
            even = [x for x in arr if x % 2 == 0]
            odd = [x for x in arr if x % 2 != 0]
            arr = even + odd
            outputs.append(" ".join(map(str, arr)) if arr else "")

        elif name == "palindrome_check" or name == "is_palindrome":
            if len(arr) <= 1:
                is_pal = True
            else:
                left = 0
                right = len(arr) - 1
                is_pal = True
                while left < right:
                    if arr[left] != arr[right]:
                        is_pal = False
                        break
                    left += 1
                    right -= 1
            outputs.append("YES" if is_pal else "NO")

        elif name == "swap_pairs" or name == "swappairs":
            new_arr = []
            for i in range(0, len(arr), 2):
                if i + 1 < len(arr):
                    new_arr.append(arr[i + 1])
                    new_arr.append(arr[i])
                else:
                    new_arr.append(arr[i])
            arr = new_arr
            outputs.append(" ".join(map(str, arr)) if arr else "")

        return outputs, arr


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

            step_outputs = []
            for core in v.core_functions:
                outputs, arr = self._simulate_step(arr, core)
                step_outputs.extend(outputs)

            expected = "\n".join(step_outputs) + "\n" if step_outputs else "\n"

            tests.append({
                "id": f"fixed_{idx}",
                "stdin": " ".join(map(str, inp)) + "\n",
                "expected_stdout": expected,
            })

        rng = self.make_random("tests")
        while len(tests) < 10:
            size = v.test_size
            inp = [rng.randint(-100, 100) for _ in range(size)]
            arr = inp[:]

            step_outputs = []
            for core in v.core_functions:
                outputs, arr = self._simulate_step(arr, core)
                step_outputs.extend(outputs)

            expected = "\n".join(step_outputs) + "\n" if step_outputs else "\n"

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

                proc = subprocess.run(
                    [str(binary_path)],
                    input=test["stdin"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )

                if proc.returncode != 0:
                    stderr = proc.stderr or ""
                    if stderr.strip():
                        runtime_error = stderr
                    else:
                        runtime_error = "Программа завершилась с ненулевым кодом и пустым stderr."
                    messages.append(
                        f"Тест {idx} ({test['id']}): FAIL\n"
                        f"Вход:\n{test['stdin']}\n"
                        f"Ошибка выполнения:\n{runtime_error}"
                    )
                    if self.fail_on_first_test:
                        break
                    continue

                obtained = proc.stdout or ""

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