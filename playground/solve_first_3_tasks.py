from typing import List


# Индекс первого элемента, кратного M
def first_multiple_index(a: List[int], M: int) -> int:
    if M == 0:
        return -1
    for i, x in enumerate(a):
        if x % M == 0:
            return i
    return -1