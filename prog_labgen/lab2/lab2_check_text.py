import argparse
import shutil
import sys
from pathlib import Path

from prog_labgen.lab2.lab2 import Lab2Task
from prog_labgen.lab2.lab2_parser import parse_student_solution_blob, write_solution_to_dir


def check_from_text_blob(
    blob_text: str,
    Nmax: int = 100,
    K: int = 3,
    student: str = "ab12",
    fail_on_first_test: bool = True,
    keep_temp: bool = False,
) -> None:
    entries = parse_student_solution_blob(blob_text)

    debug_dir = Path("/home/chesluchilos/mse1h2026-lab-gen/debug_student_solution")
    
    if debug_dir.exists() and not keep_temp:
        shutil.rmtree(debug_dir)
    
    debug_dir.mkdir(exist_ok=True, parents=True)

    write_solution_to_dir(entries, debug_dir)

    task = Lab2Task(
        student=student,
        Nmax=Nmax,
        K=K,
        fail_on_first_test=fail_on_first_test,
    )

    ok, msg = task.check(solution_path=debug_dir)
    print("OK" if ok else "FAIL")
    print(msg)
    
    if not keep_temp and debug_dir.exists():
        shutil.rmtree(debug_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="lab2_check_text",
        description="Проверить решение студента из текст‑полотна.",
    )
    parser.add_argument("--blob-file", required=True, help="Файл с текст‑полотном студента.")
    parser.add_argument("--Nmax", type=int, default=100, help="Максимальный размер массива.")
    parser.add_argument("--K", type=int, default=3, help="Количество core‑функций.")
    parser.add_argument("--student", default="ab12", help="Имя студента для генерации варианта.")
    parser.add_argument("--all-tests", action="store_true", help="Не останавливаться на первой ошибке.")
    parser.add_argument("--keep-temp", action="store_true", help="Оставить временные файлы для отладки.")

    args = parser.parse_args()

    blob = Path(args.blob_file).read_text(encoding="utf-8", errors="replace")

    check_from_text_blob(
        blob_text=blob,
        Nmax=args.Nmax,
        K=args.K,
        student=args.student,
        fail_on_first_test=not args.all_tests,
        keep_temp=args.keep_temp,
    )