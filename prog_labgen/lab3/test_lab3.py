import pytest

from prog_labgen.lab3.lab3 import (
    Limits,
    Sentence,
    Variant,
    SolveResult,
    Lab3Task,
    SelectRule,
    RewriteRule,
    KeywordRule,
    SelectRuleKind,
    RewriteRuleKind,
    KeywordRuleKind,
    cut_text_to_marker,
    split_sentences,
    apply_select_rule,
    apply_rewrite_rule,
    choose_keyword,
    solve_text,
    normalize_output,
)


def test_cut_text_to_marker_middle():
    assert cut_text_to_marker("abc ### tail", "###") == "abc "


def test_split_sentences_trims_leading_spaces():
    limits = Limits()
    sentences = split_sentences("   One two.\tThree four! ###", limits)

    assert len(sentences) == 2
    assert sentences[0].normalized == "One two."
    assert sentences[0].words == ("One", "two")
    assert sentences[0].ending == "."
    assert sentences[1].normalized == "Three four!"


def test_apply_select_rule_position_even():
    s1 = Sentence(index=1, raw="A.", normalized="A.", ending=".", words=("A",))
    s2 = Sentence(index=2, raw="B.", normalized="B.", ending=".", words=("B",))
    rule = SelectRule(kind=SelectRuleKind.POSITION, position_type="even")

    assert apply_select_rule(s1, rule) is False
    assert apply_select_rule(s2, rule) is True


def test_apply_select_rule_digit_count():
    sentence = Sentence(
        index=1,
        raw="ab 12 c3.",
        normalized="ab 12 c3.",
        ending=".",
        words=("ab", "12", "c3"),
    )
    rule = SelectRule(kind=SelectRuleKind.DIGIT_COUNT, threshold=3)

    assert apply_select_rule(sentence, rule) is True


def test_apply_rewrite_rule_reverse_words():
    sentence = Sentence(
        index=1,
        raw="one two three.",
        normalized="one two three.",
        ending=".",
        words=("one", "two", "three"),
    )
    rule = RewriteRule(kind=RewriteRuleKind.REVERSE_WORDS)

    assert apply_rewrite_rule(sentence, rule) == ["three", "two", "one"]


def test_apply_rewrite_rule_remove_even():
    sentence = Sentence(
        index=1,
        raw="one two three four.",
        normalized="one two three four.",
        ending=".",
        words=("one", "two", "three", "four"),
    )
    rule = RewriteRule(kind=RewriteRuleKind.REMOVE_BY_POSITION, position_type="even")

    assert apply_rewrite_rule(sentence, rule) == ["one", "three"]


def test_choose_keyword_last_shortest():
    words = ["alpha", "to", "bbb", "io"]
    rule = KeywordRule(kind=KeywordRuleKind.LAST_SHORTEST)

    assert choose_keyword(words, rule) == "io"


def test_choose_keyword_by_position_fallback_to_last():
    words = ["one", "two"]
    rule = KeywordRule(kind=KeywordRuleKind.BY_POSITION, position=5)

    assert choose_keyword(words, rule) == "two"


def test_solve_text_end_to_end():
    variant = Variant(
        seed="test",
        seed_hash=1,
        select_rule=SelectRule(kind=SelectRuleKind.POSITION, position_type="odd"),
        rewrite_rule=RewriteRule(kind=RewriteRuleKind.REVERSE_WORDS),
        keyword_rule=KeywordRule(kind=KeywordRuleKind.FIRST_LONGEST),
        limits=Limits(),
    )

    result = solve_text("one two. three four five! ###", variant)

    assert result.transformed_sentences == ["two one."]
    assert result.keywords == ["two"]
    assert result.render_output() == "two one.\nKey words: two"


def test_solve_result_empty_render():
    result = SolveResult([], [])
    assert result.render_output() == "EMPTY\nKey words: EMPTY"


def test_normalize_output():
    text = "a  \r\nb\r\n\r\n"
    assert normalize_output(text) == "a\nb"


def test_build_variant_is_deterministic():
    task1 = Lab3Task(seed="ivanov", tests_count=3)
    task2 = Lab3Task(seed="ivanov", tests_count=3)

    v1 = task1._build_variant()
    v2 = task2._build_variant()

    assert v1 == v2


def test_generate_tests_count_and_shape():
    task = Lab3Task(seed="ivanov", tests_count=3)
    tests = task.generate_tests()

    assert len(tests) == 3
    for test in tests:
        assert "stdin" in test
        assert "expected_stdout" in test
        assert "test_id" in test


def test_check_success(monkeypatch, tmp_path):
    task = Lab3Task(seed="ivanov", tests_count=1)

    fake_bin_dir = tmp_path / "build"
    fake_bin_dir.mkdir()
    fake_bin = fake_bin_dir / "lab3_solution"
    fake_bin.write_text("")

    expected = task.generate_tests()[0]["expected_stdout"]

    monkeypatch.setattr(task, "compile_c_solution", lambda *args, **kwargs: (fake_bin, None))
    monkeypatch.setattr(task, "run_binary", lambda *args, **kwargs: (expected, None))

    ok, message = task.check("solution.c")

    assert ok is True
    assert "Тест 1: OK" in message
