from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable

from prog_labgen.base_module import BaseTask, rand_choice, rand_int, rand_sample


LEVELS = ("INFO", "DEBUG", "WARN", "ERROR", "CRITICAL")
SERVICES = ("auth-service", "DB_CORE", "api.gateway", "cache", "PAYMENT", "user_handler", "mail-service")
WORDS = ("timeout", "failed", "denied", "exception", "started", "finished", "connection", "request", "user", "worker")
REQUIRED_REGEX_MARKERS = ("#include <regex.h>", "regcomp(", "regexec(")


@dataclass(frozen=True)
class Variant:
    seed: str
    seed_hash: int
    task_key: str
    params: dict[str, Any]
    filters: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class ParsedRecord:
    text: str
    data: dict[str, Any]


TASK_TITLES = {
    "terminal": "Логи терминала",
    "url": "URL-ссылки",
    "ip": "IP-адреса",
    "finance": "Финансовые данные",
    "server": "Серверные логи",
    "apache": "Логи Apache",
}


class Lab5Task(BaseTask):
    def __init__(
        self,
        seed: str,
        tests_count: int = 10,
        records_per_test: int = 14,
        filters_count: int = 2,
        fail_on_first_test: bool = True,
        compiler: str | None = None,
    ) -> None:
        super().__init__(seed=seed, fail_on_first_test=fail_on_first_test, compiler=compiler)
        self.tests_count = max(1, tests_count)
        self.records_per_test = max(3, records_per_test)
        self.filters_count = max(1, filters_count)
        self._variant: Variant | None = None

    def _build_variant(self) -> Variant:
        if self._variant is not None:
            return self._variant

        rng = self.make_random()
        task_key = rand_choice(rng, tuple(TASK_TITLES.keys()))
        params = _generate_params(task_key, rng)
        filters = tuple(_generate_filters(task_key, params, rng, self.filters_count))
        self._variant = Variant(
            seed=self.seed,
            seed_hash=self.make_seed_hash(),
            task_key=task_key,
            params=params,
            filters=filters,
        )
        return self._variant

    def render_assignment(self) -> str:
        v = self._build_variant()
        lines = [
            "Лабораторная работа 5",
            f"Seed: {v.seed}",
            f"Seed hash: {v.seed_hash}",
            f"Задача: {TASK_TITLES[v.task_key]}",
            "",
            "На вход программе подаётся текст - набор строк. Ввод заканчивается строкой Fin.",
            "В тексте могут встречаться корректные структуры выбранного типа, произвольные строки и повреждённые записи.",
            "Гарантируется, что каждая корректная структура полностью располагается в пределах одной строки.",
            "Нужно использовать регулярные выражения. Разрешается использовать несколько регулярных выражений.",
            "",
            "Обработка выполняется в два этапа:",
            "1. Найти все структуры, удовлетворяющие формату и параметрам этапа 1.",
            "2. Отфильтровать найденные структуры по условиям этапа 2.",
            "",
            "Формат вывода:",
            "- на первой строке вывести количество структур, прошедших этап 1;",
            "- далее вывести все структуры, прошедшие этап 2, по одной в строке, в порядке появления во входных данных;",
            "- если после этапа 2 подходящих структур нет, вывести Empty;",
            "- если на этапе 1 корректных структур нет, вывести две строки: 0 и Empty.",
            "",
            "Формат структуры:",
            *_describe_format(v.task_key),
            "",
            "Параметры этапа 1:",
            *_describe_params(v.task_key, v.params),
            "",
            "Условия фильтрации этапа 2:",
            *[f"- {_describe_filter(v.task_key, flt)}" for flt in v.filters],
        ]
        return "\n".join(lines)

    def generate_tests(self) -> list[dict[str, Any]]:
        variant = self._build_variant()
        tests: list[dict[str, Any]] = []

        for index in range(1, self.tests_count + 1):
            rng = self.make_random(f"lab5-test-{index}")
            lines = _generate_input_lines(variant, rng, self.records_per_test)
            stdin_data = "\n".join(lines + ["Fin."]) + "\n"
            expected = solve(stdin_data, variant) + "\n"
            tests.append({"input_text": stdin_data, "stdin": stdin_data, "expected_stdout": expected})
        return tests

    def check(self, solution_path: str) -> tuple[bool, str]:
        regex_error = _validate_regex_usage(solution_path)
        if regex_error is not None:
            return False, regex_error

        binary_path, compile_error = self.compile_c_solution(solution_path, output_name="lab5_solution")
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
                    messages.append(f"Тест {index}: FAIL\nВход:\n{test_case['input_text']}\nОшибка выполнения:\n{runtime_error}")
                    if self.fail_on_first_test:
                        break
                    continue
                expected = normalize_output(test_case["expected_stdout"])
                actual = normalize_output(obtained or "")
                if actual == expected:
                    passed_tests += 1
                    messages.append(f"Тест {index}: OK")
                else:
                    messages.append(f"Тест {index}: FAIL\nВход:\n{test_case['input_text']}\nОжидалось:\n{expected}\nПолучено:\n{actual}")
                    if self.fail_on_first_test:
                        break
        finally:
            if binary_path.exists():
                binary_path.unlink()
            shutil.rmtree(binary_path.parent, ignore_errors=True)

        summary = f"Итог: {passed_tests}/{total_tests} тестов пройдено"
        all_passed = passed_tests == total_tests
        footer = "Все тесты пройдены" if all_passed else "Есть ошибки"
        return all_passed, "\n".join(messages + [summary, footer])


