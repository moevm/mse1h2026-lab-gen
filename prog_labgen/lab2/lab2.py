from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from subprocess import TimeoutExpired
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

from prog_labgen.base_module import BaseTask


HEADER_RE = re.compile(r"^###\s*(.*?)\s*###\s*$")
LEGACY_HEADER_RE = re.compile(r"^###\s+(.*?)\s*$")


def parse_student_solution_blob(text: str) -> List[Tuple[str, str]]:
    if not text.strip():
        return []

    result: List[Tuple[str, str]] = []
    current_name: str | None = None
    current_lines: List[str] = []

    for raw_line in text.splitlines():
        header_match = HEADER_RE.match(raw_line)
        legacy_match = LEGACY_HEADER_RE.match(raw_line) if header_match is None else None

        if header_match or legacy_match:
            if current_name is not None:
                result.append((current_name, "\n".join(current_lines)))
            current_name = (header_match or legacy_match).group(1).strip()
            current_lines = []
            continue

        if current_name is not None:
            current_lines.append(raw_line)

    if current_name is not None:
        result.append((current_name, "\n".join(current_lines)))

    return result


def write_solution_to_dir(entries: List[Tuple[str, str]], target_dir: Path) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)

    for name, content in entries:
        clean_name = name.strip()
        if not clean_name:
            continue

        filepath = target_dir / clean_name
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(content, encoding="utf-8", errors="replace")


def check_from_text_blob(
    blob_text: str,
    nmax: int | None = None,
    k: int | None = None,
    Nmax: int | None = None,
    K: int | None = None,
    seed: str = "ab12",
    fail_on_first_test: bool = True,
    keep_temp: bool = False,
) -> None:
    resolved_nmax = 100 if nmax is None and Nmax is None else (nmax if nmax is not None else Nmax)
    resolved_k = 3 if k is None and K is None else (k if k is not None else K)

    entries = parse_student_solution_blob(blob_text)

    if keep_temp:
        debug_dir = Path.cwd() / "debug_student_solution"
        if debug_dir.exists():
            shutil.rmtree(debug_dir)
    else:
        debug_dir = Path(tempfile.mkdtemp(prefix="lab2_check_"))

    debug_dir.mkdir(exist_ok=True, parents=True)
    write_solution_to_dir(entries, debug_dir)

    try:
        task = Lab2Task(
            seed=seed,
            nmax=resolved_nmax,
            k=resolved_k,
            fail_on_first_test=fail_on_first_test,
        )

        ok, msg = task.check(solution_path=str(debug_dir))
        print("OK" if ok else "FAIL")
        print(msg)
    finally:
        if not keep_temp and debug_dir.exists():
            shutil.rmtree(debug_dir)

CORE_TYPES = [
    "reverse_subarray",
    "cyclic_shift",
    "swap_pairs",
    "move_even_to_front",
    "interleave_ends",
]


CORE_TITLES = {
    "reverse_subarray": "Разворот подмассива",
    "cyclic_shift": "Циклический сдвиг массива",
    "swap_pairs": "Перестановка элементов в парах",
    "move_even_to_front": "Перенос чётных элементов в начало",
    "interleave_ends": "Преобразование в порядок «начало-конец»",
}


@dataclass(frozen=True)
class CoreFunctionSpec:
    key: str
    name: str
    params: Dict[str, Any]


@dataclass(frozen=True)
class StepFunctionSpec:
    name: str
    module: str
    calls: Tuple[str, ...]


@dataclass(frozen=True)
class Variant:
    seed: str
    seed_hash: int
    Nmax: int
    K: int
    data_io_module: str
    core_module: str
    main_file: str
    executable: str
    core_functions: Tuple[CoreFunctionSpec, ...]
    steps: Tuple[StepFunctionSpec, ...]


def _suffix(rng, length: int = 3) -> str:
    alphabet = "abcdefghijklmnopqrstuvwxyz0123456789"
    return "".join(rng.choice(alphabet) for _ in range(length))


def _make_core_spec(rng, key: str, nmax: int) -> CoreFunctionSpec:
    func_name = f"cf_{_suffix(rng, 3)}"
    if key == "reverse_subarray":
        upper = max(1, min(nmax, 8))
        a = rng.randint(0, upper - 1)
        b = rng.randint(a, upper - 1)
        params = {"A": a, "B": b}
    elif key == "cyclic_shift":
        direction = rng.choice(["left", "right"])
        t = rng.randint(1, max(1, min(nmax, 7)))
        params = {"direction": direction, "T": t}
    else:
        params = {}
    return CoreFunctionSpec(key=key, name=func_name, params=params)


