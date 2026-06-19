from .lab1 import Lab1Task, NumberSystem, PositionalNumberSystem, make_number_system


def test_positional_number_system_uses_common_interface():
    number_system = make_number_system("positional", 16)

    assert isinstance(number_system, NumberSystem)
    assert isinstance(number_system, PositionalNumberSystem)
    assert number_system.encode(255) == "FF"
    assert number_system.get_format() == "standard"


def test_encode_standard_numbers():
    assert make_number_system("positional", 16).encode(0) == "0"
    assert make_number_system("positional", 16).encode(255) == "FF"
    assert make_number_system("positional", 16).encode(-31) == "-1F"
    assert make_number_system("positional", 36).encode(35) == "Z"


def test_encode_tokenized_numbers():
    assert make_number_system("positional", 37).encode(38) == "1:1"
    assert make_number_system("positional", 234).encode(500) == "2:32"
    assert make_number_system("positional", 234).encode(-500) == "-2:32"


def test_random_base_is_deterministic():
    task1 = Lab1Task("student", random_base=True, base_min=10, base_max=234)
    task2 = Lab1Task("student", random_base=True, base_min=10, base_max=234)

    assert task1._build_variant()["number_system"] == task2._build_variant()["number_system"]
    assert 10 <= task1._build_variant()["number_system"]["base"] <= 234


def test_standard_format_for_base_16():
    task = Lab1Task("student", random_base=True, base_min=16, base_max=16)
    test = task.generate_tests()[0]
    number_system = make_number_system("positional", 16)

    assert test["number_base"] == 16
    assert test["number_format"] == "standard"
    assert test["stdin"] == " ".join(number_system.encode(value) for value in test["input_array"]) + "\n"


def test_tokenized_format_for_base_234():
    task = Lab1Task("student", random_base=True, base_min=234, base_max=234)

    assert task._format_stdin([500, -239, 12]) == "2:32 -1:5 12\n"
    assert task.generate_tests()[0]["number_base"] == 234
    assert task.generate_tests()[0]["number_format"] == "tokenized"


def test_default_lab1_stays_decimal():
    task = Lab1Task("student")
    test = task.generate_tests()[0]
    number_system = make_number_system("positional", 10)

    assert task._build_variant()["number_system"]["base"] == 10
    assert number_system.get_format() == "standard"
    assert test["stdin"] == " ".join(str(value) for value in test["input_array"]) + "\n"