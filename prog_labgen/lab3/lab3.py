from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
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
