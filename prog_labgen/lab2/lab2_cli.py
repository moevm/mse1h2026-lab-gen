import argparse
import warnings
from pathlib import Path

from prog_labgen.base_module import CLIParser, add_common_cli_args, get_common_cli_args
from prog_labgen.lab2.lab2 import Lab2Task, check_from_text_blob

warnings.filterwarnings("ignore", category=RuntimeWarning, module="runpy")


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("значение должно быть целым числом") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("значение должно быть положительным целым числом")
    return parsed


def create_lab2_task(args: argparse.Namespace) -> Lab2Task:
    return Lab2Task(
        nmax=args.n_max,
        k=args.k,
        **get_common_cli_args(args),
    )


def add_lab2_cli_args(parser: argparse.ArgumentParser) -> None:
    add_common_cli_args(parser)
    parser.add_argument("--n-max", dest="n_max", type=positive_int, default=100, help="Максимальный размер массива")
    parser.add_argument("--k", type=positive_int, default=3, help="Количество step-функций")
    parser.add_argument("--blob-file", default=None, help="Файл с ответом студента для проверки в режиме check")
    parser.add_argument("--keep-temp", action="store_true", help="Оставить временные файлы после проверки --blob-file")
    parser.set_defaults(func=create_lab2_task)


Lab2CLIParser = CLIParser(
    name="lab2",
    add_cli_args=add_lab2_cli_args,
)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    Lab2CLIParser.add_cli_args(parser)
    args = parser.parse_args()
    try:
        task = args.func(args)
    except ValueError as exc:
        parser.error(str(exc))

    if args.mode == "init":
        print(task.render_assignment())
    elif args.mode == "dry-run":
        print(task.dry_run())
    elif args.mode == "check":
        if args.blob_file:
            blob = Path(args.blob_file).read_text(encoding="utf-8", errors="replace")
            check_from_text_blob(
                blob_text=blob,
                nmax=args.n_max,
                k=args.k,
                seed=args.seed,
                fail_on_first_test=not args.all_tests,
                keep_temp=args.keep_temp,
            )
        else:
            ok, msg = task.check(args.solution)
            print("OK" if ok else "FAIL")
            print(msg)
