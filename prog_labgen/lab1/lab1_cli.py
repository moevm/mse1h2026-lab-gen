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
    if args.base_min > args.base_max:
        parser.error("--base-min must be less than or equal to --base-max for lab1.")
    if args.random_base and args.n_max < 6:
        parser.error("--n-max must be at least 6 for lab1 random-base mode.")

    common_args = get_common_cli_args(args)
    return Lab1Task(
        seed=args.seed,
        n_max=args.n_max,
        sep=args.sep,
        k=args.k,
        tests_per_task=args.tests_per_task,
        random_base=args.random_base,
        base_min=args.base_min,
        base_max=args.base_max,
        fail_on_first_test=common_args["fail_on_first_test"],
        compiler=common_args["compiler"],
    )


def add_lab1_cli_args(parser: argparse.ArgumentParser) -> None:
    add_common_cli_args(parser)
    parser.add_argument("--n-max", type=int_at_least(1, "--n-max"), default=100, help="Maximum array size.")
    parser.add_argument("--sep", type=str, default=" ", help="Input separator used in generated local tests.")
    parser.add_argument("--k", type=int_at_least(1, "--k"), default=3, help="Number of assigned subtasks.")
    parser.add_argument(
        "--random-base",
        action="store_true",
        help="Use a seed-dependent numeral system base for input numbers and output results.",
    )
    parser.add_argument(
        "--base-min",
        type=int_at_least(2, "--base-min"),
        default=10,
        help="Minimum numeral system base used with --random-base.",
    )
    parser.add_argument(
        "--base-max",
        type=int_at_least(2, "--base-max"),
        default=10,
        help="Maximum numeral system base used with --random-base.",
    )
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