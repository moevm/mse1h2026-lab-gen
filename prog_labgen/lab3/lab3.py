from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from prog_labgen.base_module import BaseTask

DEFAULT_SENTENCE_ENDINGS = ".;?!"
DEFAULT_VOWELS = set("aeiouyAEIOUY")


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