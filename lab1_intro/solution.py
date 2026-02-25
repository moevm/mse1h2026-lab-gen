# Решение студента

from typing import List


# Индекс первого элемента, кратного M
def ans_first_multiple_index(a: List[int], M: int) -> int:
    """
    Возвращает индекс первого элемента массива, который делится на M без остатка.
    Если нет — -1.
    """
    if M == 0:
        return -1
    for i, x in enumerate(a):
        if x % M == 0:
            return i
    return -1


# Индекс последнего элемента массива, для которого |a[i]| > T
def ans_last_abs_gt_index(a: List[int], T: int) -> int:
    """
    Возвращает индекс последнего элемента, для которого |a[i]| > T.
    Если нет — -1.
    """
    for i in range(len(a) - 1, -1, -1):
        if abs(a[i]) > T:
            return i
    return -1


# Количество элементов в диапазоне [A; B]
def ans_count_in_range(a: List[int], A: int, B: int) -> int:
    """
    Возвращает количество элементов, удовлетворяющих A ≤ a[i] ≤ B.
    """
    # По условию A ≤ B, но на всякий случай проверяем
    if A > B:
        return 0
    count = 0
    for x in a:
        if A <= x <= B:
            count += 1
    return count


# Сумма модулей на позициях с шагом K, начиная с P
def ans_sum_abs_step(a: List[int], P: int, K_step: int) -> int:
    """
    Сумма |a[i]| по индексам P, P+K, P+2K, ... пока i < n.
    Если P ≥ n — 0.
    """
    n = len(a)
    if P >= n or K_step < 1:
        return 0
    
    total = 0
    for i in range(P, n, K_step):
        total += abs(a[i])
    return total


# Сумма элементов, делящихся на D
def ans_sum_divisible(a: List[int], D: int) -> int:
    """
    Сумма всех элементов, которые делятся на D без остатка.
    Если нет — 0.
    """
    if D == 0:
        return 0
    
    total = 0
    for x in a:
        if x % D == 0:
            total += x
    return total


# Количество элементов, которые по модулю меньше L
def ans_count_abs_lt(a: List[int], L: int) -> int:
    """
    Количество элементов, для которых |a[i]| < L.
    """
    count = 0
    for x in a:
        if abs(x) < L:
            count += 1
    return count