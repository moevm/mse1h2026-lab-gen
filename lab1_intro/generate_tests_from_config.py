import random
from typing import List

from generate_params import Config


def gen_random_array(rnd: random.Random, cfg: Config) -> List[int]:
    n = rnd.randint(int(cfg.get_param("N_max")*0.1), cfg.get_param("N_max"))
    return [rnd.randint(-25, 25) for _ in range(n)]