def _describe_core(spec: CoreFunctionSpec) -> str:
    if spec.key == "reverse_subarray":
        return (
            f"{CORE_TITLES[spec.key]}: функция  {spec.name}  должна разворачивать элементы "
            f"с индексами от A={spec.params['A']} до B={spec.params['B']} включительно."
        )
    if spec.key == "cyclic_shift":
        direction = "влево" if spec.params["direction"] == "left" else "вправо"
        return (
            f"{CORE_TITLES[spec.key]}: функция  {spec.name}  должна циклически сдвигать массив "
            f"{direction} на T={spec.params['T']} позиций."
        )
    if spec.key == "swap_pairs":
        return f"{CORE_TITLES[spec.key]}: функция  {spec.name}  меняет местами элементы в каждой полной паре."
    if spec.key == "move_even_to_front":
        return (
            f"{CORE_TITLES[spec.key]}: функция  {spec.name}  переносит все чётные элементы в начало, "
            "а все нечётные — в конец."
        )
    return (
        f"{CORE_TITLES[spec.key]}: функция  {spec.name}  преобразует массив в порядок "
        " a0, a[n-1], a1, a[n-2], ... ."
    )


def _interleave_order(size: int) -> List[int]:
    order: List[int] = []
    left = 0
    right = size - 1
    while left <= right:
        order.append(left)
        if left != right:
            order.append(right)
        left += 1
        right -= 1
    return order


def _apply_core(arr: List[int], spec: CoreFunctionSpec) -> List[int]:
    result = arr[:]

    if spec.key == "reverse_subarray":
        a = spec.params["A"]
        b = spec.params["B"]
        if 0 <= a <= b < len(result):
            result[a : b + 1] = reversed(result[a : b + 1])
        return result

    if spec.key == "cyclic_shift":
        if not result:
            return result
        t = spec.params["T"] % len(result)
        if t == 0:
            return result
        if spec.params["direction"] == "left":
            return result[t:] + result[:t]
        return result[-t:] + result[:-t]

    if spec.key == "swap_pairs":
        for i in range(0, len(result) - 1, 2):
            result[i], result[i + 1] = result[i + 1], result[i]
        return result

    if spec.key == "move_even_to_front":
        even = [x for x in result if x % 2 == 0]
        odd = [x for x in result if x % 2 != 0]
        return even + odd

    if spec.key == "interleave_ends":
        order = _interleave_order(len(result))
        return [result[index] for index in order]

    raise ValueError(f"Unknown core function: {spec.key}")


def _apply_inverse_deterministic_core(arr: List[int], spec: CoreFunctionSpec) -> List[int]:
    result = arr[:]

    if spec.key == "reverse_subarray":
        return _apply_core(result, spec)

    if spec.key == "cyclic_shift":
        inverse_direction = "right" if spec.params["direction"] == "left" else "left"
        inverse_spec = CoreFunctionSpec(key="cyclic_shift", name=spec.name, params={"direction": inverse_direction, "T": spec.params["T"]})
        return _apply_core(result, inverse_spec)

    if spec.key == "swap_pairs":
        return _apply_core(result, spec)

    if spec.key == "interleave_ends":
        size = len(result)
        order = _interleave_order(size)
        original = [0] * size
        for out_pos, in_pos in enumerate(order):
            original[in_pos] = result[out_pos]
        return original

    raise ValueError(f"Function {spec.key} is not invertible in this checker")


