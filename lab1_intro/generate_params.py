import random
import hashlib

from typing import Dict, List

from solve_tasks import first_multiple_index, last_abs_gt_index, count_in_range, sum_abs_step, sum_divisible, \
    count_abs_lt

# Подзадачи и соответствующие им параметры
TASKS_INFO = {
    1: {"name": "ans_first_multiple_index", "func": first_multiple_index, "params": ["M"]},
    2: {"name": "ans_last_abs_gt_index", "func": last_abs_gt_index, "params": ["T"]},
    3: {"name": "ans_count_in_range", "func": count_in_range, "params": ["A", "B"]},
    4: {"name": "ans_sum_abs_step", "func": sum_abs_step, "params": ["P", "K_step"]},
    5: {"name": "ans_sum_divisible", "func": sum_divisible, "params": ["D"]},
    6: {"name": "ans_count_abs_lt", "func": count_abs_lt, "params": ["L"]},
}


class Config:
    """
    Класс-конфигурация

    Содержит:
        params - словарь из параметров вида "имя-числовое значение"
        sep - разделитель чисел в строке
        tasks - список выбранных подзадач (K штук)
    """

    def __init__(self) -> None:
        self._params: Dict[str, int] = {}
        self._sep: str = " "
        self._tasks: List[int] = []

    def get_param(self, key: str, default: int = 0) -> int:
        return self._params.get(key, default)

    def set_param(self, key: str, value: int) -> None:
        self._params[key] = value

    def get_sep(self) -> str:
        return self._sep

    def set_sep(self, value: str) -> None:
        self._sep = value

    def get_tasks(self) -> List[int]:
        return self._tasks

    def set_tasks(self, value: List[int]):
        self._tasks = value


def generate_params(seed: str, N_max: int = 100, sep: str = ',', K: int = 3) -> Config:
    """
    Генерирует конфигурацию для студента на основе seed.
    
    Аргументы:
        seed: строка-идентификатор студента
        N_max: максимальный размер массива
        sep: разделитель чисел
        K: количество подзадач
    
    Возвращает:
        Config: объект конфигурации с параметрами и задачами
    """

    config = Config()
    config.set_param("N_max", N_max)
    config.set_sep(sep)
    config.set_param("K", K)

    # Инициализируем генератор случайных чисел на основе seed
    # Используем хеш от seed для детерминированности
    seed_hash = int(hashlib.md5(seed.encode()).hexdigest(), 16)
    rnd = random.Random(seed_hash)

    config.set_param("seed_hash", seed_hash)

    # Генерируем список подзадач
    all_tasks = list(range(1, 7))
    selected_tasks = rnd.sample(all_tasks, K)
    config.set_tasks(selected_tasks)

    # Генерируем параметры для каждой подзадачи
    params_dict = {}
    for task_num in selected_tasks:
        task_info = TASKS_INFO[task_num]

        for param_name in task_info["params"]:
            # Разные параметры имеют разные диапазоны значений
            if param_name in ["M", "D", "L", "T", "P"]:  # Делители, пороги и т.д.
                params_dict[param_name] = rnd.randint(2, 15)
            elif param_name == "A":  # Левая граница диапазона
                params_dict[param_name] = rnd.randint(0, int(N_max*0.25))
            elif param_name == "B":  # Правая граница диапазона
                params_dict[param_name] = rnd.randint(int(N_max*0.75), N_max)
            elif param_name == "K_step":  # Шаг
                params_dict[param_name] = rnd.randint(1, 3)

    # Устанавливаем все сгенерированные параметры в конфиг
    for param_name, value in params_dict.items():
        config.set_param(param_name, value)

    return config
