import argparse

from prog_labgen.base_module import CLIParser, add_common_cli_args, get_common_cli_args, int_at_least
from .lab6 import Lab6Task


def create_lab6_task(args: argparse.Namespace) -> Lab6Task:
    return Lab6Task(
        tests_count=args.tests_count,
        **get_common_cli_args(args),
    )


def add_lab6_cli_args(parser: argparse.ArgumentParser) -> None:
    add_common_cli_args(parser)
    parser.add_argument("--tests-count", type=int_at_least(1, "--tests-count"), default=5)
    parser.set_defaults(func=create_lab6_task)


Lab6CLIParser = CLIParser(name="lab6", add_cli_args=add_lab6_cli_args)
