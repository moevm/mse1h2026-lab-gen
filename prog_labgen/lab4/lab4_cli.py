import argparse

from .lab4 import Lab4Task
from prog_labgen.base_module import (
    CLIParser,
    add_common_cli_args,
    get_common_cli_args,
    int_at_least
)


def create_lab4_task(args: argparse.Namespace) -> Lab4Task:
    return Lab4Task(
        line_max=args.line_max,
        element_max=args.element_max,
        word_max=args.word_max,
        tests_count=args.tests_count,
        **get_common_cli_args(args),
    )


def add_lab4_cli_args(parser: argparse.ArgumentParser) -> None:
    add_common_cli_args(parser)
    parser.add_argument(
        "--line-max",
        type=int_at_least(10, "--line_max"),
        default=10000,
        help="Максимальная длина исходной строки (LineMax).",
    )
    parser.add_argument(
        "--element-max",
        type=int_at_least(1, "--element-max"),
        default=200,
        help="Максимальное количество элементов (ElementMax).",
    )
    parser.add_argument(
        "--word-max",
        type=int_at_least(3, "--word-max"),
        default=64,
        help="Максимальная длина одного элемента (WordMax).",
    )
    parser.add_argument(
        "--tests-count",
        type=int_at_least(1, "--tests-count"),
        default=10,
        help="Количество генерируемых тестов.",
    )
    parser.set_defaults(func=create_lab4_task)


Lab4CLIParser = CLIParser(
    name="lab4",
    add_cli_args=add_lab4_cli_args,
)