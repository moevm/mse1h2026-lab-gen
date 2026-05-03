import pytest

from .lab2 import Lab2Task, parse_student_solution_blob


def test_render_assignment_is_deterministic():
    t1 = Lab2Task(student="ab12", Nmax=100, K=3)
    t2 = Lab2Task(student="ab12", Nmax=100, K=3)
    assert t1._build_variant() == t2._build_variant()
    assert t1.render_assignment() == t2.render_assignment()


def test_render_assignment_contains_required_modules():
    task = Lab2Task(student="ab12", Nmax=100, K=3)
    variant = task._build_variant()
    text = task.render_assignment()

    assert variant.main_file in text
    assert f"{variant.data_io_module}.h" in text
    assert f"{variant.core_module}.c" in text
    assert variant.executable in text
    for step in variant.steps:
        assert step.name in text
        assert step.module in text
        for call in step.calls:
            assert call in text


def test_variant_contains_k_steps():
    task = Lab2Task(student="ivanov", Nmax=50, K=2)
    variant = task._build_variant()
    assert len(variant.steps) == 2


def test_generate_tests_basic_shape():
    task = Lab2Task(student="ab12", Nmax=50, K=2)
    tests = task.generate_tests()
    assert isinstance(tests, list)
    assert len(tests) == 10
    for test in tests:
        assert "stdin" in test and "expected_stdout" in test


def test_every_test_has_exactly_k_output_lines():
    task = Lab2Task(student="ab12", Nmax=50, K=3)
    tests = task.generate_tests()
    for test in tests:
        assert len(test["expected_stdout"].splitlines()) == 3


def test_empty_array_handling():
    task = Lab2Task(student="ab12", Nmax=50, K=3)
    tests = task.generate_tests()
    empty_test = next(test for test in tests if test["id"] == "fixed_5")
    assert empty_test["stdin"] == "\n"
    assert len(empty_test["expected_stdout"].splitlines()) == 3


def test_parser_supports_new_block_format_and_preserves_blank_lines():
    blob = """###main_x.c###
int main(void) {

    return 0;
}
###Makefile###
all:
\techo ok
"""
    entries = parse_student_solution_blob(blob)
    assert entries[0][0] == "main_x.c"
    assert "\n\n" in entries[0][1]
    assert entries[1][0] == "Makefile"


def test_check_method_exists():
    task = Lab2Task(student="ab12", Nmax=50, K=2)
    assert callable(task.check)


@pytest.mark.parametrize("student", ["ab12", "ivanov", "petrov"])
def test_variant_has_at_least_three_core_functions(student: str):
    task = Lab2Task(student=student, Nmax=100, K=3)
    variant = task._build_variant()
    assert len(variant.core_functions) >= 3


def test_every_core_function_is_used_in_at_least_one_step():
    task = Lab2Task(student="lalala", Nmax=100, K=4)
    variant = task._build_variant()
    used = {call for step in variant.steps for call in step.calls}
    declared = {spec.name for spec in variant.core_functions}
    assert declared <= used


def test_generated_suffixes_have_required_lengths_and_valid_charset():
    task = Lab2Task(student="lalala", Nmax=100, K=4)
    variant = task._build_variant()

    def suffix_of(name: str, prefix: str, tail: str = "") -> str:
        assert name.startswith(prefix)
        if tail:
            assert name.endswith(tail)
            name = name[: -len(tail)]
        return name[len(prefix):]

    alphabet = set("abcdefghijklmnopqrstuvwxyz0123456789")

    main_suffix = suffix_of(variant.main_file, "main_", ".c")
    assert len(main_suffix) == 4
    assert set(main_suffix) <= alphabet

    file_suffixes = [
        suffix_of(variant.data_io_module, "data_io_"),
        suffix_of(variant.core_module, "core_"),
        suffix_of(variant.executable, "lab2_"),
        *[suffix_of(step.module, "step_") for step in variant.steps],
    ]
    for suffix in file_suffixes:
        assert len(suffix) == 3
        assert set(suffix) <= alphabet

    function_suffixes = [
        *[spec.name[len("cf_") :] for spec in variant.core_functions],
        *[step.name[len("sf_") :] for step in variant.steps],
    ]
    for suffix in function_suffixes:
        assert len(suffix) == 3
        assert set(suffix) <= alphabet


def test_format_test_fail_message_has_expected_and_no_reason_label():
    task = Lab2Task(student="lalala", Nmax=100, K=4)
    msg = task._format_test_fail_message(
        test_index=1,
        test_id="fixed_1",
        stdin_text="1 2 3\n",
        expected_text="1 2 3\n4 5 6",
        actual_text="1 2 3\n4 5 0",
    )
    assert "Ожидалось:\n1 2 3\n4 5 6" in msg
    assert "Получено:\n1 2 3\n4 5 0" in msg


def test_constructor_accepts_new_lowercase_parameters():
    task = Lab2Task(student="ab12", nmax=50, k=2)
    assert task.Nmax == 50
    assert task.K == 2


@pytest.mark.parametrize(
    ("kwargs", "error_part"),
    [
        ({"student": "", "nmax": 50, "k": 2}, "--student"),
        ({"student": "ab12", "nmax": 0, "k": 2}, "--n-max"),
        ({"student": "ab12", "nmax": 50, "k": 0}, "--k"),
    ],
)
def test_constructor_rejects_invalid_parameters(kwargs, error_part):
    with pytest.raises(ValueError, match=error_part):
        Lab2Task(**kwargs)



def test_check_from_text_blob_keeps_lab2_check_text_functionality(capsys):
    from .lab2 import check_from_text_blob

    variant = Lab2Task(student="ab12", nmax=100, k=3)._build_variant()
    blob = (
        f"###{variant.main_file}###\n"
        "int main(void) {\n"
        "    return 1;\n"
        "}\n"
        "###Makefile###\n"
        "CC ?= gcc\n"
        "CFLAGS ?= -std=c11 -Wall -Wextra -pedantic\n"
        f"{variant.executable}: {variant.main_file}\n"
        f"\t$(CC) $(CFLAGS) -o {variant.executable} {variant.main_file}\n"
        "clean:\n"
        f"\trm -f {variant.executable}\n"
    )

    check_from_text_blob(
        blob_text=blob,
        student="ab12",
        nmax=100,
        k=3,
        fail_on_first_test=True,
    )

    output = capsys.readouterr().out
    assert "FAIL" in output
    assert "Программа завершилась" in output
