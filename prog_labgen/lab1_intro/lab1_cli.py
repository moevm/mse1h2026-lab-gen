import argparse

from prog_labgen.base_module import CLIParser, add_common_cli_args, get_common_cli_args

from .lab1_intro import Lab1Task


def create_lab1_task(args: argparse.Namespace) -> Lab1Task:
    return Lab1Task(
        n_max=args.n_max,
        sep=args.sep,
        k=args.k,
        tests_per_task=args.tests_per_task,
        **get_common_cli_args(args),
    )


def add_lab1_cli_args(parser: argparse.ArgumentParser) -> None:
    add_common_cli_args(parser)
    parser.add_argument("--n-max", type=int, default=100)
    parser.add_argument("--sep", type=str, default=" ")
    parser.add_argument("--k", type=int, default=3)
    parser.add_argument("--tests-per-task", type=int, default=5)
    parser.set_defaults(func=create_lab1_task)


Lab1CLIParser = CLIParser(
    name="lab1_intro",
    add_cli_args=add_lab1_cli_args,
)
