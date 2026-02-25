from typing import List

def ans_first_multiple_index(a: List[int], M: int) -> int:
    if M == 0:
        return -1
    for i, x in enumerate(a):
        if x % M == 0:
            return i
    return -1

def ans_last_abs_gt_index(a: List[int], T: int) -> int:
    for i in range(len(a) - 1, -1, -1):
        if abs(a[i]) > T:
            return i
    return -1

def ans_count_in_range(a: List[int], A: int, B: int) -> int:
    if A > B:
        return 0
    count = 0
    for x in a:
        if A <= x <= B:
            count += 1
    return count

def ans_sum_abs_step(a: List[int], P: int, K_step: int) -> int:
    n = len(a)
    if P >= n or K_step < 1:
        return 0
    
    total = 0
    for i in range(P, n, K_step):
        total += abs(a[i])
    return total


def ans_sum_divisible(a: List[int], D: int) -> int:
    if D == 0:
        return 0
    
    total = 0
    for x in a:
        if x % D == 0:
            total += x
    return total

def ans_count_abs_lt(a: List[int], L: int) -> int:
    count = 0
    for x in a:
        if abs(x) < L:
            count += 1
    return count