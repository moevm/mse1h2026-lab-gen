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
