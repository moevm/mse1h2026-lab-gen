import argparse
import shutil
import tempfile
import warnings
from pathlib import Path

from prog_labgen.lab2.lab2 import Lab2Task
from prog_labgen.lab2.lab2_parser import parse_solution_blob, write_solution_to_dir

warnings.filterwarnings("ignore", category=RuntimeWarning, module="runpy")


def check_from_text_blob(
    blob_text: str,
    Nmax: int = 100,
    K: int = 3,
    seed: str = "ab12",
    fail_on_first_test: bool = True,
    keep_temp: bool = False,
) -> None:
    entries = parse_solution_blob(blob_text)

    if keep_temp:
        debug_dir = Path.cwd() / "debug_solution"
        if debug_dir.exists():
            shutil.rmtree(debug_dir)
    else:
        debug_dir = Path(tempfile.mkdtemp(prefix="lab2_check_"))

    debug_dir.mkdir(exist_ok=True, parents=True)
    write_solution_to_dir(entries, debug_dir)

    task = Lab2Task(
        seed=seed,
        Nmax=Nmax,
        K=K,
        fail_on_first_test=fail_on_first_test,
    )

    ok, msg = task.check(solution_path=str(debug_dir))
    print("OK" if ok else "FAIL")
    print(msg)

    if not keep_temp and debug_dir.exists():
        shutil.rmtree(debug_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="lab2_check_text",
        description="Проверить решение студента из текстового полотна.",
    )
    parser.add_argument("--blob-file", required=True, help="Файл с текстовым полотном студента.")
    parser.add_argument("--Nmax", type=int, default=100, help="Максимальный размер массива.")
    parser.add_argument("--K", type=int, default=3, help="Количество step-функций.")
    parser.add_argument("--seed", default="ab12", help="Seed string для генерации варианта.")
    parser.add_argument("--all-tests", action="store_true", help="Не останавливаться на первой ошибке.")
    parser.add_argument("--keep-temp", action="store_true", help="Оставить временные файлы для отладки.")

    args = parser.parse_args()
    blob = Path(args.blob_file).read_text(encoding="utf-8", errors="replace")

    check_from_text_blob(
        blob_text=blob,
        Nmax=args.Nmax,
        K=args.K,
        seed=args.seed,
        fail_on_first_test=not args.all_tests,
        keep_temp=args.keep_temp,
    )