def _validate_regex_usage(solution_path: str) -> str | None:
    path = Path(solution_path)
    if not path.exists():
        return f"Solution file not found: {solution_path}"

    source = path.read_text(encoding="utf-8", errors="ignore")
    missing = [marker for marker in REQUIRED_REGEX_MARKERS if marker not in source]
    if not missing:
        return None

    return (
        "Решение должно использовать регулярные выражения из стандартной библиотеки C.\n"
        "Не найдены обязательные маркеры: "
        + ", ".join(missing)
    )


def normalize_output(text: str) -> str:
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def solve(stdin_data: str, variant: Variant) -> str:
    parser = PARSERS[variant.task_key]
    stage1: list[ParsedRecord] = []

    for raw in stdin_data.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if raw == "Fin.":
            break
        parsed = parser(raw, variant.params)
        if parsed is not None:
            stage1.append(parsed)
    stage2 = [rec.text for rec in stage1 if all(_passes_filter(variant.task_key, rec, flt) for flt in variant.filters)]
    return "\n".join([str(len(stage1)), *(stage2 if stage2 else ["Empty"])])


def _generate_params(task: str, rng: Any) -> dict[str, Any]:

    if task == "terminal":
        return {
            "flags": rand_choice(rng, ("any", "has_any", "no_flags", "has_long", "has_short")),
            "paths": rand_choice(rng, ("any", "absolute", "relative", "none")),
            "user_rule": rand_choice(rng, ("contains", "not_contains")),
            "user_symb": rand_choice(rng, ("_", "a", "1")),
            "host_rule": rand_choice(rng, ("contains", "not_contains")),
            "host_symb": rand_choice(rng, ("-", "_", "1")),
        }
    if task == "url":
        return {
            "protocol": rand_choice(rng, ("required", "forbidden", "optional")),
            "path": rand_choice(rng, ("required", "forbidden", "optional")),
            "query": rand_choice(rng, ("required", "forbidden", "optional")),
            "port": rand_choice(rng, ("any_required", "range_required", "forbidden", "optional")),
            "port_min": rand_int(rng, 1000, 3000),
            "port_max": rand_int(rng, 3001, 9000),
        }
    if task == "ip":
        return {
            "leading_zeroes": rand_choice(rng, ("allowed", "forbidden")),
            "cidr": rand_choice(rng, ("allowed", "forbidden")),
            "port": rand_choice(rng, ("allowed", "forbidden")),
            "hex": rand_choice(rng, ("forbidden", "upper", "lower", "any")),
        }
    if task == "finance":
        return {
            "fraction": rand_choice(rng, ("integer", "fraction", "both")),
            "thousands": rand_choice(rng, ("dot", "underscore", "none", "any")),
            "date_sep": rand_choice(rng, ("/", ".", "-")),
            "currency_case": rand_choice(rng, ("upper", "lower", "any")),
        }
    if task == "server":
        return {
            "dt_wrap": rand_choice(rng, ("[]", "{}", "<>", "any", "none")),
            "date_sep": rand_choice(rng, ("/", ".", "-")),
            "level_wrap": rand_choice(rng, ("[]", "{}", "<>", "any", "none")),
            "sep": rand_choice(rng, (" ", "|", ";")),
        }
    return {
        "dt_wrap": rand_choice(rng, ("[]", "{}", "<>", "any", "none")),
        "date_sep": rand_choice(rng, ("/", ".", "-")),
        "path_rule": rand_choice(rng, ("extension", "no_extension", "query_allowed", "query_forbidden")),
        "status_wrap": rand_choice(rng, ("[]", "{}", "<>", "any", "none")),
    }


