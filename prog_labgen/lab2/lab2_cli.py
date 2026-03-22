import argparse
from prog_labgen.base_module import CLIParser, add_common_cli_args, get_common_cli_args

from prog_labgen.lab2.lab2 import Lab2Task

import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning, module="runpy")

def create_lab2_task(args: argparse.Namespace) -> Lab2Task:
    return Lab2Task(
        Nmax=args.Nmax,
        K=args.K,
        **get_common_cli_args(args),
    )


def add_lab2_cli_args(parser: argparse.ArgumentParser) -> None:
    add_common_cli_args(parser)
    parser.add_argument("--Nmax", type=int, default=100, help="Максимальный размер массива")
    parser.add_argument("--K", type=int, default=3, help="Количество core‑функций")
    parser.set_defaults(func=create_lab2_task)


Lab2CLIParser = CLIParser(
    name="lab2",
    add_cli_args=add_lab2_cli_args,
)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    Lab2CLIParser.add_cli_args(parser)
    args = parser.parse_args()
    task = args.func(args)

    if args.mode == "init":
        print(task.render_assignment())
    elif args.mode == "dry-run":
        import json
        print(json.dumps(
            {"assignment": task.render_assignment(), "tests": task.generate_tests()},
            ensure_ascii=False, indent=2,
        ))
    elif args.mode == "check":
        ok, msg = task.check(args.solution)
        print("OK" if ok else "FAIL")
        print(msg)