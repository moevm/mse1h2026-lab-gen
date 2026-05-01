from __future__ import annotations

import shutil
from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable

from prog_labgen.base_module import (
    BaseTask,
    build_faker,
    faker_text,
    rand_bool,
    rand_choice,
    rand_comparison,
    rand_direction,
    rand_int,
    rand_position_type,
)

"""
Использование внешних зависимостей
----------------------------------

Для генерации тестовых данных в данной лабораторной работе используется
библиотека Faker.

Если библиотека уже установлена в используемом Python-окружении,
дополнительных действий не требуется.

Проверка наличия Faker:
    python3 -c "from faker import Faker"

Если возникает ошибка ModuleNotFoundError, рекомендуется установить
библиотеку через виртуальное окружение:

    python3 -m venv venv
    source venv/bin/activate
    pip install Faker

После установки необходимо запускать проект внутри активированного
окружения (venv).

Важно:
Faker должен быть установлен в том же окружении Python, из которого
запускается данный проект.
"""

DEFAULT_SENTENCE_ENDINGS = ".;?!"
DEFAULT_VOWELS = set("aeiouAEIOU")


@dataclass(frozen=True)
class Limits:
    text_max: int = 10000
    sentence_max: int = 200
    word_max: int = 64
    sentence_endings: str = DEFAULT_SENTENCE_ENDINGS
    text_end_marker: str = "###"


class SelectRuleKind(str, Enum):
    WORD_COUNT = "word_count"  # отбор по количеству слов
    ENDING_PUNCT = "ending_punct"  # отбор по завершающему знаку
    WORD_LENGTH = "word_length"  # отбор по длине слова
    DIGIT_COUNT = "digit_count"  # отбор по числу цифр
    POSITION = "position"  # отбор по позиции


class RewriteRuleKind(str, Enum):
    REVERSE_WORDS = "reverse_words"  # разворот порядка слов
    CYCLIC_SHIFT = "cyclic_shift"  # циклический сдвиг слов
    SWAP_FIRST_LAST = "swap_first_last"  # обмен первого и последнего слова
    REMOVE_BY_POSITION = "remove_by_position"  # удаление слов по позиции
    DUPLICATE_FIRST = "duplicate_first"  # дублирование первого слова


class KeywordRuleKind(str, Enum):
    FIRST_LONGEST = "first_longest"  # первое самое длинное слово
    LAST_SHORTEST = "last_shortest"  # последнее самое короткое слово
    MAX_VOWELS = "max_vowels"  # слово с наибольшим числом гласных
    BY_POSITION = "by_position"  # слово по позиции


@dataclass(frozen=True)
class SelectRule:
    kind: SelectRuleKind
    comparison: str | None = None
    threshold: int | None = None
    endings: tuple[str, ...] | None = None
    position_type: str | None = None


@dataclass(frozen=True)
class RewriteRule:
    kind: RewriteRuleKind
    direction: str | None = None
    shift: int | None = None
    position_type: str | None = None


@dataclass(frozen=True)
class KeywordRule:
    kind: KeywordRuleKind
    position: int | None = None


@dataclass(frozen=True)
class Variant:
    seed: str
    seed_hash: int
    select_rule: SelectRule
    rewrite_rule: RewriteRule
    keyword_rule: KeywordRule
    limits: Limits


@dataclass(frozen=True)
class Sentence:
    index: int
    raw: str
    normalized: str
    ending: str
    words: tuple[str, ...]


# Сериализация результата задачи в строку вывода
@dataclass(frozen=True)
class SolveResult:
    transformed_sentences: list[str]
    keywords: list[str]

    def render_output(self) -> str:
        if not self.transformed_sentences:
            return "EMPTY\nKey words: EMPTY"
        return "\n".join([
            *self.transformed_sentences,
            f"Key words: {' '.join(self.keywords)}",
        ])


COMPARISONS: dict[str, Any] = {
    "<": lambda a, b: a < b,
    "<=": lambda a, b: a <= b,
    "==": lambda a, b: a == b,
    ">=": lambda a, b: a >= b,
    ">": lambda a, b: a > b,
}