def _generate_filters(task: str, params: dict[str, Any], rng: Any, count: int) -> list[dict[str, Any]]:

    if task == "terminal":
        pool = [
            {"kind": "shell", "value": rand_choice(rng, ("$", "#"))},
            {"kind": "pipe"},
            {"kind": "redirect"},
            {"kind": "command_word", "value": rand_choice(rng, ("gcc", "docker", "python", "git"))},
            {"kind": "host_hyphen"},
            {"kind": "host_digit", "value": rand_choice(rng, (True, False))},
            {"kind": "user_digit", "value": rand_choice(rng, (True, False))},
        ]
    elif task == "url":
        pool = [
            {"kind": "domain_zone", "value": rand_choice(rng, (".ru", ".com", ".org", ".edu"))},
        ]
        if params["path"] != "forbidden":
            pool.extend([
                {"kind": "path_ext", "value": rand_choice(rng, (".html", ".php", ".json", ".txt"))},
                {"kind": "path_segments", "op": rand_choice(rng, ("min", "max")), "value": rand_int(rng, 1, 3)},
            ])
        if params["query"] != "forbidden":
            pool.extend([
                {"kind": "query_param", "value": rand_choice(rng, ("id", "page", "token", "q"))},
                {"kind": "query_params_count", "op": rand_choice(rng, ("min", "max")), "value": rand_int(rng, 1, 3)},
            ])
    elif task == "ip":
        pool = [
            {"kind": "repeated_octets", "value": rand_choice(rng, (True, False))},
            rand_choice(rng, ({"kind": "loopback"}, {"kind": "multicast"})),
        ]
        if params["cidr"] == "allowed":
            pool.append({"kind": "cidr_cmp", "op": rand_choice(rng, ("min", "max")), "value": rand_int(rng, 8, 28)})
        if params["port"] == "allowed":
            pool.append({"kind": "port_range", "min": rand_int(rng, 1000, 3000), "max": rand_int(rng, 3001, 9000)})
    elif task == "finance":
        pool = [
            {"kind": "type", "value": rand_choice(rng, ("TRANSFER", "WITHDRAW", "DEPOSIT", "PAYMENT"))},
            {"kind": "amount_cmp", "op": rand_choice(rng, ("gt", "lt")), "value": rand_int(rng, 100, 5000)},
            {"kind": "amount_range", "min": rand_int(rng, 100, 1000), "max": rand_int(rng, 1001, 8000)},
            {"kind": "currency", "value": rand_choice(rng, ("USD", "EUR", "RUB", "GBP"))},
            {"kind": "time_range", "from": "09:00:00", "to": "18:00:00"},
        ]
    elif task == "server":
        pool = [
            {"kind": "level", "value": rand_choice(rng, LEVELS)},
            {"kind": "time_range", "from": "09:00:00", "to": "18:00:00"},
            {"kind": "service_hyphen"},
            {"kind": "service_case", "value": rand_choice(rng, ("upper", "lower"))},
            {"kind": "message_digit", "value": rand_choice(rng, (True, False))},
            {"kind": "message_word", "value": rand_choice(rng, ("timeout", "failed", "denied", "exception"))},
        ]
    else:
        pool = [
            {"kind": "method", "value": rand_choice(rng, ("GET", "POST", "PUT", "DELETE", "PATCH"))},
            {"kind": "status_class", "value": rand_choice(rng, (2, 3, 4, 5))},
            {"kind": "size_range", "min": rand_int(rng, 100, 1000), "max": rand_int(rng, 1001, 9000)},
            {"kind": "protocol", "value": rand_choice(rng, ("HTTP/1.0", "HTTP/1.1", "HTTP/2"))},
            {"kind": "time_range", "from": "09:00:00", "to": "18:00:00"},
        ]

    return rand_sample(rng, pool, min(count, len(pool)))



def parse_terminal(line: str, p: dict[str, Any]) -> ParsedRecord | None:
    m = re.fullmatch(r"([A-Za-z][A-Za-z0-9_]*)@([A-Za-z][A-Za-z0-9_-]*):~([#$]) ([A-Za-z0-9 ./_\-|><]+)", line)

    if not m:
        return None
    
    user, host, shell, command = m.groups()

    if (p["user_symb"] in user) != (p["user_rule"] == "contains"):
        return None
    if (p["host_symb"] in host) != (p["host_rule"] == "contains"):
        return None
    
    flags = re.findall(r"(?<!\S)--[A-Za-z0-9_-]+|(?<!\S)-[A-Za-z0-9_-]+", command)
    has_long = any(f.startswith("--") for f in flags)
    has_short = any(f.startswith("-") and not f.startswith("--") for f in flags)

    if p["flags"] == "has_any" and not flags: return None
    if p["flags"] == "no_flags" and flags: return None
    if p["flags"] == "has_long" and not has_long: return None
    if p["flags"] == "has_short" and not has_short: return None

    has_abs = bool(re.search(r"(?<!\S)/[A-Za-z0-9._/-]+", command))
    has_rel = bool(re.search(r"(?<!\S)(?:\./|\.\./)[A-Za-z0-9._/-]+", command))
    has_path = has_abs or has_rel

    if p["paths"] == "absolute" and not has_abs: return None
    if p["paths"] == "relative" and not has_rel: return None
    if p["paths"] == "none" and has_path: return None

    return ParsedRecord(line, {"user": user, "host": host, "shell": shell, "command": command})


def parse_url(line: str, p: dict[str, Any]) -> ParsedRecord | None:
    m = re.fullmatch(r"(?:(http|https|ftp)://)?([A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+)(?::([0-9]{1,5}))?(/[^?#\s]*)?(\?[^#\s]*)?(#[^\s]*)?", line)
    if not m:
        return None
    
    protocol, domain, port_s, path, query, fragment = m.groups()
    port = int(port_s) if port_s else None

    if port is not None and not (1 <= port <= 65535): return None
    if p["protocol"] == "required" and protocol is None: return None
    if p["protocol"] == "forbidden" and protocol is not None: return None
    if p["path"] == "required" and path is None: return None
    if p["path"] == "forbidden" and path is not None: return None
    if p["query"] == "required" and query is None: return None
    if p["query"] == "forbidden" and query is not None: return None
    if p["port"] == "any_required" and port is None: return None
    if p["port"] == "range_required" and (port is None or not (p["port_min"] <= port <= p["port_max"])): return None
    if p["port"] == "forbidden" and port is not None: return None

    return ParsedRecord(line, {"protocol": protocol, "domain": domain, "port": port, "path": path or "", "query": query or "", "fragment": fragment or ""})


