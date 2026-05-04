from __future__ import annotations

import random
from typing import Any, Iterable, Sequence

SUFFIX_ALPHABET = "abcdefghijklmnopqrstuvwxyz0123456789"
COMPARISON_OPERATORS: tuple[str, ...] = ("<", "<=", "==", ">=", ">")
POSITION_TYPES: tuple[str, ...] = ("even", "odd")
DIRECTIONS: tuple[str, ...] = ("left", "right")
LEADING_WHITESPACE_CHOICES: tuple[str, ...] = ("", " ", "\t", " \t")


def rand_int(rng: random.Random, minimum: int, maximum: int) -> int:
    return rng.randint(minimum, maximum)


def rand_choice(rng: random.Random, values: Sequence[Any]) -> Any:
    return rng.choice(values)


def rand_bool(rng: random.Random, probability: float = 0.5) -> bool:
    return rng.random() < probability


def rand_sample(rng: random.Random, values: Sequence[Any], k: int) -> list[Any]:
    return rng.sample(list(values), k)


def rand_partition_sizes(rng: random.Random, total: int, parts: int, minimum: int = 1) -> list[int]:
    if parts < 1:
        raise ValueError("parts must be greater than or equal to 1")
    if minimum < 0:
        raise ValueError("minimum must be greater than or equal to 0")
    if total < parts * minimum:
        raise ValueError("total is too small for the requested partition")

    sizes = [minimum] * parts
    remaining = total - parts * minimum
    for _ in range(remaining):
        sizes[rand_int(rng, 0, parts - 1)] += 1
    return sizes


def rand_suffix(
    rng: random.Random,
    length: int = 3,
    alphabet: str = SUFFIX_ALPHABET,
) -> str:
    return "".join(rand_choice(rng, alphabet) for _ in range(length))


def rand_identifier_suffix(
    rng: random.Random,
    length: int = 3,
    alphabet: str = SUFFIX_ALPHABET,
) -> str:
    return rand_suffix(rng, length=length, alphabet=alphabet)


def rand_name(
    rng: random.Random,
    prefix: str,
    *,
    length: int = 3,
    suffix: str = "",
    alphabet: str = SUFFIX_ALPHABET,
) -> str:
    return f"{prefix}{rand_suffix(rng, length=length, alphabet=alphabet)}{suffix}"


def rand_int_array(
    rng: random.Random,
    size_min: int,
    size_max: int,
    value_min: int,
    value_max: int,
) -> list[int]:
    size = rand_int(rng, size_min, size_max)
    return [rand_int(rng, value_min, value_max) for _ in range(size)]


def rand_comparison(rng: random.Random, values: Sequence[str] = COMPARISON_OPERATORS) -> str:
    return rand_choice(rng, values)


def rand_position_type(rng: random.Random, values: Sequence[str] = POSITION_TYPES) -> str:
    return rand_choice(rng, values)


def rand_direction(rng: random.Random, values: Sequence[str] = DIRECTIONS) -> str:
    return rand_choice(rng, values)


def rand_end_punctuation(rng: random.Random, allowed: Sequence[str]) -> str:
    return rand_choice(rng, allowed)


def with_leading_whitespace(
    text: str,
    rng: random.Random,
    choices: Sequence[str] = LEADING_WHITESPACE_CHOICES,
) -> str:
    return f"{rand_choice(rng, choices)}{text}"


def pool_words(
    rng: random.Random,
    pool: Sequence[str],
    *,
    count_min: int,
    count_max: int,
    max_length: int | None = None,
) -> list[str]:
    count = rand_int(rng, count_min, count_max)
    words = [rand_choice(rng, pool) for _ in range(count)]
    if max_length is None:
        return words
    return [word[:max_length] for word in words]


def mixed_pool_words(
    rng: random.Random,
    primary_pool: Sequence[str],
    secondary_pool: Sequence[str],
    *,
    secondary_probability: float,
    count_min: int,
    count_max: int,
    max_length: int | None = None,
) -> list[str]:
    count = rand_int(rng, count_min, count_max)
    words = [
        rand_choice(rng, secondary_pool if rand_bool(rng, secondary_probability) else primary_pool)
        for _ in range(count)
    ]
    if max_length is None:
        return words
    return [word[:max_length] for word in words]


def build_faker(seed: int):
    from faker import Faker

    faker = Faker()
    faker.seed_instance(seed)
    return faker


def faker_word_pool(
    *,
    faker,
    count: int,
    max_length: int | None = None,
) -> list[str]:
    words = list(faker.words(nb=count))
    if max_length is None:
        return words
    return [word[:max_length] for word in words]


def faker_words(
    rng: random.Random,
    *,
    faker,
    count_min: int,
    count_max: int,
    max_length: int | None = None,
) -> list[str]:
    count = rand_int(rng, count_min, count_max)
    words = list(faker.words(nb=count))
    if max_length is None:
        return words
    return [word[:max_length] for word in words]


def safe_faker_words(
    rng: random.Random,
    *,
    faker,
    count: int,
    max_length: int,
) -> list[str]:
    raw_words = list(faker.words(nb=count))
    words: list[str] = []
    for index in range(count):
        fallback = f"word{index + 1}{rand_int(rng, 10, 99)}"
        word = str(raw_words[index]) if index < len(raw_words) else fallback
        word = "".join(symbol for symbol in word if not symbol.isspace())
        words.append((word or fallback)[:max_length])
    return words


def faker_sentence(
    rng: random.Random,
    *,
    faker,
    word_count_min: int,
    word_count_max: int,
    endings: Sequence[str],
    max_word_length: int | None = None,
    leading_whitespace_choices: Sequence[str] = LEADING_WHITESPACE_CHOICES,
) -> str:
    words = faker_words(
        rng,
        faker=faker,
        count_min=word_count_min,
        count_max=word_count_max,
        max_length=max_word_length,
    )
    sentence = render_sentence(words, rand_end_punctuation(rng, endings))
    return with_leading_whitespace(sentence, rng, leading_whitespace_choices)


def faker_text(
    rng: random.Random,
    *,
    faker,
    sentence_count_min: int,
    sentence_count_max: int,
    word_count_min: int,
    word_count_max: int,
    endings: Sequence[str],
    separator: str = " ",
    max_word_length: int | None = None,
    marker: str | None = None,
    leading_whitespace_choices: Sequence[str] = LEADING_WHITESPACE_CHOICES,
) -> str:
    sentence_count = rand_int(rng, sentence_count_min, sentence_count_max)
    sentences = [
        faker_sentence(
            rng,
            faker=faker,
            word_count_min=word_count_min,
            word_count_max=word_count_max,
            endings=endings,
            max_word_length=max_word_length,
            leading_whitespace_choices=leading_whitespace_choices,
        )
        for _ in range(sentence_count)
    ]
    text = join_sentences(sentences, separator=separator)
    if marker is None:
        return text
    return append_end_marker(text, marker=marker)


def join_sentences(sentences: Iterable[str], separator: str = " ") -> str:
    return separator.join(sentences)


def render_sentence(words: Sequence[str], ending: str, prefix: str = "") -> str:
    return prefix + " ".join(words) + ending


def append_end_marker(text: str, marker: str = "###") -> str:
    return f"{text} {marker}"


def append_marker(text: str, marker: str = "###") -> str:
    return append_end_marker(text, marker=marker)
