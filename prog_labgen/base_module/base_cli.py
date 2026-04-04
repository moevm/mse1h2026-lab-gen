import argparse
from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class CLIParser:
    name: str
    add_cli_args: Callable[[argparse.ArgumentParser], None]


def int_at_least(minimum: int, option_name: str) -> Callable[[str], int]:
    def _parse(value: str) -> int:
        parsed = int(value)
        if parsed < minimum:
            raise argparse.ArgumentTypeError(
                f"{option_name} must be greater than or equal to {minimum}."
            )
        return parsed

    return _parse


def add_common_cli_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--seed",
        type=str,
        required=True,
        help="Seed string used for deterministic variant generation.",
    )
    parser.add_argument("--solution", type=str, default="solution.c")
    parser.add_argument(
        "--mode",
        type=str,
        choices=("init", "check", "dry-run"),
        default="init",
        help="Execution mode: render assignment, check solution, or print assignment with generated tests.",
    )
    parser.add_argument("--all-tests", action="store_true", help="Do not stop after the first failed test.")
    parser.add_argument("--cc", type=str, default=None, help="Path or name of the C compiler.")


def get_common_cli_args(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "seed": args.seed,
        "fail_on_first_test": not args.all_tests,
        "compiler": args.cc,
    }
