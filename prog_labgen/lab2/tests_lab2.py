import pytest
from typing import List, Dict
from .lab2 import Lab2Task, CORE_FUNCTIONS


def test_render_assignment_is_deterministic():
    t1 = Lab2Task(student="ab12", Nmax=100, K=3)
    t2 = Lab2Task(student="ab12", Nmax=100, K=3)
    v1 = t1._build_variant()
    v2 = t2._build_variant()
    assert v1 == v2, "Одинаковый student = одинаковый вариант"

    text1 = t1.render_assignment()
    text2 = t2.render_assignment()
    assert text1 == text2, "Формулировка должна быть одинаковой"


def test_render_assignment_contains_core_functions():
    t = Lab2Task(student="ab12", Nmax=100, K=3)
    text = t.render_assignment()
    v = t._build_variant()
    for core in v.core_functions:
        module = core["module"]
        assert module in text, f"В формулировке нет модуля {module}"
        assert core["name"] in text, f"В формулировке нет функции {core['name']}"


@pytest.mark.parametrize(
    "Nmax, K, expected_core_count",
    [(10, 2, 2), (100, 10, len(CORE_FUNCTIONS))],
)
def test_core_functions_count(Nmax: int, K: int, expected_core_count: int):
    t = Lab2Task(student="ivanov", Nmax=Nmax, K=K)
    v = t._build_variant()
    assert len(v.core_functions) == min(K, len(CORE_FUNCTIONS)), \
        "K core‑функций, не больше общего пула"


def test_generate_tests_basic():
    t = Lab2Task(student="ab12", Nmax=50, K=2)
    tests = t.generate_tests()
    assert isinstance(tests, list), "generate_tests должен возвращать список"
    assert len(tests) > 0, "Должны быть хотя бы фиксированные тесты"
    for test in tests:
        assert "stdin" in test and "expected_stdout" in test, \
            "Каждый тест должен иметь stdin и expected_stdout"


def test_generate_tests_deterministic():
    t1 = Lab2Task(student="ab12", Nmax=50, K=2)
    tests1 = t1.generate_tests()
    t2 = Lab2Task(student="ab12", Nmax=50, K=2)
    tests2 = t2.generate_tests()
    fixed1 = [t for t in tests1 if t["id"].startswith("fixed_")]
    fixed2 = [t for t in tests2 if t["id"].startswith("fixed_")]
    for t1, t2 in zip(fixed1, fixed2):
        assert t1["stdin"] == t2["stdin"], "Фиксированные входы должны совпадать"
        assert t1["expected_stdout"] == t2["expected_stdout"], "Ожидаемый вывод должен быть одинаковым"


def test_sep_parameter():
    t1 = Lab2Task(student="ab12", Nmax=50, K=2, sep=" ")
    t2 = Lab2Task(student="ab12", Nmax=50, K=2, sep=",")
    
    tests1 = t1.generate_tests()
    tests2 = t2.generate_tests()
    
    for test1, test2 in zip(tests1[:5], tests2[:5]):
        if test1["stdin"].strip():
            assert " " in test1["stdin"], "Первый тест должен использовать пробелы"
            assert "," in test2["stdin"], "Второй тест должен использовать запятые"
            numbers1 = test1["stdin"].replace(" ", "").replace(",", "").replace("\n", "")
            numbers2 = test2["stdin"].replace(" ", "").replace(",", "").replace("\n", "")
            assert numbers1 == numbers2, "Числа должны быть одинаковыми"


def test_empty_array_handling():
    t = Lab2Task(student="ab12", Nmax=50, K=3)
    tests = t.generate_tests()
    
    empty_test = None
    for test in tests:
        if test["id"] == "fixed_5":
            empty_test = test
            break
    
    assert empty_test is not None, "Должен быть тест с пустым массивом"
    assert empty_test["stdin"] == "\n", "Пустой ввод"
    
    lines = empty_test["expected_stdout"].split("\n")
    
    line_count = empty_test["expected_stdout"].count("\n") + 1
    
    assert line_count == t.K, f"Должно быть {t.K} строк вывода для пустого массива, получено {line_count} строк"
    
    first_line = lines[0] if lines else ""
    assert first_line in ["YES", "NO"], f"Первая строка должна быть YES или NO, получено: '{first_line}'"

def test_check_method_exists():
    t = Lab2Task(student="ab12", Nmax=50, K=2)
    assert hasattr(t, "check"), "check должен быть методом"
    assert callable(t.check), "check должен быть вызываемым"


def test_format_array_with_empty():
    t = Lab2Task(student="ab12", Nmax=50, K=2)
    assert t._format_array([]) == "", "Пустой массив должен давать пустую строку"


def test_format_array_with_sep():
    t1 = Lab2Task(student="ab12", Nmax=50, K=2, sep=" ")
    t2 = Lab2Task(student="ab12", Nmax=50, K=2, sep=",")
    
    arr = [1, 2, 3]
    assert t1._format_array(arr) == "1 2 3", "Пробельный разделитель"
    assert t2._format_array(arr) == "1,2,3", "Запятая как разделитель"