def parse_ip(line: str, p: dict[str, Any]) -> ParsedRecord | None:
    m = re.fullmatch(r"([0-9A-Fa-f]{1,3}(?:\.[0-9A-Fa-f]{1,3}){3})(?:/([0-9]{1,2}))?(?::([0-9]{1,5}))?", line)
    if not m:
        return None
    
    body, cidr_s, port_s = m.groups()
    parts = body.split(".")
    is_hex = any(re.search(r"[A-Fa-f]", x) for x in parts)

    if is_hex:
        if p["hex"] == "forbidden": return None
        if p["hex"] == "upper" and any(re.search(r"[a-f]", x) for x in parts): return None
        if p["hex"] == "lower" and any(re.search(r"[A-F]", x) for x in parts): return None
        nums = [int(x, 16) for x in parts]
    else:
        nums = [int(x, 10) for x in parts]
        if p["leading_zeroes"] == "forbidden" and any(len(x) > 1 and x.startswith("0") for x in parts): return None

    if any(n < 0 or n > 255 for n in nums): return None

    cidr = int(cidr_s) if cidr_s else None
    port = int(port_s) if port_s else None

    if cidr is not None and not (0 <= cidr <= 32): return None
    if port is not None and not (1 <= port <= 65535): return None
    if p["cidr"] == "forbidden" and cidr is not None: return None
    if p["port"] == "forbidden" and port is not None: return None

    return ParsedRecord(line, {"octets": nums, "cidr": cidr, "port": port, "is_hex": is_hex})


def parse_finance(line: str, p: dict[str, Any]) -> ParsedRecord | None:
    sep = re.escape(p["date_sep"])
    m = re.fullmatch(rf"\[(\d{{4}}{sep}\d{{2}}{sep}\d{{2}}) (\d{{2}}:\d{{2}}:\d{{2}})\] (TRANSFER|WITHDRAW|DEPOSIT|PAYMENT) ([0-9][0-9._]*(?:,[0-9]{{1,2}})?) ([A-Za-z]{{3}})", line)

    if not m: return None

    date_s, time_s, typ, amount_s, currency = m.groups()

    if not _valid_datetime(date_s, time_s, p["date_sep"]): return None

    has_fraction = "," in amount_s
    if p["fraction"] == "integer" and has_fraction: return None
    if p["fraction"] == "fraction" and not has_fraction: return None

    int_part = amount_s.split(",")[0]
    if not _valid_amount_int_part(int_part, p["thousands"]): return None
    if p["currency_case"] == "upper" and currency != currency.upper(): return None
    if p["currency_case"] == "lower" and currency != currency.lower(): return None

    return ParsedRecord(line, {"date": date_s, "time": time_s, "type": typ, "amount": _amount_value(amount_s), "currency": currency.upper()})


def parse_server(line: str, p: dict[str, Any]) -> ParsedRecord | None:
    if p["sep"] == " ":
        dt_token = _wrapped_token_regex(p["dt_wrap"], p["date_sep"])
        level_token = _wrapped_token_regex(p["level_wrap"], None)
        pattern = rf"({dt_token}) ({level_token}) ([A-Za-z0-9_.-]+) (.+)"
    else:
        sep = re.escape(p["sep"])
        pattern = rf"(.+?){sep}(.+?){sep}([A-Za-z0-9_.-]+){sep}(.+)"

    m = re.fullmatch(pattern, line)
    if not m: return None

    dt_raw, level_raw, service, msg = m.groups()
    dt = _unwrap(dt_raw, p["dt_wrap"])
    level = _unwrap(level_raw, p["level_wrap"])

    if dt is None or level is None or level not in LEVELS: return None
    mdt = re.fullmatch(rf"(\d{{4}}{re.escape(p['date_sep'])}\d{{2}}{re.escape(p['date_sep'])}\d{{2}}) (\d{{2}}:\d{{2}}:\d{{2}})", dt)
    if not mdt or not _valid_datetime(mdt.group(1), mdt.group(2), p["date_sep"]): return None

    return ParsedRecord(line, {"date": mdt.group(1), "time": mdt.group(2), "level": level, "service": service, "message": msg})
    


def parse_apache(line: str, p: dict[str, Any]) -> ParsedRecord | None:
    m = re.fullmatch(r"(.+?) \"(GET|POST|PUT|DELETE|PATCH) ([^\s]+) (HTTP/1\.0|HTTP/1\.1|HTTP/2)\" (\S+) ([0-9]+)", line)
    if not m: return None

    dt_raw, method, path, proto, status_raw, size_s = m.groups()
    dt = _unwrap(dt_raw, p["dt_wrap"])
    status_s = _unwrap(status_raw, p["status_wrap"])

    if dt is None or status_s is None or not re.fullmatch(r"[1-5][0-9]{2}", status_s): return None

    mdt = re.fullmatch(rf"(\d{{4}}{re.escape(p['date_sep'])}\d{{2}}{re.escape(p['date_sep'])}\d{{2}}) (\d{{2}}:\d{{2}}:\d{{2}})", dt)
    if not mdt or not _valid_datetime(mdt.group(1), mdt.group(2), p["date_sep"]): return None

    has_query = "?" in path
    base = path.split("?", 1)[0]
    has_ext = bool(re.search(r"/[A-Za-z0-9_-]+\.[A-Za-z0-9]+$", base))

    if p["path_rule"] == "extension" and not has_ext: return None
    if p["path_rule"] == "no_extension" and has_ext: return None
    if p["path_rule"] == "query_forbidden" and has_query: return None

    return ParsedRecord(line, {"date": mdt.group(1), "time": mdt.group(2), "method": method, "path": path, "protocol": proto, "status": int(status_s), "size": int(size_s)})


