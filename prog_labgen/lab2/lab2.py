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

FUNCTION_DESCRIPTIONS = {
    "is_palindrome": {
        "description": "Проверить, является ли массив палиндромом",
        "output": "YES / NO",
        "example": "1 2 3 2 1 -> YES, 1 2 3 -> NO"
    },
    "palindrome_check": {
        "description": "Проверить, является ли массив палиндромом",
        "output": "YES / NO",
        "example": "1 2 3 2 1 -> YES, 1 2 3 -> NO"
    },
    "interleave_ends": {
        "description": "Вывести элементы, чередуя начало и конец массива",
        "output": "массив",
        "example": "1 2 3 4 5 6 -> 1 6 2 5 3 4"
    },
    "reverse_segment": {
        "description": "Развернуть подмассив с индексами от A до B",
        "output": "массив",
        "example": "A=2, B=4: 1 2 3 4 5 -> 1 2 5 4 3"
    },
    "shift_left": {
        "description": "Циклически сдвинуть массив влево на T позиций",
        "output": "массив",
        "example": "T=2: 1 2 3 4 5 -> 3 4 5 1 2"
    },
    "swap_pairs": {
        "description": "Разбить массив на пары и поменять элементы в каждой паре местами",
        "output": "массив",
        "example": "1 2 3 4 5 6 -> 2 1 4 3 6 5"
    },
    "swappairs": {
        "description": "Разбить массив на пары и поменять элементы в каждой паре местами",
        "output": "массив",
        "example": "1 2 3 4 5 6 -> 2 1 4 3 6 5"
    },
    "even_odd_reorder": {
        "description": "Перенести все чётные элементы в начало, нечётные - в конец",
        "output": "массив",
        "example": "1 2 3 4 5 6 -> 2 4 6 1 3 5"
    },
}


def _get_function_description(core_name: str, params: Dict[str, Any]) -> str:
    base = FUNCTION_DESCRIPTIONS.get(core_name, {})
    description = base.get("description", core_name)
    example = base.get("example", "")
    
    if core_name == "reverse_segment":
        A = params.get("A", 0)
        B = params.get("B", 0)
        example_arr = [1, 2, 3, 4, 5, 6, 7, 8]
        if 0 <= A < len(example_arr) and 0 <= B < len(example_arr) and A <= B:
            result = example_arr[:A] + example_arr[A:B+1][::-1] + example_arr[B+1:]
            result_str = " ".join(map(str, result))
            example = f"A={A}, B={B}: 1 2 3 4 5 6 7 8 -> {result_str}"
        else:
            example = f"A={A}, B={B} (применимо только к массивам соответствующего размера)"
        return f"{description} ({example})"
    
    elif core_name == "shift_left":
        T = params.get("T", 1)
        example_arr = [1, 2, 3, 4, 5]
        T_eff = T % len(example_arr)
        result = example_arr[T_eff:] + example_arr[:T_eff]
        result_str = " ".join(map(str, result))
        return f"{description} (T={T}). Пример: 1 2 3 4 5 -> {result_str}"
    
    else:
        return f"{description}. Пример: {example}" 

@dataclass(frozen=True)
class Variant:
    student: str
    seed_hash: int
    Nmax: int
    K: int
    sep: str
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
        sep: str = " ",
        **kwargs,
    ) -> None:
        super().__init__(student=student, **kwargs)
        self.Nmax = Nmax
        self.K = K
        self.sep = sep
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
            sep=self.sep,
            core_functions=core_data,
            main_stub=self.student,
            test_size=test_size,
        )
        return self._variant


    def render_assignment(self) -> str:
        v = self._build_variant()
        lines = [
            "Вариант 2-й лабораторной",
            f"Студент: {v.student}",
            f"Seed hash: {v.seed_hash}",
            f"Nmax: {v.Nmax}",
            f"K: {v.K}",
            f"SEP: '{v.sep}'",
            "",
            "Напишите многофайловый проект на языке С, выделив каждую подзадачу в отдельный модуль.",
            f"На вход подаётся массив целых чисел. Размер массива не больше Nmax, числа разделены разделителем '{v.sep}', строка заканчивается символом перевода строки.",
            "Программа должна последовательно вычислить все K подзадач и вывести результаты в заданном порядке, каждый результат с новой строки.",
            "Для каждой подзадачи должны быть созданы: отдельный .c файл и отдельный .h файл.",
            "Главный файл должен подключать все необходимые заголовочные файлы и вызывать все назначенные функции.",
            "Проект должен собираться через Makefile. Ошибкой считается дублирование кода.",
            "",
            "=" * 60,
            "Core-функции для данного варианта:",
            "=" * 60,
        ]
        
        for idx, core in enumerate(v.core_functions, start=1):
            name = core["name"]
            params = core.get("params", {})
            
            desc = _get_function_description(name, params)
            
            lines.append(f"\n{idx}. {name}")
            lines.append(f"   {desc}")
        
        lines.append("\n" + "=" * 60)
        lines.append("Требования к реализации:")
        lines.append("=" * 60)
        lines.append("1. Каждая функция должна быть реализована в отдельной паре .c/.h файлов.")
        lines.append("2. Makefile должен собирать проект в исполняемый файл lab2_solution.")
        lines.append("3. Запрещено дублирование кода.")
        lines.append("4. Решение должно быть оформлено в виде текстового блока с разделителями ###filename")
        
        return "\n".join(lines)


    def _format_array(self, arr: List[int]) -> str:
        if not arr:
            return ""
        return self.sep.join(map(str, arr))


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
            outputs.append(self._format_array(arr))

        elif name == "shift_left":
            T = params.get("T", 1)
            if len(arr) > 0:
                T = T % len(arr)
                arr = arr[T:] + arr[:T]
            outputs.append(self._format_array(arr))

        elif name == "even_odd_reorder":
            even = [x for x in arr if x % 2 == 0]
            odd = [x for x in arr if x % 2 != 0]
            arr = even + odd
            outputs.append(self._format_array(arr))

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
            outputs.append(self._format_array(arr))

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
                "stdin": self.sep.join(map(str, inp)) + "\n",
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
                "stdin": self.sep.join(map(str, inp)) + "\n",
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