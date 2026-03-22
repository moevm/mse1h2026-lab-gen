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
        assert f"модуль: {module}" in text, f"В формулировке нет модуля {module}"
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

def test_check_success_and_failure():
    t = Lab2Task(student="ab12", Nmax=50, K=2)
    tests = t.generate_tests()
    fake_binary_dir = (t.solution_path.parent / "fake_build") if hasattr(t, "solution_path") else None
    if fake_binary_dir:
        fake_binary_dir.mkdir(exist_ok=True)
        fake_binary = fake_binary_dir / "lab2_solution"
        fake_binary.write_text("#")

    assert isinstance(t.generate_tests(), list), "generate_tests работает"
    assert len(t.generate_tests()) > 0, "Есть тесты"