PARSERS: dict[str, Callable[[str, dict[str, Any]], ParsedRecord | None]] = {
    "terminal": parse_terminal, "url": parse_url, "ip": parse_ip,
    "finance": parse_finance, "server": parse_server, "apache": parse_apache,
}


def _wrapped_token_regex(mode: str, date_sep: str | None) -> str:
    if date_sep is None:
        inner = r"[A-Za-z]+"
    else:
        ds = re.escape(date_sep)
        inner = rf"\d{{4}}{ds}\d{{2}}{ds}\d{{2}} \d{{2}}:\d{{2}}:\d{{2}}"
    if mode == "none":
        return inner
    if mode == "[]":
        return rf"\[{inner}\]"
    if mode == "{}":
        return rf"\{{{inner}\}}"
    if mode == "<>":
        return rf"<{inner}>"
    return rf"(?:\[{inner}\]|\{{{inner}\}}|<{inner}>)"


def _unwrap(raw: str, mode: str) -> str | None:
    pairs = {"[]": ("[", "]"), "{}": ("{", "}"), "<>": ("<", ">")}
    if mode == "none":
        if raw[:1] in "[{<" or raw[-1:] in "]}>": return None
        return raw
    if mode == "any":
        for a, b in pairs.values():
            if raw.startswith(a) and raw.endswith(b): return raw[1:-1]
        return None
    a, b = pairs[mode]
    if raw.startswith(a) and raw.endswith(b): return raw[1:-1]

    return None


def _valid_datetime(date_s: str, time_s: str, sep: str) -> bool:
    try:
        datetime.strptime(date_s + " " + time_s, f"%Y{sep}%m{sep}%d %H:%M:%S")
        return True
    except ValueError:
        return False


def _valid_amount_int_part(s: str, rule: str) -> bool:
    if s.startswith("0") and s != "0": return False
    if rule == "none": return s.isdigit()
    seps = {"dot": ".", "underscore": "_"}
    allowed = [seps[rule]] if rule in seps else [".", "_", ""]

    for sep in allowed:
        if sep == "" and s.isdigit(): return True
        if sep and re.fullmatch(rf"[1-9][0-9]{{0,2}}(?:{re.escape(sep)}[0-9]{{3}})+", s): return True

    return False


def _amount_value(s: str) -> float:
    return float(s.replace(".", "").replace("_", "").replace(",", "."))



def _passes_filter(task: str, rec: ParsedRecord, flt: dict[str, Any]) -> bool:
    d = rec.data; k = flt["kind"]
    if k == "shell": return d["shell"] == flt["value"]
    if k == "pipe": return "|" in d["command"]
    if k == "redirect": return ">" in d["command"] or "<" in d["command"]
    if k == "command_word": return d["command"].startswith(flt["value"])
    if k == "host_hyphen": return "-" in d["host"]
    if k == "host_digit": return bool(re.search(r"\d", d["host"])) == flt["value"]
    if k == "user_digit": return bool(re.search(r"\d", d["user"])) == flt["value"]
    if k == "domain_zone": return d["domain"].endswith(flt["value"])
    if k == "path_ext": return d["path"].split("?", 1)[0].endswith(flt["value"])
    if k == "path_segments":
        n = len([x for x in d["path"].split("/") if x])
        return n >= flt["value"] if flt["op"] == "min" else n <= flt["value"]
    if k == "query_param": return _query_has_param(d["query"], flt["value"])
    if k == "query_params_count":
        n = _query_param_count(d["query"])
        return n >= flt["value"] if flt["op"] == "min" else n <= flt["value"]
    if k == "repeated_octets": return (len(set(d["octets"])) < 4) == flt["value"]
    if k == "cidr_cmp":
        return d["cidr"] is not None and (d["cidr"] >= flt["value"] if flt["op"] == "min" else d["cidr"] <= flt["value"])
    if k == "port_range": return d["port"] is not None and flt["min"] <= d["port"] <= flt["max"]
    if k == "loopback": return d["octets"][0] == 127
    if k == "multicast": return 224 <= d["octets"][0] <= 239
    if k == "type": return d["type"] == flt["value"]
    if k == "amount_cmp": return d["amount"] > flt["value"] if flt["op"] == "gt" else d["amount"] < flt["value"]
    if k == "amount_range": return flt["min"] <= d["amount"] <= flt["max"]
    if k == "currency": return d["currency"] == flt["value"]
    if k == "time_range": return flt["from"] <= d["time"] <= flt["to"]
    if k == "level": return d["level"] == flt["value"]
    if k == "service_hyphen": return "-" in d["service"]
    if k == "service_case":
        letters = [c for c in d["service"] if c.isalpha()]
        return bool(letters) and (all(c.isupper() for c in letters) if flt["value"] == "upper" else all(c.islower() for c in letters))
    if k == "message_digit": return bool(re.search(r"\d", d["message"])) == flt["value"]
    if k == "message_word": return re.search(rf"\b{re.escape(flt['value'])}\b", d["message"], re.IGNORECASE) is not None
    if k == "method": return d["method"] == flt["value"]
    if k == "status_class": return d["status"] // 100 == flt["value"]
    if k == "size_range": return flt["min"] <= d["size"] <= flt["max"]
    if k == "protocol": return d["protocol"] == flt["value"]
    return False


