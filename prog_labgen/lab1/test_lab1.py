from .lab1 import Lab1Task, NumberSystem, PositionalNumberSystem, encode_number, get_number_format, make_number_system


def test_positional_number_system_uses_common_interface():
    number_system = make_number_system("positional", 16)

    assert isinstance(number_system, NumberSystem)
    assert isinstance(number_system, PositionalNumberSystem)
    assert number_system.encode(255) == "FF"
    assert number_system.get_format() == "standard"


def test_encode_standard_numbers():
    assert encode_number(0, 16) == "0"
    assert encode_number(255, 16) == "FF"
    assert encode_number(-31, 16) == "-1F"
    assert encode_number(35, 36) == "Z"


def test_encode_tokenized_numbers():
    assert encode_number(38, 37) == "1:1"
    assert encode_number(500, 234) == "2:32"
    assert encode_number(-500, 234) == "-2:32"


def test_random_base_is_deterministic():
    task1 = Lab1Task("student", random_base=True, base_min=10, base_max=234)
    task2 = Lab1Task("student", random_base=True, base_min=10, base_max=234)

    assert task1._build_variant()["number_system"] == task2._build_variant()["number_system"]
    assert 10 <= task1._build_variant()["number_system"]["base"] <= 234


def test_standard_format_for_base_16():
    task = Lab1Task("student", random_base=True, base_min=16, base_max=16)
    test = task.generate_tests()[0]

    assert test["number_base"] == 16
    assert test["number_format"] == "standard"
    assert test["stdin"] == " ".join(encode_number(value, 16) for value in test["input_array"]) + "\n"


def test_tokenized_format_for_base_234():
    task = Lab1Task("student", random_base=True, base_min=234, base_max=234)

    assert task._format_stdin([500, -239, 12]) == "2:32 -1:5 12\n"
    assert task.generate_tests()[0]["number_base"] == 234
    assert task.generate_tests()[0]["number_format"] == "tokenized"


def test_default_lab1_stays_decimal():
    task = Lab1Task("student")
    test = task.generate_tests()[0]

    assert task._build_variant()["number_system"]["base"] == 10
    assert get_number_format(10) == "standard"
    assert test["stdin"] == " ".join(str(value) for value in test["input_array"]) + "\n"