class Lab3Task(BaseTask):
    def __init__(
            self,
            seed: str,
            text_max: int = 10000,
            sentence_max: int = 200,
            word_max: int = 64,
            tests_count: int = 10,
            fail_on_first_test: bool = True,
            compiler: str | None = None
    ) -> None:
        super().__init__(seed=seed, fail_on_first_test=fail_on_first_test, compiler=compiler)
        self.limits = Limits(
            text_max=text_max,
            sentence_max=sentence_max,
            word_max=word_max,
        )
        self.tests_count = max(1, tests_count)
        self._variant: Variant | None = None

    def _build_variant(self) -> Variant:
        if self._variant is not None:
            return self._variant

        rng = self.make_random()
        select_kind = rand_choice(rng, list(SelectRuleKind))
        rewrite_kind = rand_choice(rng, list(RewriteRuleKind))
        keyword_kind = rand_choice(rng, list(KeywordRuleKind))

        select_rule = _generate_select_rule(select_kind, rng, self.limits)
        rewrite_rule = _generate_rewrite_rule(rewrite_kind, rng)
        keyword_rule = _generate_keyword_rule(keyword_kind, rng)
        select_rule = _ensure_select_rule_has_positive_case(select_rule, rewrite_rule)

        self._variant = Variant(
            seed=self.seed,
            seed_hash=self.make_seed_hash(),
            select_rule=select_rule,
            rewrite_rule=rewrite_rule,
            keyword_rule=keyword_rule,
            limits=self.limits,
        )
        return self._variant

    def render_assignment(self) -> str:
        variant = self._build_variant()
        lines = [
            "Концепция варианта ЛР3",
            f"Seed: {variant.seed}",
            f"Seed hash: {variant.seed_hash}",
            f"TextMax: {variant.limits.text_max}",
            f"SentenceMax: {variant.limits.sentence_max}",
            f"WordMax: {variant.limits.word_max}",
            "Программа должна читать текст из stdin до маркера ###, выделять предложения, обрабатывать их и печатать результат.",
            "Предложения заканчиваются одним из символов: . ; ? !",
            "Общие требования:",
            "- пробелы и табуляции в начале предложения удаляются;",
            "- маркер ### не входит в обработку;",
            "- каждое предложение результата выводится с новой строки;",
            "- порядок выбранных предложений не меняется;",
            "- если после обработки не осталось ни одного предложения, вывести EMPTY;",
            "- после всех предложений вывести строку Key words: ...;",
            "- если предложений не осталось, вывести Key words: EMPTY.",
            "Правила варианта:",
            f"1. select_rule: {_describe_select_rule(variant.select_rule)}",
            f"2. rewrite_rule: {_describe_rewrite_rule(variant.rewrite_rule)}",
            f"3. keyword_rule: {_describe_keyword_rule(variant.keyword_rule)}",
        ]
        return "\n".join(lines)

    def generate_tests(self) -> list[dict[str, Any]]:
        variant = self._build_variant()
        tests: list[dict[str, Any]] = []
        rng = self.make_random("lab3-tests")
        faker = build_faker(self.make_seed_hash("lab3-faker"))

        tests.append(
            _build_test_case(
                variant,
                f"{self.limits.text_end_marker}\n",
                "empty_1",
                expect_empty=True,
            )
        )
        for index in range(2, self.tests_count + 1):
            input_text = generate_positive_input(variant, rng, faker, index=index)
            tests.append(_build_test_case(variant, input_text, f"positive_{index}", expect_empty=False))

        return tests

    def check(self, solution_path: str) -> tuple[bool, str]:
        binary_path, compile_error = self.compile_c_solution(
            solution_path,
            output_name="lab3_solution",
        )
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
                    messages.append(
                        f"Тест {index}: FAIL\n"
                        f"Вход:\n{test_case['input_text']}\n"
                        f"Ошибка выполнения:\n{runtime_error}"
                    )
                    if self.fail_on_first_test:
                        break
                    continue

                expected = normalize_output(test_case["expected_stdout"])
                actual = normalize_output(obtained or "")

                if actual == expected:
                    passed_tests += 1
                    messages.append(f"Тест {index}: OK")
                    continue

                messages.append(
                    f"Тест {index}: FAIL\n"
                    f"Вход:\n{test_case['input_text']}\n"
                    f"Ожидалось:\n{expected}\n"
                    f"Получено:\n{actual}"
                )
                if self.fail_on_first_test:
                    break
        finally:
            if binary_path.exists():
                binary_path.unlink()
            try:
                binary_path.parent.rmdir()
            except OSError:
                pass
            shutil.rmtree(binary_path.parent, ignore_errors=True)

        summary = f"Итог: {passed_tests}/{total_tests} тестов пройдено"
        all_passed = passed_tests == total_tests
        footer = "Все тесты пройдены" if all_passed else "Есть ошибки"
        return all_passed, "\n".join(messages + [summary, footer])


