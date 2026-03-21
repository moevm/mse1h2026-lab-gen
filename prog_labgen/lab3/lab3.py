from __future__ import annotations

import shutil
from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable

from prog_labgen.base_module import BaseTask

DEFAULT_SENTENCE_ENDINGS = ".;?!"
DEFAULT_VOWELS = set("aeiouyAEIOUY")
FIXED_TEST_INPUTS: tuple[str, ...] = (
    "Small fox runs. Brilliant minds grow fast! Tiny digits stay? Northern mountains shimmer brightly. ###",
    "  One two three.\t\t444 mark here! Empty 1? ### trailing text is ignored.",
    "Alpha beta gamma delta; Seven 77 seas? lone! ###",
    "\t\tSingle. Double word! 12345 digits and numbers 7? ###",
    "Keep calm and code. Remove every second word maybe! Echo echo echo? ###",
)
WORD_POOL: tuple[str, ...] = (
    "alpha", "beta", "gamma", "delta", "omega", "vector", "matrix", "cipher",
    "orbit", "signal", "planet", "rocket", "forest", "river", "silver", "bright",
    "northern", "violet", "quantum", "whisper", "crystal", "autumn", "python", "kernel",
)
DIGIT_WORD_POOL: tuple[str, ...] = ("x1", "m2", "n33", "p444", "z5555", "a7b8")


@dataclass(frozen=True)
class Limits:
    text_max: int = 10000
    sentence_max: int = 200
    word_max: int = 64
    sentence_endings = DEFAULT_SENTENCE_ENDINGS
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
    student: str
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
            student: str,
            text_max: int = 10000,
            sentence_max: int = 200,
            word_max: int = 64,
            tests_count: int = 10,
            fail_on_first_test: bool = True,
            compiler: str | None = None
    ) -> None:
        super().__init__(student=student, fail_on_first_test=fail_on_first_test, compiler=compiler)
        self.limits = Limits(
            text_max=text_max,
            sentence_max=sentence_max,
            word_max=word_max,
        )
        self.test_count = max(1, tests_count)
        self._variant: Variant | None = None

    def _build_variant(self) -> Variant:
        if self._variant is not None:
            return self._variant

        rng = self.make_random()
        select_kind = rng.choice(list(SelectRuleKind))
        rewrite_kind = rng.choice(list(RewriteRuleKind))
        keyword_kind = rng.choice(list(KeywordRuleKind))

        self._variant = Variant(
            student=self.student,
            seed_hash=self.make_seed_hash(),
            select_rule=_generate_select_rule(select_kind, rng, self.limits),
            rewrite_rule=_generate_rewrite_rule(rewrite_kind, rng),
            keyword_rule=_generate_keyword_rule(keyword_kind, rng),
            limits=self.limits,
        )
        return self._variant

    def render_assignment(self) -> str:
        variant = self._build_variant()
        lines = [
            "Концепция варианта ЛР3",
            f"Студент: {variant.student}",
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
        for index, input_text in enumerate(FIXED_TEST_INPUTS[: self.tests_count], start=1):
            tests.append(
                {
                    "input_text": input_text,
                    "stdin": input_text,
                    "expected_stdout": solve_text(input_text, variant).render_output() + "\n",
                    "test_id": f"fixed_{index}",
                }
            )
        rng = self.make_random()
        while len(tests) < self.tests_count:
            input_text = generate_random_input(rng, self.limits)
            test_index = len(tests) - len(FIXED_TEST_INPUTS) + 1
            tests.append(
                {
                    "input_text": input_text,
                    "stdin": input_text,
                    "expected_stdout": solve_text(input_text, variant).render_output() + "\n",
                    "test_id": f"random_{test_index}",
                }
            )

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
            comparison=rng.choice(tuple(COMPARISONS.keys())),
            threshold=rng.randint(1, min(12, max(1, limits.word_max))),
        )
    if kind is SelectRuleKind.ENDING_PUNCT:
        endings = [symbol for symbol in limits.sentence_endings if rng.choice((True, False))]
        if not endings:
            endings = [rng.choice(tuple(limits.sentence_endings))]
        return SelectRule(kind=kind, endings=tuple(sorted(endings)))
    if kind is SelectRuleKind.WORD_LENGTH:
        return SelectRule(kind=kind, threshold=rng.randint(1, min(12, max(1, limits.word_max))))
    if kind is SelectRuleKind.DIGIT_COUNT:
        return SelectRule(kind=kind, threshold=rng.randint(1, 8))
    if kind is SelectRuleKind.POSITION:
        return SelectRule(kind=kind, position_type=rng.choice(("even", "odd")))
    raise ValueError(f"Unsupported select rule kind: {kind}")


def _generate_rewrite_rule(kind: RewriteRuleKind, rng: Any) -> RewriteRule:
    if kind is RewriteRuleKind.REVERSE_WORDS:
        return RewriteRule(kind=kind)
    if kind is RewriteRuleKind.CYCLIC_SHIFT:
        return RewriteRule(kind=kind, direction=rng.choice(("left", "right")), shift=rng.randint(1, 5))
    if kind is RewriteRuleKind.SWAP_FIRST_LAST:
        return RewriteRule(kind=kind)
    if kind is RewriteRuleKind.REMOVE_BY_POSITION:
        return RewriteRule(kind=kind, position_type=rng.choice(("even", "odd")))
    if kind is RewriteRuleKind.DUPLICATE_FIRST:
        return RewriteRule(kind=kind)
    raise ValueError(f"Unsupported rewrite rule kind: {kind}")


def _generate_keyword_rule(kind: KeywordRuleKind, rng: Any) -> KeywordRule:
    if kind is KeywordRuleKind.BY_POSITION:
        return KeywordRule(kind=kind, position=rng.randint(1, 5))
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
        return "выбрать самое длинное слово."
    if rule.kind is KeywordRuleKind.LAST_SHORTEST:
        return "выбрать последнее самое короткое слово."
    if rule.kind is KeywordRuleKind.MAX_VOWELS:
        return "выбрать слово с наибольшим числом гласных; при равенстве взять первое."
    return f"выбрать слово с номером {rule.position}, а если его нет, то последнее слово предложения."


def cut_text_to_marker(text: str, marker: str) -> str:
    index = text.find(marker)
    return text[:index] if index > 0 else text


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


def generate_random_input(rng: Any, limits: Limits) -> str:
    sentence_count = rng.randint(3, 7)
    sentences: list[str] = []

    for _ in range(sentence_count):
        word_count = rng.randint(1, 7)
        words: list[str] = []
        for _ in range(word_count):
            source = DIGIT_WORD_POOL if rng.random() < 0.25 else WORD_POOL
            word = rng.choice(source)
            words.append(word[: limits.word_max])
        prefix = rng.choice(("", " ", "\t", " \t"))
        ending = rng.choice(tuple(limits.sentence_endings))
        sentences.append(prefix + " ".join(words) + ending)

    return " ".join(sentences) + " ###"
