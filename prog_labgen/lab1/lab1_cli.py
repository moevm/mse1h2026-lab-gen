import argparse

from prog_labgen.base_module import (
    CLIParser,
    add_common_cli_args,
    get_common_cli_args,
    int_at_least,
)

from .lab1 import Lab1Task
from .lab1 import TASKS


def create_lab1_task(args: argparse.Namespace, parser: argparse.ArgumentParser) -> Lab1Task:
    if args.k > len(TASKS):
        parser.error(f"--k must be less than or equal to {len(TASKS)} for lab1.")

    common_args = get_common_cli_args(args)
    return Lab1Task(
        seed=args.seed,
        n_max=args.n_max,
        sep=args.sep,
        k=args.k,
        tests_per_task=args.tests_per_task,
        fail_on_first_test=common_args["fail_on_first_test"],
        compiler=common_args["compiler"],
    )


def add_lab1_cli_args(parser: argparse.ArgumentParser) -> None:
    add_common_cli_args(parser)
    parser.add_argument("--n-max", type=int_at_least(1, "--n-max"), default=100, help="Maximum array size.")
    parser.add_argument("--sep", type=str, default=" ", help="Input separator used in generated local tests.")
    parser.add_argument("--k", type=int_at_least(1, "--k"), default=3, help="Number of assigned subtasks.")
    parser.add_argument(
        "--tests-per-task",
        type=int_at_least(1, "--tests-per-task"),
        default=5,
        help="Number of generated tests for each variant.",
    )
    parser.set_defaults(func=lambda args, parser=parser: create_lab1_task(args, parser))


Lab1CLIParser = CLIParser(
    name="lab1",
    add_cli_args=add_lab1_cli_args,
)