def _generate_select_rule(kind: SelectRuleKind, rng: Any, limits: Limits) -> SelectRule:
    if kind is SelectRuleKind.WORD_COUNT:
        return SelectRule(
            kind=kind,
            comparison=rand_comparison(rng, tuple(COMPARISONS.keys())),
            threshold=rand_int(rng, 1, min(12, max(1, limits.word_max))),
        )
    if kind is SelectRuleKind.ENDING_PUNCT:
        endings = [symbol for symbol in limits.sentence_endings if rand_bool(rng)]
        if not endings:
            endings = [rand_choice(rng, tuple(limits.sentence_endings))]
        return SelectRule(kind=kind, endings=tuple(sorted(endings)))
    if kind is SelectRuleKind.WORD_LENGTH:
        return SelectRule(kind=kind, threshold=rand_int(rng, 1, min(12, max(1, limits.word_max))))
    if kind is SelectRuleKind.DIGIT_COUNT:
        return SelectRule(kind=kind, threshold=rand_int(rng, 1, 8))
    if kind is SelectRuleKind.POSITION:
        return SelectRule(kind=kind, position_type=rand_position_type(rng))
    raise ValueError(f"Unsupported select rule kind: {kind}")


def _minimum_word_count_surviving_rewrite(rule: RewriteRule) -> int:
    if rule.kind is RewriteRuleKind.REMOVE_BY_POSITION and rule.position_type == "odd":
        return 2
    return 1


def _word_count_survives_rewrite(word_count: int, rule: RewriteRule) -> bool:
    return word_count >= _minimum_word_count_surviving_rewrite(rule)


def _find_positive_word_count(rule: SelectRule, rewrite_rule: RewriteRule) -> int | None:
    if rule.kind is not SelectRuleKind.WORD_COUNT:
        return _minimum_word_count_surviving_rewrite(rewrite_rule)

    threshold = int(rule.threshold or 1)
    upper_bound = max(24, threshold + 10)
    for word_count in range(1, upper_bound + 1):
        if not COMPARISONS[str(rule.comparison)](word_count, threshold):
            continue
        if _word_count_survives_rewrite(word_count, rewrite_rule):
            return word_count
    return None


def _ensure_select_rule_has_positive_case(
    select_rule: SelectRule,
    rewrite_rule: RewriteRule,
) -> SelectRule:
    if select_rule.kind is not SelectRuleKind.WORD_COUNT:
        return select_rule
    if _find_positive_word_count(select_rule, rewrite_rule) is not None:
        return select_rule

    minimum = _minimum_word_count_surviving_rewrite(rewrite_rule)
    comparison = str(select_rule.comparison)
    if comparison == "<":
        threshold = minimum + 1
    elif comparison == "<=":
        threshold = minimum
    elif comparison == "==":
        threshold = minimum
    else:
        threshold = int(select_rule.threshold or minimum)

    return SelectRule(
        kind=select_rule.kind,
        comparison=select_rule.comparison,
        threshold=threshold,
    )


def _generate_rewrite_rule(kind: RewriteRuleKind, rng: Any) -> RewriteRule:
    if kind is RewriteRuleKind.REVERSE_WORDS:
        return RewriteRule(kind=kind)
    if kind is RewriteRuleKind.CYCLIC_SHIFT:
        return RewriteRule(kind=kind, direction=rand_direction(rng), shift=rand_int(rng, 1, 5))
    if kind is RewriteRuleKind.SWAP_FIRST_LAST:
        return RewriteRule(kind=kind)
    if kind is RewriteRuleKind.REMOVE_BY_POSITION:
        return RewriteRule(kind=kind, position_type=rand_position_type(rng))
    if kind is RewriteRuleKind.DUPLICATE_FIRST:
        return RewriteRule(kind=kind)
    raise ValueError(f"Unsupported rewrite rule kind: {kind}")


