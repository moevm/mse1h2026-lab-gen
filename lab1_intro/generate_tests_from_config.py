import random
from typing import List, Dict, Any

from generate_params import Config, TASKS_INFO, generate_params


def gen_random_array(rnd: random.Random, cfg: Config) -> List[int]:
    n = rnd.randint(int(cfg.get_param("N_max")*0.1), cfg.get_param("N_max"))
    return [rnd.randint(-25, 25) for _ in range(n)]


def generate_tests(cfg: Config, tests_per_task: int = 5) -> List[Dict[str, Any]]:
    nmax = cfg.get_param("N_max")
    seed_hash = cfg.get_param("seed_hash")
    rnd = random.Random(seed_hash)

    out: List[Dict[str, Any]] = []
    for task_id in cfg.get_tasks():
        spec = TASKS_INFO[task_id]
        func = spec["func"]
        param_names: List[str] = spec["params"]

        # параметры задачи из конфига
        task_params = {p: cfg.get_param(p) for p in param_names}

        tests: List[Dict[str, Any]] = []

        for _ in range(tests_per_task):
            arr = gen_random_array(rnd, cfg)

            # считаем ожидаемое значение вызовом правильной функции
            args = [arr] + [task_params[p] for p in param_names]
            expected = func(*args)

            tests.append({
                "значение теста": arr,
                "ожидаемое значение": expected
            })

        # если параметр один — кладём число, если два — кладём dict
        if len(param_names) == 1:
            param_value: Any = task_params[param_names[0]]
        else:
            param_value = task_params

        out.append({
            "название первой функции": spec["name"],
            "значение параметра функции": param_value,
            "тесты": tests
        })

    return out