def _query_has_param(query: str, name: str) -> bool:
    if not query.startswith("?"): return False
    return any(part.split("=", 1)[0] == name for part in query[1:].split("&") if part)


def _query_param_count(query: str) -> int:
    if not query.startswith("?"): return 0
    return len([part for part in query[1:].split("&") if part])



def _generate_input_lines(v: Variant, rng: Any, count: int) -> list[str]:
    lines: list[str] = ["ordinary text without useful data", "broken 999 record"]
    for _ in range(max(2, count // 4)):
        lines.append(_make_record(v, rng, satisfy_filters=True))
    for _ in range(max(2, count // 3)):
        lines.append(_make_record(v, rng, satisfy_filters=False))
    while len(lines) < count:
        lines.append(_make_invalid_for_task(v.task_key, rng))
    rng.shuffle(lines)

    return lines[:count]


def _make_record(v: Variant, rng: Any, satisfy_filters: bool) -> str:
    for attempt in range(200):
        rec = _make_stage1_record(v.task_key, v.params, rng, satisfy_filters, v.filters, attempt)
        parsed = PARSERS[v.task_key](rec, v.params)
        if parsed is None:
            continue
        ok = all(_passes_filter(v.task_key, parsed, f) for f in v.filters)
        if ok == satisfy_filters:
            return rec
        
    return _make_stage1_record(v.task_key, v.params, rng, False, (), 0)


def _make_stage1_record(task: str, p: dict[str, Any], rng: Any, good: bool, filters: tuple[dict[str, Any], ...], attempt: int) -> str:
    if task == "terminal":
        user = _terminal_user(p, good, filters, attempt)
        host = _terminal_host(p, good, filters, attempt)
        shell = _filter_value(filters, "shell", "#" if good else "$")
        cmd_word = _filter_value(filters, "command_word", "git" if good else "echo")
        command = cmd_word + " status"
        if p["flags"] in ("has_any", "has_short"): command += " -v"
        if p["flags"] == "has_long": command += " --all"
        if p["paths"] == "absolute": command += " /var/log/app.log"
        if p["paths"] == "relative": command += " ./src/main.c"
        if good and any(f["kind"] == "pipe" for f in filters): command += " | grep ok"
        if good and any(f["kind"] == "redirect" for f in filters): command += " > out.txt"

        return f"{user}@{host}:~{shell} {command}"
    
    if task == "url":
        zone = _filter_value(filters, "domain_zone", ".com" if good else ".net")
        domain = "example" + zone
        protocol = "https://" if p["protocol"] in ("required", "optional") else ""
        port = ""
        if p["port"] in ("any_required", "optional"):
            port = ":8080"
        elif p["port"] == "range_required":
            port = f":{p['port_min']}"
        ext = _filter_value(filters, "path_ext", ".html" if good else ".bin")
        path = "/api/v1/file" + ext if p["path"] != "forbidden" else ""
        if p["path"] == "required" and not path: path = "/a/b/file.html"
        qname = _filter_value(filters, "query_param", "id" if good else "x")
        query = f"?{qname}=42&page=1" if p["query"] != "forbidden" else ""
        if p["query"] == "required" and not query: query = "?id=1"

        return protocol + domain + port + path + query
    
    if task == "ip":
        first = 127 if good and any(f["kind"] == "loopback" for f in filters) else 225 if good and any(f["kind"] == "multicast" for f in filters) else 192
        octets = [first, 168, 1, 10 if not (good and any(f["kind"] == "repeated_octets" and f.get("value") for f in filters)) else 1]
        body = ".".join(str(x) for x in octets)
        cidr = "/24" if p["cidr"] == "allowed" else ""
        port = ":8080" if p["port"] == "allowed" else ""

        return body + cidr + port
    
    if task == "finance":
        typ = _filter_value(filters, "type", "DEPOSIT" if good else "PAYMENT")
        amount = "1500" if p["thousands"] == "none" else ("1.500" if p["thousands"] in ("dot", "any") else "1_500")
        if p["fraction"] in ("fraction", "both"): amount += ",50"
        cur = _filter_value(filters, "currency", "USD" if good else "EUR")
        if p["currency_case"] == "lower": cur = cur.lower()
        dt = _format_dt(p["date_sep"], "2025", "05", "12", "12:30:00")

        return f"[{dt}] {typ} {amount} {cur}"
    
    if task == "server":
        level = _filter_value(filters, "level", "ERROR" if good else "INFO")
        service = "auth-service" if good and any(f["kind"] == "service_hyphen" for f in filters) else "cache"
        if good and any(f["kind"] == "service_case" and f["value"] == "upper" for f in filters): service = "DB_CORE"
        if good and any(f["kind"] == "service_case" and f["value"] == "lower" for f in filters): service = "auth-service"
        word = _filter_value(filters, "message_word", "timeout" if good else "started")
        msg = f"request {word} detected"
        if good and any(f["kind"] == "message_digit" and f["value"] for f in filters): msg += " 42"
        if good and any(f["kind"] == "message_digit" and not f["value"] for f in filters): msg = re.sub(r"\d", "", msg)
        dt = _wrap(_format_dt(p["date_sep"], "2025", "05", "12", "12:30:00"), p["dt_wrap"])
        lv = _wrap(level, p["level_wrap"])

        return p["sep"].join([dt, lv, service, msg])
    
    method = _filter_value(filters, "method", "GET" if good else "POST")
    proto = _filter_value(filters, "protocol", "HTTP/1.1" if good else "HTTP/2")
    status_class = _filter_value(filters, "status_class", 2 if good else 5)
    status = str(status_class * 100)
    size = "1500"
    path = "/api/index.html" if p["path_rule"] != "no_extension" else "/api/index"

    if p["path_rule"] == "query_allowed": path += "?id=1"
    dt = _wrap(_format_dt(p["date_sep"], "2025", "05", "12", "12:30:00"), p["dt_wrap"])
    st = _wrap(status, p["status_wrap"])
    
    return f'{dt} "{method} {path} {proto}" {st} {size}'


def _filter_value(filters: tuple[dict[str, Any], ...], kind: str, default: Any) -> Any:
    for f in filters:
        if f["kind"] == kind:
            return f["value"]
    return default


def _terminal_user(p: dict[str, Any], good: bool, filters: tuple[dict[str, Any], ...], attempt: int) -> str:
    name = "user1" if good and any(f["kind"] == "user_digit" and f["value"] for f in filters) else "user"
    symb = p["user_symb"]
    if p["user_rule"] == "contains" and symb not in name:
        name = "u" + symb + "ser" if symb.isalpha() else "user" + symb
    if p["user_rule"] == "not_contains": name = name.replace(symb, "x")
    if not name[0].isalpha(): name = "u" + name
    return name


def _terminal_host(p: dict[str, Any], good: bool, filters: tuple[dict[str, Any], ...], attempt: int) -> str:
    host = "host1" if good and any(f["kind"] == "host_digit" and f["value"] for f in filters) else "host"
    if good and any(f["kind"] == "host_hyphen" for f in filters): host = "web-node"
    symb = p["host_symb"]
    if p["host_rule"] == "contains" and symb not in host:
        host = "h" + symb + "ost" if symb.isalpha() else "host" + symb
    if p["host_rule"] == "not_contains": host = host.replace(symb, "x")
    if not host[0].isalpha(): host = "h" + host
    return host


def _wrap(value: str, mode: str) -> str:
    if mode == "none": return value
    if mode == "any": mode = "[]"
    return {"[]": f"[{value}]", "{}": f"{{{value}}}", "<>": f"<{value}>"}[mode]


def _format_dt(sep: str, y: str, m: str, d: str, time_s: str) -> str:
    return f"{y}{sep}{m}{sep}{d} {time_s}"


def _make_invalid_for_task(task: str, rng: Any) -> str:
    return rand_choice(rng, ("not a valid record", "2025-99-99 bad", "@@@", "Fin but not marker", "broken log line"))



def _describe_format(task: str) -> list[str]:
    return {
        "terminal": ["<username>@<hostname>:~<symbol> <command>", "username начинается с латинской буквы и содержит латинские буквы, цифры, _.", "hostname начинается с латинской буквы и содержит латинские буквы, цифры, _, -.", "symbol — $ или #."],
        "url": ["<protocol><domain><port><path><query><fragment>", "protocol: http://, https:// или ftp://; port: :N, 1 <= N <= 65535."],
        "ip": ["IPv4: X.X.X.X, где каждый октет от 0 до 255.", "Дополнительно вариант может разрешать CIDR-маску, порт и шестнадцатеричные октеты."],
        "finance": ["[<datetime>] <type> <amount> <currency>", "type: TRANSFER, WITHDRAW, DEPOSIT, PAYMENT; amount без ведущих нулей, дробная часть отделяется запятой."],
        "server": ["<datetime> <level> <service> <message>", "level: INFO, DEBUG, WARN, ERROR, CRITICAL; service содержит латинские буквы, цифры, -, _, ."],
        "apache": ["<datetime> \"<method> <path> <protocol>\" <status> <size>", "method: GET, POST, PUT, DELETE, PATCH; protocol: HTTP/1.0, HTTP/1.1, HTTP/2."],
    }[task]


def _describe_params(task: str, p: dict[str, Any]) -> list[str]:
    if task == "terminal":
        return [f"command: {_map(p['flags'], {'any':'может содержать любое количество флагов','has_any':'должен содержать хотя бы один флаг','no_flags':'не должен содержать флаги','has_long':'должен содержать полный флаг --...','has_short':'должен содержать краткий флаг -...'})}", f"command: {_map(p['paths'], {'any':'может содержать пути любого вида','absolute':'должен содержать абсолютный путь','relative':'должен содержать относительный путь','none':'не должен содержать пути'})}", f"username {'должен содержать' if p['user_rule']=='contains' else 'не должен содержать'} символ {p['user_symb']}", f"hostname {'должен содержать' if p['host_rule']=='contains' else 'не должен содержать'} символ {p['host_symb']}"]
    if task == "url":
        return [f"protocol: {_presence(p['protocol'])}", f"path: {_presence(p['path'])}", f"query: {_presence(p['query'])}", f"port: {_describe_port_param(p)}"]
    if task == "ip":
        return [f"ведущие нули: {'разрешены' if p['leading_zeroes']=='allowed' else 'запрещены'}", f"CIDR-маска: {'разрешена' if p['cidr']=='allowed' else 'запрещена'}", f"порт: {'разрешён' if p['port']=='allowed' else 'запрещён'}", f"hex-формат: {_map(p['hex'], {'forbidden':'запрещён','upper':'разрешены только заглавные A-F','lower':'разрешены только строчные a-f','any':'разрешён в любом регистре'})}"]
    if task == "finance":
        return [f"amount: {_map(p['fraction'], {'integer':'только целые числа','fraction':'только дробные числа','both':'целые или дробные числа'})}", f"разделитель тысяч: {_map(p['thousands'], {'dot':'.','underscore':'_','none':'нет','any':'., _ или отсутствует'})}", f"разделитель даты: {p['date_sep']}", f"currency: {_map(p['currency_case'], {'upper':'только заглавные буквы','lower':'только строчные буквы','any':'без учёта регистра'})}"]
    if task == "server":
        return [f"datetime: {_wrap_desc(p['dt_wrap'])}", f"разделитель даты: {p['date_sep']}", f"level: {_wrap_desc(p['level_wrap'])}", f"разделитель между элементами: {repr(p['sep'])}"]
    return [f"datetime: {_wrap_desc(p['dt_wrap'])}", f"разделитель даты: {p['date_sep']}", f"path: {_map(p['path_rule'], {'extension':'обязан оканчиваться расширением','no_extension':'не должен содержать расширение','query_allowed':'может содержать query-параметры','query_forbidden':'не содержит query-параметры'})}", f"status: {_wrap_desc(p['status_wrap'])}"]


def _describe_filter(task: str, f: dict[str, Any]) -> str:
    k = f["kind"]
    if k == "shell": return f"только оболочка {f['value']}"
    if k == "pipe": return "command содержит pipe |"
    if k == "redirect": return "command содержит перенаправление > или <"
    if k == "command_word": return f"command начинается со слова {f['value']}"
    if k == "host_hyphen": return "hostname содержит -"
    if k == "host_digit": return f"hostname {'содержит' if f['value'] else 'не содержит'} число"
    if k == "user_digit": return f"username {'содержит' if f['value'] else 'не содержит'} число"
    if k == "domain_zone": return f"домен оканчивается на {f['value']}"
    if k == "path_ext": return f"path содержит файл с расширением {f['value']}"
    if k == "path_segments": return f"path содержит {'не менее' if f['op']=='min' else 'не более'} {f['value']} сегментов"
    if k == "query_param": return f"query содержит параметр {f['value']}"
    if k == "query_params_count": return f"query содержит {'не менее' if f['op']=='min' else 'не более'} {f['value']} параметров"
    if k == "repeated_octets": return f"адрес {'содержит' if f['value'] else 'не содержит'} повторяющиеся октеты"
    if k == "cidr_cmp": return f"маска подсети {'не меньше' if f['op']=='min' else 'не больше'} {f['value']}"
    if k == "port_range": return f"порт в диапазоне {f['min']}..{f['max']}"
    if k == "loopback": return "только loopback адреса"
    if k == "multicast": return "только multicast адреса"
    if k == "type": return f"type = {f['value']}"
    if k == "amount_cmp": return f"amount {'больше' if f['op']=='gt' else 'меньше'} {f['value']}"
    if k == "amount_range": return f"amount в диапазоне {f['min']}..{f['max']}"
    if k == "currency": return f"currency = {f['value']}"
    if k == "time_range": return f"время в диапазоне {f['from']}..{f['to']}"
    if k == "level": return f"level = {f['value']}"
    if k == "service_hyphen": return "service содержит -"
    if k == "service_case": return f"буквы в service только {'верхнего' if f['value']=='upper' else 'нижнего'} регистра"
    if k == "message_digit": return f"message {'содержит' if f['value'] else 'не содержит'} число"
    if k == "message_word": return f"message содержит слово {f['value']}"
    if k == "method": return f"method = {f['value']}"
    if k == "status_class": return f"status класса {f['value']}xx"
    if k == "size_range": return f"size в диапазоне {f['min']}..{f['max']}"
    if k == "protocol": return f"protocol = {f['value']}"
    return str(f)

def _map(value: str, mapping: dict[str, str]) -> str:
    return mapping[value]


def _presence(value: str) -> str:
    return {"required": "обязателен", "forbidden": "запрещён", "optional": "может быть или отсутствовать"}[value]


def _describe_port_param(p: dict[str, Any]) -> str:
    if p["port"] == "any_required": return "обязателен, любое значение 1..65535"
    if p["port"] == "range_required": return f"обязателен, диапазон {p['port_min']}..{p['port_max']}"
    if p["port"] == "forbidden": return "запрещён"
    return "может быть или отсутствовать"


def _wrap_desc(mode: str) -> str:
    return {"[]":"обособлен []", "{}":"обособлен {}", "<>":"обособлен <>", "any":"обособлен любыми скобками [], {}, <>", "none":"не обособлен"}[mode]
