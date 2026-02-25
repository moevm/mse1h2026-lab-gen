import importlib.util
import sys

from typing import List, Dict, Any
from pprint import pprint


def check_solution(student_file: str, tests: List[Dict[str, Any]]) -> None:
    """
    Проверяет студенческое решение и выводит результат.
    
    Аргументы:
        student_file: путь к .py файлу студента
        tests: тестовые данные из generate_tests
    """
    # Загружаем модуль студента
    spec = importlib.util.spec_from_file_location("student_module", student_file)
    module = importlib.util.module_from_spec(spec)
    sys.modules["student_module"] = module
    spec.loader.exec_module(module)
    
    total_tests = 0
    passed = 0
    pprint(tests)
    
    for task_data in tests:
        task_name = task_data["название первой функции"]
        task_params = task_data["значение параметра функции"]
        
        # Получаем функцию студента
        if not hasattr(module, task_name):
            print(f"Функция {task_name} не найдена!")
            continue
        
        student_func = getattr(module, task_name)
        
        print(f"\n\tПроверка задачи: {task_name}")
        
        for i, test in enumerate(task_data["тесты"], 1):
            arr = test["значение теста"]
            expected = test["ожидаемое значение"]
            
            # Вызываем функцию студента
            if isinstance(task_params, dict):
                # Для задач с несколькими параметрами
                result = student_func(arr, *task_params.values())
            else:
                # Для задач с одним параметром
                result = student_func(arr, task_params)
            
            total_tests += 1
            if result == expected:
                print(f"\tТест {i}: OK")
                passed += 1
            else:
                print(f"\tТест {i}: FAIL")
                print(f"\tВход: {arr}")
                print(f"\tПараметры: {task_params}")
                print(f"\tОжидалось: {expected}, Получено: {result}")
    
    print(f"\n{'='*40}")
    print(f"ИТОГ: {passed}/{total_tests} тестов пройдено")
    print(f"{'ВСЕ ТЕСТЫ ПРОЙДЕНЫ' if passed == total_tests else 'ЕСТЬ ОШИБКИ'}")



if __name__ == "__main__":
    from generate_params import generate_params
    from generate_tests_from_config import generate_tests
    cfg = generate_params(seed="student123", N_max=15, sep=",", K=3)
    tests = generate_tests(cfg, tests_per_task=5)

    check_solution("solution.py", tests)