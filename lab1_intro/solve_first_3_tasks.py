from typing import List


# Индекс первого элемента, кратного M
def first_multiple_index(a: List[int], M: int) -> int:
    if M == 0:
        return -1
    for i, x in enumerate(a):
        if x % M == 0:
            return i
    return -1


# Индекс последнего элемента массива, для которого |a[i]| > T.
def last_abs_gt_index(a: List[int], T: int) -> int:
    for i in range(len(a) - 1, -1, -1):
        if abs(a[i]) > T:
            return i
    return -1


# Количество элементов в диапазоне [A; B]
def count_in_range(a: List[int], A: int, B: int) -> int:
    # По условию A <= B
    if A > B:
        return 0
    return sum(1 for x in a if A <= x <= B)


# Сумма модулей на позициях с шагом K, начиная с P
def sum_abs_step(a: List[int], P: int, K_step: int) -> int:
    if K_step < 1:
        return 0
    if P >= len(a):
        return 0
    s = 0
    for i in range(P, len(a), K_step):
        s += abs(a[i])
    return s
