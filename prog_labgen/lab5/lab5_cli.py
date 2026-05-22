import argparse

from prog_labgen.base_module import CLIParser, add_common_cli_args, get_common_cli_args, int_at_least

from .lab5 import Lab5Task


def create_lab5_task(args: argparse.Namespace) -> Lab5Task:
    return Lab5Task(
        tests_count=args.tests_count,
        records_per_test=args.records_per_test,
        filters_count=args.filters_count,
        **get_common_cli_args(args),
    )


def add_lab5_cli_args(parser: argparse.ArgumentParser) -> None:
    add_common_cli_args(parser)
    parser.add_argument(
        "--tests-count",
        type=int_at_least(1, "--tests-count"),
        default=10,
        help="Количество генерируемых тестов.",
    )
    parser.add_argument(
        "--records-per-test",
        type=int_at_least(3, "--records-per-test"),
        default=14,
        help="Примерное количество строк во входных тестах.",
    )
    parser.add_argument(
        "--filters-count",
        type=int_at_least(1, "--filters-count"),
        default=2,
        help="Количество условий фильтрации этапа 2.",
    )
    parser.set_defaults(func=create_lab5_task)


Lab5CLIParser = CLIParser(
    name="lab5",
    add_cli_args=add_lab5_cli_args,
)
