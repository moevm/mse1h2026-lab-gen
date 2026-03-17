import argparse
from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class CLIParser:
    name: str
    add_cli_args: Callable[[argparse.ArgumentParser], None]


def add_common_cli_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--student", type=str, required=True)
    parser.add_argument("--solution", type=str)
    parser.add_argument(
        "--mode",
        type=str,
        choices=("init", "check", "dry-run"),
        default="init",
    )
    parser.add_argument("--all-tests", action="store_true")
    parser.add_argument("--cc", type=str, default=None)


def get_common_cli_args(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "student": args.student,
        "fail_on_first_test": not args.all_tests,
        "compiler": args.cc,
    }
