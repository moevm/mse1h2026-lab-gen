import argparse

from prog_labgen.base_module import CLIParser, add_common_cli_args, get_common_cli_args

from .lab3 import Lab3Task


def create_lab3_task(args: argparse.Namespace) -> Lab3Task:
    return Lab3Task(
        text_max=args.text_max,
        sentence_max=args.sentence_max,
        word_max=args.word_max,
        tests_count=args.tests_count,
        **get_common_cli_args(args),
    )


def add_lab3_cli_args(parser: argparse.ArgumentParser) -> None:
    add_common_cli_args(parser)
    parser.add_argument("--text-max", type=int, default=10_000)
    parser.add_argument("--sentence-max", type=int, default=200)
    parser.add_argument("--word-max", type=int, default=64)
    parser.add_argument("--tests-count", type=int, default=10)
    parser.set_defaults(func=create_lab3_task)


Lab3CLIParser = CLIParser(
    name="lab3",
    add_cli_args=add_lab3_cli_args,
)