def _generate_keyword_rule(kind: KeywordRuleKind, rng: Any) -> KeywordRule:
    if kind is KeywordRuleKind.BY_POSITION:
        return KeywordRule(kind=kind, position=rand_int(rng, 1, 5))
    return KeywordRule(kind=kind)


def _describe_select_rule(rule: SelectRule) -> str:
    if rule.kind is SelectRuleKind.WORD_COUNT:
        return f"выбрать предложение, если число слов {rule.comparison} {rule.threshold}."
    if rule.kind is SelectRuleKind.ENDING_PUNCT:
        endings_text = ", ".join(repr(symbol) for symbol in (rule.endings or ()))
        return f"выбрать предложение, только если оно оканчивается одним из символов: {endings_text}."
    if rule.kind is SelectRuleKind.WORD_LENGTH:
        return f"выбрать предложение, только если в нём есть слово длины не меньше {rule.threshold}."
    if rule.kind is SelectRuleKind.DIGIT_COUNT:
        return f"выбрать предложение, только если общее число цифр в предложении не меньше {rule.threshold}."
    return f"выбрать только предложения с {'чётными' if rule.position_type == 'even' else 'нечётными'} номерами."


def _describe_rewrite_rule(rule: RewriteRule) -> str:
    if rule.kind is RewriteRuleKind.REVERSE_WORDS:
        return "развернуть порядок слов, сохранив завершающий знак предложения."
    if rule.kind is RewriteRuleKind.CYCLIC_SHIFT:
        direction = "влево" if rule.direction == "left" else "вправо"
        return f"циклически сдвинуть слова {direction} на {rule.shift} позиций."
    if rule.kind is RewriteRuleKind.SWAP_FIRST_LAST:
        return "если в предложении не меньше двух слов, поменять местами первое и последнее слово."
    if rule.kind is RewriteRuleKind.REMOVE_BY_POSITION:
        return f"удалить слова с {'чётными' if rule.position_type == 'even' else 'нечётными'} номерами; если слов не осталось, предложение не выводить."
    return "продублировать первое слово в конец предложения перед знаком препинания."


def _describe_keyword_rule(rule: KeywordRule) -> str:
    if rule.kind is KeywordRuleKind.FIRST_LONGEST:
        return "выбрать первое самое длинное слово."
    if rule.kind is KeywordRuleKind.LAST_SHORTEST:
        return "выбрать последнее самое короткое слово."
    if rule.kind is KeywordRuleKind.MAX_VOWELS:
        return "выбрать слово с наибольшим числом гласных; при равенстве взять первое."
    return f"выбрать слово с номером {rule.position}, а если его нет, то последнее слово предложения."


def cut_text_to_marker(text: str, marker: str) -> str:
    index = text.find(marker)
    return text[:index] if index >= 0 else text


def split_sentences(text: str, limits: Limits) -> list[Sentence]:
    prepared_text = cut_text_to_marker(text, limits.text_end_marker)
    if len(prepared_text) > limits.text_max:
        prepared_text = prepared_text[: limits.text_max]

    sentences: list[Sentence] = []
    start = 0
    for index, symbol in enumerate(prepared_text):
        if symbol not in limits.sentence_endings:
            continue
        raw = prepared_text[start: index + 1]
        start = index + 1
        normalized = raw.lstrip(" \t")
        if not normalized:
            continue
        content = normalized[:-1]
        sentences.append(
            Sentence(
                index=len(sentences) + 1,
                raw=raw,
                normalized=normalized,
                ending=normalized[-1],
                words=tuple(content.split()),
            )
        )
        if len(sentences) >= limits.sentence_max:
            break
    return sentences


def count_digits(sentence: Sentence) -> int:
    return sum(symbol.isdigit() for symbol in sentence.normalized)


def apply_select_rule(sentence: Sentence, rule: SelectRule) -> bool:
    if rule.kind is SelectRuleKind.WORD_COUNT:
        return COMPARISONS[str(rule.comparison)](len(sentence.words), int(rule.threshold))
    if rule.kind is SelectRuleKind.ENDING_PUNCT:
        return sentence.ending in set(rule.endings or ())
    if rule.kind is SelectRuleKind.WORD_LENGTH:
        return any(len(word) >= int(rule.threshold or 0) for word in sentence.words)
    if rule.kind is SelectRuleKind.DIGIT_COUNT:
        return count_digits(sentence) >= int(rule.threshold or 0)
    return sentence.index % 2 == (0 if rule.position_type == "even" else 1)


