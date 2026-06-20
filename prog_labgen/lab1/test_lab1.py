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


def test_encode_standard_numbers_with_leading_zeros():
    number_system = make_number_system("positional", 16)

    assert number_system.encode_with_leading_zeros(0) == "0000"
    assert number_system.encode_with_leading_zeros(255) == "00FF"
    assert number_system.encode_with_leading_zeros(-31) == "-001F"
    assert number_system.encode(255) == "FF"


def test_encode_tokenized_numbers_with_leading_zeros():
    number_system = make_number_system("positional", 234)

    assert number_system.encode_with_leading_zeros(0) == "0000"
    assert number_system.encode_with_leading_zeros(500) == "0002:0032"
    assert number_system.encode_with_leading_zeros(-239) == "-0001:0005"
    assert number_system.encode(500) == "2:32"


def test_encode_large_numbers():
    assert make_number_system("positional", 16).encode(4095) == "FFF"
    assert make_number_system("positional", 234).encode(234 * 234 + 5) == "1:0:5"
    assert make_number_system("positional", 234).encode(123456) == "2:59:138"
    assert make_number_system("positional", 234).encode(-123456) == "-2:59:138"


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
    assert test["leading_zeros_input"] is True

    arr = test["input_array"]
    stdin_tokens = test["stdin"].rstrip().split()

    boundary_count = 2
    body_len = len(arr) - boundary_count
    half_len = body_len // 2

    first_half = arr[:half_len]
    second_half = arr[half_len:body_len]
    boundary_values = arr[body_len:]

    first_tokens = stdin_tokens[:half_len]
    second_tokens = stdin_tokens[half_len:body_len]
    boundary_tokens = stdin_tokens[body_len:]

    assert first_half == second_half
    assert boundary_values == [0, 123456]
    assert first_half[0] == 21
    assert first_half[1] == -21
    assert first_tokens[0] == "15"
    assert first_tokens[1] == "-15"
    assert second_tokens[0] == "0015"
    assert second_tokens[1] == "-0015"
    assert boundary_tokens == ["0000", "1E240"]


def test_tokenized_format_for_base_234():
    task = Lab1Task("student", random_base=True, base_min=234, base_max=234)
    test = task.generate_tests()[0]

    assert task._format_stdin([500, -239, 12]) == "2:32 -1:5 12\n"
    assert test["number_base"] == 234
    assert test["number_format"] == "tokenized"
    assert test["leading_zeros_input"] is True


def test_random_base_tests_have_plain_and_leading_zero_halves():
    task = Lab1Task("student", random_base=True, base_min=234, base_max=234)

    for test in task.generate_tests():
        arr = test["input_array"]
        stdin_tokens = test["stdin"].rstrip().split()

        boundary_count = 2
        body_len = len(arr) - boundary_count
        half_len = body_len // 2

        first_half = arr[:half_len]
        second_half = arr[half_len:body_len]
        boundary_values = arr[body_len:]

        first_tokens = stdin_tokens[:half_len]
        second_tokens = stdin_tokens[half_len:body_len]
        boundary_tokens = stdin_tokens[body_len:]

        assert first_half == second_half
        assert boundary_values == [0, 123456]
        assert first_half[0] == 239
        assert first_half[1] == -239

        assert first_tokens[0] == "1:5"
        assert first_tokens[1] == "-1:5"
        assert second_tokens[0] == "0001:0005"
        assert second_tokens[1] == "-0001:0005"
        assert boundary_tokens == ["0000", "0002:0059:0138"]


def test_random_base_expected_output_stays_canonical():
    task = Lab1Task("student", random_base=True, base_min=234, base_max=234)

    for test in task.generate_tests():
        assert "0001:0005" in test["stdin"]
        assert "0002:0059:0138" in test["stdin"]
        assert "0001:0005" not in test["expected_stdout"]
        assert "0002:0059:0138" not in test["expected_stdout"]


def test_default_lab1_stays_decimal():
    task = Lab1Task("student")
    test = task.generate_tests()[0]
    number_system = make_number_system("positional", 10)

    assert task._build_variant()["number_system"]["base"] == 10
    assert number_system.get_format() == "standard"
    assert "leading_zeros_input" in test
    assert test["leading_zeros_input"] is False
    assert test["stdin"] == " ".join(str(value) for value in test["input_array"]) + "\n"