class Lab2Task(BaseTask):
    def __init__(
        self,
        seed: str,
        nmax: int | None = None,
        k: int | None = None,
        Nmax: int | None = None,
        K: int | None = None,
        **kwargs,
    ) -> None:
        resolved_nmax = 100 if nmax is None and Nmax is None else (nmax if nmax is not None else Nmax)
        resolved_k = 3 if k is None and K is None else (k if k is not None else K)

        self._validate_init_args(seed=seed, nmax=resolved_nmax, k=resolved_k)

        super().__init__(seed=seed.strip(), **kwargs)
        self.Nmax = int(resolved_nmax)
        self.K = int(resolved_k)
        self._variant: Variant | None = None

    @staticmethod
    def _validate_init_args(seed: str, nmax: int | None, k: int | None) -> None:
        if not isinstance(seed, str) or not seed.strip():
            raise ValueError("Параметр --seed должен быть непустой строкой.")
        for name, value in (("--n-max", nmax), ("--k", k)):
            if not isinstance(value, int):
                raise ValueError(f"Параметр {name} должен быть целым числом.")
            if value <= 0:
                raise ValueError(f"Параметр {name} должен быть положительным целым числом.")
        if nmax > 100_000:
            raise ValueError("Параметр --n-max слишком большой: допустимо не больше 100000.")
        if k > 50:
            raise ValueError("Параметр --k слишком большой: допустимо не больше 50.")

    def _build_variant(self) -> Variant:
        if self._variant is not None:
            return self._variant

        rng = self.make_random("lab2")
        available_count = min(len(CORE_TYPES), max(3, min(self.K + 1, len(CORE_TYPES))))
        chosen_types = rng.sample(CORE_TYPES, available_count)
        core_specs = tuple(_make_core_spec(rng, key, self.Nmax) for key in chosen_types)

        step_specs: List[StepFunctionSpec] = []
        core_names = [spec.name for spec in core_specs]
        step_calls: List[List[str]] = [[] for _ in range(self.K)]

        for step_index in range(self.K):
            step_calls[step_index].append(rng.choice(core_names))

        used_core_names = {name for calls in step_calls for name in calls}
        missing_core_names = [name for name in core_names if name not in used_core_names]
        rng.shuffle(missing_core_names)
        for core_name in missing_core_names:
            step_calls[rng.randrange(self.K)].append(core_name)

        for calls in step_calls:
            target_len = rng.randint(len(calls), max(len(calls), min(3, len(core_names))))
            while len(calls) < target_len:
                calls.append(rng.choice(core_names))
            rng.shuffle(calls)

        for calls in step_calls:
            module = f"step_{_suffix(rng, 3)}"
            step_name = f"sf_{_suffix(rng, 3)}"
            step_specs.append(StepFunctionSpec(name=step_name, module=module, calls=tuple(calls)))

        self._variant = Variant(
            seed=self.seed,
            seed_hash=self.make_seed_hash("lab2"),
            Nmax=self.Nmax,
            K=self.K,
            data_io_module=f"data_io_{_suffix(rng, 3)}",
            core_module=f"core_{_suffix(rng, 3)}",
            main_file=f"main_{_suffix(rng, 4)}.c",
            executable=f"lab2_{_suffix(rng, 3)}",
            core_functions=core_specs,
            steps=tuple(step_specs),
        )
        return self._variant

    def render_assignment(self) -> str:
        variant = self._build_variant()

        lines = [
            "Вариант 2-й лабораторной",
            f"Seed: {variant.seed}",
            f"Seed hash: {variant.seed_hash}",
            f"Nmax: {variant.Nmax}",
            f"K: {variant.K}",
            "",
            "Напишите многофайловый проект на языке С, разбив решение на модули и собрав его через Makefile.",
            "На вход подаётся массив целых чисел. Размер массива не больше Nmax, числа разделены пробелами, строка заканчивается символом перевода строки.",
            "Программа должна считать массив, последовательно применить к нему все назначенные step-функции и вывести массив после каждого шага.",
            "Каждая core-функция и каждая step-функция работают с массивом на месте, не меняют его длину и имеют интерфейс вида  void func(int arr[], int size) .",
            "",
            "Структура решения:",
            f"- главный файл:  {variant.main_file} ;",
            f"- модуль ввода-вывода:  {variant.data_io_module}.h  и  {variant.data_io_module}.c ;",
            f"- модуль core-функций:  {variant.core_module}.h  и  {variant.core_module}.c ;",
        ]

        for step in variant.steps:
            lines.append(f"- модуль шага:  {step.module}.h  и {step.module}.c .")

        lines.extend([
            f"- итоговый исполняемый файл: {variant.executable};",
            "- обязательный файл сборки: Makefile.",
            "",
            "Назначенные core-функции:",
        ])

        for index, spec in enumerate(variant.core_functions, start=1):
            lines.append(f"{index}. {_describe_core(spec)}")

        lines.append("")
        lines.append("Назначенные step-функции:")
        for index, step in enumerate(variant.steps, start=1):
            call_chain = " -> ".join(step.calls)
            lines.append(
                f"{index}. Функция {step.name} в файлах {step.module}.h/.c должна последовательно вызывать: {call_chain}."
            )

        lines.extend([
            "",
            "Требования к главному файлу:",
            "1. Считать массив через функцию input из модуля data_io.",
            "2. Вызвать step-функции строго в указанном порядке.",
            "3. После каждого шага вывести текущее состояние массива через функцию output из модуля data_io.",
            "",
            "Формат сдачи одним текстом:",
            f"###{variant.main_file}###",
            "...",
            "",
            f"###{variant.data_io_module}.h###",
            "...",
            "",
            f"###{variant.data_io_module}.c###",
            "...",
            "",
            f"###{variant.core_module}.h###",
            "...",
            "",
            f"###{variant.core_module}.c###",
            "...",
            "",
            "###step_xxx.h###",
            "...",
            "",
            "###step_xxx.c###",
            "...",
            "",
            "###Makefile###",
            "...",
        ])

        return "\n".join(lines)

    @staticmethod
    def _format_array(arr: List[int]) -> str:
        return " ".join(map(str, arr))

    @staticmethod
    def _parse_array_line(line: str) -> Tuple[List[int] | None, str | None]:
        stripped = line.strip()
        if not stripped:
            return [], None
        try:
            return [int(token) for token in stripped.split()], None
        except ValueError:
            return None, f"Строка вывода содержит нецелое значение: {line!r}"

    def _apply_step_canonical(self, arr: List[int], step: StepFunctionSpec, core_map: Dict[str, CoreFunctionSpec]) -> List[int]:
        result = arr[:]
        for core_name in step.calls:
            result = _apply_core(result, core_map[core_name])
        return result

    def _validate_step_output(
        self,
        before: List[int],
        after: List[int],
        step: StepFunctionSpec,
        core_map: Dict[str, CoreFunctionSpec],
    ) -> bool:
        calls = [core_map[name] for name in step.calls]
        last_even_index = -1
        for idx, spec in enumerate(calls):
            if spec.key == "move_even_to_front":
                last_even_index = idx

        if last_even_index == -1:
            expected = self._apply_step_canonical(before, step, core_map)
            return after == expected

        candidate = after[:]
        suffix = calls[last_even_index + 1 :]
        for spec in reversed(suffix):
            candidate = _apply_inverse_deterministic_core(candidate, spec)

        even_count = sum(1 for value in before if value % 2 == 0)
        prefix_ok = all(value % 2 == 0 for value in candidate[:even_count])
        suffix_ok = all(value % 2 != 0 for value in candidate[even_count:])
        multiset_ok = Counter(candidate) == Counter(before)

        return prefix_ok and suffix_ok and multiset_ok

    def _simulate_pipeline(self, arr: List[int]) -> List[str]:
        variant = self._build_variant()
        core_map = {spec.name: spec for spec in variant.core_functions}
        current = arr[:]
        outputs: List[str] = []
        for step in variant.steps:
            current = self._apply_step_canonical(current, step, core_map)
            outputs.append(self._format_array(current))
        return outputs

    def generate_tests(self) -> List[Dict[str, Any]]:
        variant = self._build_variant()
        tests: List[Dict[str, Any]] = []

        fixed_inputs = [
            [1, 2, 3, 4, 5, 6],
            [10, 20, 30, 40],
            [1, 1, 1, 1],
            [1, 2, 3],
            [],
        ]

        for index, arr in enumerate(fixed_inputs, start=1):
            inp = arr[: variant.Nmax]
            expected_lines = self._simulate_pipeline(inp)
            tests.append(
                {
                    "id": f"fixed_{index}",
                    "stdin": self._format_array(inp) + "\n" if inp else "\n",
                    "expected_stdout": "\n".join(expected_lines) + "\n",
                }
            )

        rng = self.make_random("lab2_tests")
        while len(tests) < 10:
            size = rng.randint(0, min(12, variant.Nmax))
            inp = [rng.randint(-20, 20) for _ in range(size)]
            expected_lines = self._simulate_pipeline(inp)
            tests.append(
                {
                    "id": f"random_{len(tests)}",
                    "stdin": self._format_array(inp) + "\n" if inp else "\n",
                    "expected_stdout": "\n".join(expected_lines) + "\n",
                }
            )

        return tests

    def _format_test_fail_message(
        self,
        test_index: int,
        test_id: str,
        stdin_text: str,
        expected_text: str,
        actual_text: str | None = None,
        runtime_error: str | None = None,
    ) -> str:
        parts = [f"Тест {test_index} ({test_id}): FAIL", f"Вход:\n{stdin_text}"]
        parts.append(f"Ожидалось:\n{expected_text}")
        if actual_text is not None:
            parts.append(f"Получено:\n{actual_text}")
        if runtime_error:
            parts.append(f"Ошибка выполнения:\n{runtime_error}")
        return "\n".join(parts)

    def check(self, solution_path: str) -> tuple[bool, str]:
        variant = self._build_variant()
        build_dir = Path(solution_path)
        if not build_dir.exists():
            return False, f"Каталог с решением не найден: {solution_path}"
        if not build_dir.is_dir():
            return False, f"Путь к решению должен быть каталогом с Makefile: {solution_path}"
        if not (build_dir / "Makefile").exists():
            return False, f"В каталоге решения не найден обязательный файл Makefile: {build_dir}"

        core_map = {spec.name: spec for spec in variant.core_functions}

        env = os.environ.copy()
        if self.compiler:
            env["CC"] = self.compiler

        try:
            make_result = subprocess.run(
                ["make", "-C", str(build_dir), variant.executable],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                env=env,
                timeout=20,
            )
        except FileNotFoundError:
            return False, "Команда make не найдена. Установите make или проверьте PATH."
        except TimeoutExpired:
            return False, "Сборка через Makefile превысила лимит времени."
        if make_result.returncode != 0:
            error_text = (make_result.stderr + make_result.stdout).strip()
            return False, f"Ошибка сборки через Makefile:\n{error_text}"

        binary_path = build_dir / variant.executable
        if not binary_path.exists():
            return False, f"Makefile не создал исполняемый файл {variant.executable}."

        total = 0
        passed = 0
        messages: List[str] = []

        try:
            for test_index, test in enumerate(self.generate_tests(), start=1):
                total += 1
                try:
                    proc = subprocess.run(
                        [str(binary_path)],
                        input=test["stdin"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        timeout=5,
                    )
                except TimeoutExpired:
                    messages.append(
                        self._format_test_fail_message(
                            test_index=test_index,
                            test_id=test["id"],
                            stdin_text=test["stdin"],
                            expected_text=test["expected_stdout"],
                            runtime_error="Программа превысила лимит времени выполнения.",
                        )
                    )
                    if self.fail_on_first_test:
                        break
                    continue

                if proc.returncode != 0:
                    runtime_error = proc.stderr.strip() or "Программа завершилась с ненулевым кодом без сообщения об ошибке."
                    messages.append(
                        self._format_test_fail_message(
                            test_index=test_index,
                            test_id=test["id"],
                            stdin_text=test["stdin"],
                            expected_text=test["expected_stdout"],
                            actual_text=(proc.stdout or "").replace("\r\n", "\n").replace("\r", "\n"),
                            runtime_error=runtime_error,
                        )
                    )
                    if self.fail_on_first_test:
                        break
                    continue

                actual_text = (proc.stdout or "").replace("\r\n", "\n").replace("\r", "\n")
                actual_lines = actual_text.splitlines()

                input_arr, parse_error = self._parse_array_line(test["stdin"])
                if parse_error is not None or input_arr is None:
                    raise RuntimeError(f"Некорректно сформирован тест: {parse_error}")

                if len(actual_lines) != variant.K:
                    messages.append(
                        self._format_test_fail_message(
                            test_index=test_index,
                            test_id=test["id"],
                            stdin_text=test["stdin"],
                            expected_text=test["expected_stdout"],
                            actual_text=actual_text,
                        )
                    )
                    if self.fail_on_first_test:
                        break
                    continue

                current = input_arr
                ok = True
                for step, line in zip(variant.steps, actual_lines):
                    parsed_line, line_error = self._parse_array_line(line)
                    if line_error is not None or parsed_line is None:
                        ok = False
                        break
                    valid = self._validate_step_output(current, parsed_line, step, core_map)
                    if not valid:
                        ok = False
                        break
                    current = parsed_line

                if ok:
                    passed += 1
                    messages.append(f"Тест {test_index} ({test['id']}): OK")
                else:
                    messages.append(
                        self._format_test_fail_message(
                            test_index=test_index,
                            test_id=test["id"],
                            stdin_text=test["stdin"],
                            expected_text=test["expected_stdout"],
                            actual_text=actual_text,
                        )
                    )
                    if self.fail_on_first_test:
                        break
        finally:
            try:
                subprocess.run(
                    ["make", "-C", str(build_dir), "clean"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False,
                    env=env,
                    timeout=10,
                )
            except (FileNotFoundError, TimeoutExpired):
                pass

        ok = passed == total
        summary = f"Итог: {passed}/{total} тестов пройдено"
        footer = "Все тесты пройдены!" if ok else "Есть ошибки"
        return ok, "\n".join(messages + [summary, footer])