def cyclic_shift(words: list[str], shift: int, direction: str) -> list[str]:
    if not words:
        return []
    step = shift % len(words)
    if step == 0:
        return words[:]
    if direction == "left":
        return words[step:] + words[:step]
    return words[-step:] + words[:-step]


def apply_rewrite_rule(sentence: Sentence, rule: RewriteRule) -> list[str]:
    words = list(sentence.words)
    if rule.kind is RewriteRuleKind.REVERSE_WORDS:
        return list(reversed(words))
    if rule.kind is RewriteRuleKind.CYCLIC_SHIFT:
        return cyclic_shift(words, int(rule.shift or 0), str(rule.direction or "left"))
    if rule.kind is RewriteRuleKind.SWAP_FIRST_LAST:
        if len(words) >= 2:
            words[0], words[-1] = words[-1], words[0]
        return words
    if rule.kind is RewriteRuleKind.REMOVE_BY_POSITION:
        kept_words: list[str] = []
        remove_even = rule.position_type == "even"
        for index, word in enumerate(words, start=1):
            if remove_even and index % 2 == 1:
                kept_words.append(word)
            if not remove_even and index % 2 == 0:
                kept_words.append(word)
        return kept_words
    if words:
        words.append(words[0])
    return words


def count_vowels(word: str) -> int:
    return sum(symbol in DEFAULT_VOWELS for symbol in word)


def choose_keyword(words: list[str], rule: KeywordRule) -> str:
    if not words:
        raise ValueError("Cannot choose keyword from empty sentence")

    if rule.kind is KeywordRuleKind.FIRST_LONGEST:
        max_length = max(len(word) for word in words)
        for word in words:
            if len(word) == max_length:
                return word

    if rule.kind is KeywordRuleKind.LAST_SHORTEST:
        min_length = min(len(word) for word in words)
        for word in reversed(words):
            if len(word) == min_length:
                return word

    if rule.kind is KeywordRuleKind.MAX_VOWELS:
        max_count = max(count_vowels(word) for word in words)
        for word in words:
            if count_vowels(word) == max_count:
                return word

    if rule.kind is KeywordRuleKind.BY_POSITION:
        position = int(rule.position or 1)
        return words[position - 1] if position <= len(words) else words[-1]

    raise ValueError(f"Unsupported keyword rule kind: {rule.kind}")


def render_sentence(words: Iterable[str], ending: str) -> str:
    prepared_words = list(words)
    return f"{' '.join(prepared_words)}{ending}" if prepared_words else ""


def solve_text(text: str, variant: Variant) -> SolveResult:
    transformed_sentences: list[str] = []
    keywords: list[str] = []

    for sentence in split_sentences(text, variant.limits):
        if not apply_select_rule(sentence, variant.select_rule):
            continue
        transformed_words = apply_rewrite_rule(sentence, variant.rewrite_rule)
        if not transformed_words:
            continue
        transformed_sentences.append(render_sentence(transformed_words, sentence.ending))
        keywords.append(choose_keyword(transformed_words, variant.keyword_rule))

    return SolveResult(transformed_sentences=transformed_sentences, keywords=keywords)


def normalize_output(text: str) -> str:
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def _build_test_case(
    variant: Variant,
    input_text: str,
    test_id: str,
    *,
    expect_empty: bool,
) -> dict[str, Any]:
    result = solve_text(input_text, variant)
    rendered_output = result.render_output()
    is_empty = not result.transformed_sentences
    if is_empty != expect_empty:
        expected_kind = "EMPTY" if expect_empty else "non-EMPTY"
        actual_kind = "EMPTY" if is_empty else "non-EMPTY"
        raise RuntimeError(
            f"Generated lab3 test '{test_id}' is {actual_kind}, expected {expected_kind}."
        )
    return {
        "input_text": input_text,
        "stdin": input_text,
        "expected_stdout": rendered_output + "\n",
        "test_id": test_id,
    }


