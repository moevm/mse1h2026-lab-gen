import argparse
import inspect
import sys

import prog_labgen


def configure_stdio() -> None:
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream is not None and hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def init_task(task) -> None:
    print(task.init_task())


def check_task(task, solution_path: str) -> None:
    passed, message = task.check(solution_path)
    print("Passed:", passed)
    print(message)
    sys.exit(0 if passed else 1)


def dry_run_task(task) -> None:
    print(task.dry_run())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Framework for generating and checking prog labs."
    )
    subparsers = parser.add_subparsers(dest="lab", required=True)

    for _, cli_parser in inspect.getmembers(
        prog_labgen, lambda obj: isinstance(obj, prog_labgen.CLIParser)
    ):
        lab_parser = subparsers.add_parser(cli_parser.name)
        cli_parser.add_cli_args(lab_parser)

    return parser


def main() -> None:
    configure_stdio()
    parser = build_parser()
    args = parser.parse_args()
    task = args.func(args)

    if args.mode == "init":
        init_task(task)
    elif args.mode == "check":
        check_task(task, args.solution)
    elif args.mode == "dry-run":
        dry_run_task(task)
    else:
        parser.error(f"Unsupported mode: {args.mode}")


if __name__ == "__main__":
    main()