def _faker_words(rng: Any, faker: Any, count: int, max_length: int) -> list[str]:
    raw_words = list(faker.words(nb=count))
    words: list[str] = []
    for index in range(count):
        fallback = f"word{index + 1}{rand_int(rng, 10, 99)}"
        word = str(raw_words[index]) if index < len(raw_words) else fallback
        word = "".join(symbol for symbol in word if not symbol.isspace())
        words.append((word or fallback)[:max_length])
    return words


def _positive_word_count(variant: Variant) -> int:
    if variant.select_rule.kind is SelectRuleKind.WORD_COUNT:
        word_count = _find_positive_word_count(variant.select_rule, variant.rewrite_rule)
        if word_count is None:
            raise RuntimeError(
                f"Cannot generate a non-EMPTY test for select rule: {variant.select_rule}"
            )
        return word_count
    return max(3, _minimum_word_count_surviving_rewrite(variant.rewrite_rule))


def _word_count_for_digit_rule(variant: Variant, base_count: int) -> int:
    if variant.select_rule.kind is not SelectRuleKind.DIGIT_COUNT:
        return base_count
    max_word_length = max(1, variant.limits.word_max)
    required_digits = int(variant.select_rule.threshold or 1)
    count = max(base_count, (required_digits + max_word_length - 1) // max_word_length)
    while not _word_count_survives_rewrite(count, variant.rewrite_rule):
        count += 1
    return count


def _apply_select_rule_payload(words: list[str], variant: Variant) -> None:
    rule = variant.select_rule
    max_word_length = max(1, variant.limits.word_max)

    if rule.kind is SelectRuleKind.WORD_LENGTH:
        threshold = int(rule.threshold or 1)
        words[0] = "x" * threshold
        return

    if rule.kind is SelectRuleKind.DIGIT_COUNT:
        required_digits = int(rule.threshold or 1)
        remaining_digits = required_digits
        for index in range(len(words)):
            if remaining_digits <= 0:
                break
            digit_count = min(max_word_length, remaining_digits)
            words[index] = "".join(str((index + offset) % 10) for offset in range(digit_count))
            remaining_digits -= digit_count


def _positive_sentence_ending(variant: Variant, rng: Any) -> str:
    rule = variant.select_rule
    if rule.kind is SelectRuleKind.ENDING_PUNCT:
        return rand_choice(rng, tuple(rule.endings or tuple(variant.limits.sentence_endings)))
    return rand_choice(rng, tuple(variant.limits.sentence_endings))


def _render_generated_sentence(words: list[str], ending: str, rng: Any) -> str:
    leading_whitespace = rand_choice(rng, ("", " ", "\t", " \t"))
    return f"{leading_whitespace}{' '.join(words)}{ending}"


def _build_positive_sentence(variant: Variant, rng: Any, faker: Any) -> str:
    word_count = _word_count_for_digit_rule(variant, _positive_word_count(variant))
    max_word_length = max(1, variant.limits.word_max)
    words = _faker_words(rng, faker, word_count, max_word_length)
    _apply_select_rule_payload(words, variant)
    return _render_generated_sentence(words, _positive_sentence_ending(variant, rng), rng)


def generate_positive_input(variant: Variant, rng: Any, faker: Any, *, index: int) -> str:
    sentences: list[str] = []
    if variant.select_rule.kind is SelectRuleKind.POSITION and variant.select_rule.position_type == "even":
        noise_words = _faker_words(rng, faker, 3, max(1, variant.limits.word_max))
        noise_ending = rand_choice(rng, tuple(variant.limits.sentence_endings))
        sentences.append(_render_generated_sentence(noise_words, noise_ending, rng))

    sentences.append(_build_positive_sentence(variant, rng, faker))

    if index % 3 == 0 and variant.select_rule.kind is not SelectRuleKind.POSITION:
        sentences.append(_build_positive_sentence(variant, rng, faker))

    return f"{' '.join(sentences)} {variant.limits.text_end_marker}"


def generate_random_input(rng: Any, limits: Limits, faker: Any) -> str:
    return faker_text(
        rng,
        faker=faker,
        sentence_count_min=3,
        sentence_count_max=7,
        word_count_min=1,
        word_count_max=7,
        endings=tuple(limits.sentence_endings),
        max_word_length=limits.word_max,
        marker=limits.text_end_marker,
    )
