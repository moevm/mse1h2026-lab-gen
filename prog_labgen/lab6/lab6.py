from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from prog_labgen.base_module import BaseTask, rand_sample


LIST_TYPES = {
    0: "односвязный список",
    1: "циклический двунаправленный список",
    2: "развёрнутый связный список",
    3: "XOR-список",
}


@dataclass(frozen=True)
class CoreSpec:
    title: str
    params: tuple[str, ...]
    prototype: str
    description: str


CORES: dict[int, CoreSpec] = {
    0: CoreSpec("Количество элементов, больших X", ("X",), "int list_count_greater(struct ListStruct *list, int x);", "Вернуть количество элементов, значение которых больше X."),
    1: CoreSpec("Сумма элементов, кратных D", ("D",), "int list_sum_divisible(struct ListStruct *list, int d);", "Вернуть сумму элементов, делящихся на D без остатка."),
    2: CoreSpec("Количество элементов в диапазоне [A; B]", ("A", "B"), "int list_count_range(struct ListStruct *list, int a, int b);", "Вернуть количество элементов, для которых A <= data <= B."),
    3: CoreSpec("Сумма элементов на позициях с шагом K, начиная с P", ("P", "K"), "int list_sum_by_step(struct ListStruct *list, int p, int k);", "Вернуть сумму элементов с индексами P, P+K, P+2K, ..."),
    4: CoreSpec("Циклический сдвиг вправо на K", ("K",), "void list_rotate_right(struct ListStruct *list, int k);", "Сдвинуть элементы списка вправо на K позиций."),
    5: CoreSpec("Первый элемент, больший X", ("X",), "struct ListNode *list_find_first_greater(struct ListStruct *list, int x);", "Вернуть указатель на первый узел со значением больше X или NULL."),
    6: CoreSpec("Разделение относительно X", ("X",), "void list_partition(struct ListStruct *list, int x);", "Сначала элементы < X, затем элементы >= X, порядок внутри групп сохраняется."),
    7: CoreSpec("Удаление всех элементов, равных X", ("X",), "void list_remove_all_equal(struct ListStruct *list, int x);", "Удалить все элементы, равные X."),
    8: CoreSpec("Замена всех элементов X на VALUE", ("X", "VALUE"), "void list_replace_value(struct ListStruct *list, int x, int value);", "Заменить все значения X на VALUE."),
    9: CoreSpec("Индекс последнего элемента, меньшего X", ("X",), "int list_find_last_less_index(struct ListStruct *list, int x);", "Вернуть индекс последнего элемента < X или -1."),
    10: CoreSpec("Проверка наличия элемента в диапазоне [A; B]", ("A", "B"), "bool list_has_range_value(struct ListStruct *list, int a, int b);", "Вернуть true, если есть элемент в диапазоне [A; B]."),
    11: CoreSpec("Удаление элементов вне диапазона [A; B]", ("A", "B"), "void list_remove_out_of_range(struct ListStruct *list, int a, int b);", "Удалить все элементы вне диапазона [A; B]."),
    12: CoreSpec("Сумма элементов в диапазоне индексов [P; R]", ("P", "R"), "int list_sum_index_range(struct ListStruct *list, int p, int r);", "Вернуть сумму элементов с индексами от P до R включительно."),
    13: CoreSpec("Умножение элементов на позициях с шагом K", ("P", "K", "M"), "void list_multiply_by_step(struct ListStruct *list, int p, int k, int m);", "Умножить на M элементы с индексами P, P+K, P+2K, ..."),
    14: CoreSpec("Проверка чередования относительно X", ("X",), "bool list_is_alternating_by_x(struct ListStruct *list, int x);", "Проверить чередование элементов < X и >= X."),
    15: CoreSpec("Ограничение значений диапазоном [A; B]", ("A", "B"), "void list_clamp(struct ListStruct *list, int a, int b);", "Значения меньше A заменить на A, больше B - на B."),
    16: CoreSpec("Вставка VALUE после каждого элемента, кратного D", ("D", "VALUE"), "void list_insert_value_after_divisible(struct ListStruct *list, int d, int value);", "После каждого элемента, кратного D, вставить VALUE."),
    17: CoreSpec("Удаление подряд идущих повторов X", ("X",), "void list_compress_x_runs(struct ListStruct *list, int x);", "В каждой серии подряд идущих X оставить один элемент."),
    18: CoreSpec("Подсчёт пар соседей с суммой S", ("S",), "int list_count_neighbor_pairs_sum(struct ListStruct *list, int s);", "Вернуть количество соседних пар с суммой S."),
    19: CoreSpec("Все элементы с шагом K больше X", ("P", "K", "X"), "bool list_all_by_step_greater(struct ListStruct *list, int p, int k, int x);", "Проверить, что все элементы P, P+K, ... больше X."),
}



def _list_type_assignment_text(list_type: int) -> list[str]:
    if list_type == 0:
        return [
            "Создайте API (application programming interface - в данном случае набор функций) для работы с односвязным списком.",
            "",
            "Односвязный список состоит из узлов, каждый из которых хранит значение и указатель на следующий элемент.",
            "Список хранит значения типа int.",
            "",
            "Структуры списка выглядят следующим образом:",
            "",
            "struct ListNode {",
            "    struct ListNode *next;  // указатель на следующий элемент",
            "    int data;               // данные для хранения в узле",
            "};",
            "",
            "struct ListStruct {",
            "    struct ListNode *head;  // указатель на голову",
            "};",
            "",
            "Особенности односвязного списка:",
            "head указывает на первый элемент списка.",
            "Пустой список имеет head == NULL.",
            "Последний элемент имеет next == NULL.",
            "Движение по списку возможно только вперёд.",
            "Чтобы найти предыдущий узел, нужно начинать обход с головы.",
            "Вставка в начало выполняется просто, а вставка в конец требует обхода списка, если в структуре нет указателя на хвост.",
        ]
    if list_type == 1:
        return [
            "Создайте API (application programming interface - в данном случае набор функций) для работы с циклическим двунаправленным списком.",
            "",
            "Циклический двунаправленный список состоит из узлов, каждый из которых хранит значение, указатель на следующий элемент и указатель на предыдущий элемент.",
            "Список хранит значения типа int.",
            "",
            "Структуры списка выглядят следующим образом:",
            "",
            "struct ListNode {",
            "    struct ListNode *next;  // указатель на следующий элемент",
            "    struct ListNode *prev;  // указатель на предыдущий элемент",
            "    int data;               // данные для хранения в узле",
            "};",
            "",
            "struct ListStruct {",
            "    struct ListNode *head;  // указатель на голову",
            "};",
            "",
            "Особенности циклического двунаправленного списка:",
            "head указывает на первый элемент списка.",
            "Пустой список имеет head == NULL.",
            "У последнего элемента next указывает на head.",
            "У первого элемента prev указывает на последний элемент.",
            "У списка из одного элемента node->next == node и node->prev == node.",
            "При обходе нельзя искать конец по NULL.",
            "Обход заканчивается, когда текущий указатель снова стал равен head.",
            "При вставке и удалении нужно корректно обновлять и next, и prev.",
        ]
    if list_type == 2:
        return [
            "Создайте API (application programming interface - в данном случае набор функций) для работы с развёрнутым связным списком.",
            "",
            "Развёрнутый связный список - это структура данных, в которой каждый физический узел, то есть блок, содержит несколько логических элементов в массиве фиксированного размера.",
            "Это уменьшает количество выделений памяти и снижает накладные расходы на хранение указателей.",
            "Список хранит значения типа int.",
            "",
            "Структуры списка выглядят следующим образом:",
            "",
            "#define BLOCK_SIZE 4",
            "",
            "struct ListNode {",
            "    int data[BLOCK_SIZE];   // массив элементов",
            "    int count;              // текущее количество элементов в блоке",
            "    struct ListNode *next;  // указатель на следующий блок",
            "};",
            "",
            "struct ListStruct {",
            "    struct ListNode *head;  // указатель на первый блок",
            "};",
            "",
            "В развёрнутом списке один ListNode - это не один элемент, а блок элементов.",
            "Например, список из 9 чисел при BLOCK_SIZE = 4 может выглядеть так:",
            "",
            "[3 8 1 6 | count = 4] -> [5 9 2 4 | count = 4] -> [7 _ _ _ | count = 1] -> NULL",
            "",
            "Логические элементы списка: 3, 8, 1, 6, 5, 9, 2, 4, 7.",
            "Физические узлы списка: block 0, block 1, block 2.",
            "",
            "Инварианты развёрнутого списка:",
            "Пустой список имеет head == NULL.",
            "Каждый существующий блок имеет 0 < count <= BLOCK_SIZE.",
            "Блок с count == 0 не должен оставаться в списке.",
            "В последнем блоке может быть меньше BLOCK_SIZE элементов.",
            "Элементы внутри блока находятся в data[0] ... data[count - 1].",
            "Элементы на позициях count ... BLOCK_SIZE - 1 считаются неиспользуемыми.",
            "Порядок логических элементов определяется порядком блоков и порядком элементов внутри блока.",
            "Индекс считается по логическим элементам, а не по блокам.",
        ]
    return [
        "Создайте API (application programming interface - в данном случае набор функций) для работы с XOR-списком.",
        "",
        "XOR список - это разновидность двусвязного списка, в котором вместо хранения двух отдельных указателей prev и next используется один указатель, содержащий результат побитового XOR адресов соседних узлов.",
        "",
        "В XOR-списке хранится link = prev ⊕ next, где:",
        "prev - адрес предыдущего узла",
        "next - адрес следующего узла",
        "⊕ - операция побитового XOR",
        "",
        "Чтобы получить следующий элемент при обходе, необходимо знать адрес предыдущего:",
        "next = prev ⊕ current->link",
        "",
        "Список хранит значения типа int.",
        "Структуры списка выглядят следующим образом:",
        "",
        "struct ListNode {",
        "    struct ListNode *link;  // XOR(prev, next)",
        "    int data;               // данные",
        "};",
        "",
        "struct ListStruct {",
        "    struct ListNode *head;  // указатель на первый элемент",
        "};",
        "",
        "Для выполнения XOR над адресами нужно использовать целочисленный тип uintptr_t из <stdint.h>.",
        "",
        "static struct ListNode *xor_nodes(struct ListNode *a, struct ListNode *b) {",
        "    return (struct ListNode *)((uintptr_t)a ^ (uintptr_t)b);",
        "}",
        "",
        "Особенности XOR-списка:",
        "Для движения вперёд нужно помнить предыдущий узел.",
        "Для движения назад нужно помнить следующий узел.",
        "Нельзя получить next, зная только current.",
        "Нельзя получить prev, зная только current.",
        "Произвольный доступ невозможен без последовательного обхода.",
        "Любое неверное обновление XOR-связей разрушает список.",
        "Для преобразования указателей нужно использовать uintptr_t.",
    ]


def _standard_functions_assignment_text() -> list[str]:
    return [
        "Структуры объявлять не нужно! Они уже есть в проверяющем коде.",
        "Функцию main писать не нужно. Программа должна содержать только реализации требуемых функций.",
        "",
        "Необходимо реализовать следующий стандартный API для взаимодействия со списком:",
        "",
        "struct ListStruct *list_init();",
        "Создаёт новый список и возвращает указатель на него. Список должен быть пустым.",
        "",
        "void list_destroy(struct ListStruct *list);",
        "Очищает список list, освобождает память всех его элементов и память самой структуры списка.",
        "",
        "void list_push_front(struct ListStruct *list, int data);",
        "Добавляет новый элемент в начало списка.",
        "list -- список, в который необходимо добавить элемент.",
        "data -- данные, которые нужно добавить.",
        "",
        "void list_push_back(struct ListStruct *list, int data);",
        "Добавляет новый элемент в конец списка.",
        "list -- список, в который необходимо добавить элемент.",
        "data -- данные, которые нужно добавить.",
        "",
        "void list_pop(struct ListStruct *list, struct ListNode *node_to_remove);",
        "Удаляет элемент из списка.",
        "list -- список, из которого необходимо удалить элемент.",
        "node_to_remove -- указатель на элемент, который необходимо удалить.",
        "Если node_to_remove равняется NULL, список не изменяется.",
        "",
        "int list_count(struct ListStruct *list);",
        "Подсчитывает количество логических элементов в списке.",
        "list -- список, для которого необходимо посчитать количество элементов.",
        "",
        "struct ListNode *list_get_head(struct ListStruct *list);",
        "Возвращает указатель на первый физический узел списка.",
        "Если список пуст, возвращает NULL.",
        "",
        "struct ListNode *list_get_tail(struct ListStruct *list);",
        "Возвращает указатель на последний физический узел списка.",
        "Если список пуст, возвращает NULL.",
        "",
        "struct ListNode *list_get(struct ListStruct *list, int index);",
        "Возвращает указатель на элемент с индексом index.",
        "Индексация начинается с 0.",
        "Если index выходит за границы списка, возвращает NULL.",
        "Для развёрнутого списка возвращает указатель на блок, в котором находится логический элемент с заданным индексом.",
        "",
        "bool list_is_empty(struct ListStruct *list);",
        "Возвращает true, если список пуст, иначе возвращает false.",
        "",
        "void list_sort(struct ListStruct *list);",
        "Сортирует логические элементы списка по возрастанию значения data.",
        "Структура списка после сортировки должна оставаться корректной для выбранного типа списка.",
    ]


def _insert_assignment_text(list_type: int, insert_mode: int) -> list[str]:
    if list_type == 2:
        return [
            "Дополнительно необходимо реализовать функцию вставки для развёрнутого списка:",
            "",
            "void list_insert_at(struct ListStruct *list, int index, int data);",
            "Вставляет новый логический элемент со значением data по индексу index.",
            "Если index <= 0, элемент вставляется в начало.",
            "Если index >= list_count(list), элемент вставляется в конец.",
            "При вставке нужно поддерживать корректные значения count в блоках.",
        ]
    if insert_mode == 0:
        return [
            "Дополнительно необходимо реализовать функцию вставки:",
            "",
            "void list_insert_before(struct ListStruct *list, struct ListNode *node, int data);",
            "Вставляет новый элемент со значением data перед узлом node.",
            "list -- список, в который необходимо добавить элемент.",
            "node -- узел, перед которым нужно вставить новый элемент.",
            "data -- данные, которые нужно добавить.",
            "Если node равняется NULL, элемент необходимо добавить в конец списка.",
        ]
    return [
        "Дополнительно необходимо реализовать функцию вставки:",
        "",
        "void list_insert_after(struct ListStruct *list, struct ListNode *node, int data);",
        "Вставляет новый элемент со значением data после узла node.",
        "list -- список, в который необходимо добавить элемент.",
        "node -- узел, после которого нужно вставить новый элемент.",
        "data -- данные, которые нужно добавить.",
        "Если node равняется NULL, элемент необходимо добавить в начало списка.",
    ]


def _format_core_params(spec: CoreSpec, params: dict[str, int]) -> str:
    return ", ".join(f"{name} = {params[name]}" for name in spec.params)



def _count_greater(a, x): return sum(v > x for v in a)
def _sum_divisible(a, d): return sum(v for v in a if v % d == 0)
def _count_range(a, lo, hi): return sum(lo <= v <= hi for v in a)
def _sum_by_step(a, p, k): return 0 if p >= len(a) else sum(a[i] for i in range(p, len(a), k))
def _rotate_right(a, k): return a[-(k % len(a)):] + a[:-(k % len(a))] if a else a

def _first_greater(a, x):
    for i, v in enumerate(a):
        if v > x:
            return i
    return -1

def _partition(a, x): return [v for v in a if v < x] + [v for v in a if v >= x]
def _remove_equal(a, x): return [v for v in a if v != x]
def _replace_value(a, x, value): return [value if v == x else v for v in a]
def _last_less(a, x): return max([i for i, v in enumerate(a) if v < x], default=-1)
def _has_range(a, lo, hi): return any(lo <= v <= hi for v in a)
def _remove_out(a, lo, hi): return [v for v in a if lo <= v <= hi]
def _sum_index_range(a, p, r): return sum(a[max(0, p):min(len(a), r + 1)])
def _multiply_step(a, p, k, m):
    b = a[:]
    for i in range(p, len(b), k):
        b[i] *= m
    return b

def _alternating(a, x):
    return all((a[i] < x) != (a[i - 1] < x) for i in range(1, len(a)))

def _clamp(a, lo, hi): return [min(max(v, lo), hi) for v in a]

def _insert_after_divisible(a, d, value):
    b = []
    for v in a:
        b.append(v)
        if v % d == 0:
            b.append(value)
    return b

def _compress_x(a, x):
    b = []
    prev_x = False
    for v in a:
        if v == x:
            if not prev_x:
                b.append(v)
            prev_x = True
        else:
            b.append(v)
            prev_x = False
    return b

def _pairs_sum(a, s): return sum(1 for i in range(len(a) - 1) if a[i] + a[i + 1] == s)
def _all_step_gt(a, p, k, x): return p < len(a) and all(a[i] > x for i in range(p, len(a), k))


class Lab6Task(BaseTask):
    def __init__(self, seed: str, tests_count: int = 5, fail_on_first_test: bool = True, compiler: str | None = None) -> None:
        super().__init__(seed=seed, fail_on_first_test=fail_on_first_test, compiler=compiler)
        self.tests_count = tests_count
        self._variant: dict[str, Any] | None = None

    def _build_variant(self) -> dict[str, Any]:
        if self._variant is not None:
            return self._variant
        rnd = self.make_random()
        list_type = rnd.randint(0, 3)
        available = [i for i in CORES if not (list_type == 2 and i == 5)]
        cores = rand_sample(rnd, available, 4)
        a = rnd.randint(-10, 0)
        b = rnd.randint(1, 10)
        self._variant = {
            "seed": self.seed,
            "seed_hash": self.make_seed_hash(),
            "LIST_TYPE": list_type,
            "INSERT_MODE": rnd.randint(0, 1),
            "CORES": cores,
            "params": {
                "X": rnd.randint(-5, 5), "D": rnd.randint(2, 5),
                "A": a, "B": b, "P": rnd.randint(0, 3),
                "K": rnd.randint(1, 3), "M": rnd.randint(2, 4),
                "R": rnd.randint(2, 7), "S": rnd.randint(-5, 8),
                "VALUE": rnd.randint(10, 20),
            },
        }
        return self._variant

    def render_assignment(self) -> str:
        variant = self._build_variant()
        params = variant["params"]
        list_type = variant["LIST_TYPE"]

        lines = [
            "Концепция варианта ЛР6",
            f"Seed: {variant['seed']}",
            f"Seed hash: {variant['seed_hash']}",
            f"LIST_TYPE: {list_type} ({LIST_TYPES[list_type]})",
            f"INSERT_MODE: {variant['INSERT_MODE']}",
            "CORE_1: " + str(variant["CORES"][0]),
            "CORE_2: " + str(variant["CORES"][1]),
            "CORE_3: " + str(variant["CORES"][2]),
            "CORE_4: " + str(variant["CORES"][3]),
            "",
        ]

        lines.extend(_list_type_assignment_text(list_type))
        lines.append("")
        lines.extend(_standard_functions_assignment_text())
        lines.append("")
        lines.extend(_insert_assignment_text(list_type, variant["INSERT_MODE"]))
        lines.append("")
        lines.append("Также необходимо реализовать дополнительные индивидуальные функции варианта.")
        lines.append("Эти функции не заменяют стандартный API, а добавляются к нему.")
        lines.append("Ниже перечислены только функции, назначенные в вашем варианте.")
        lines.append("")
        lines.append("Дополнительные индивидуальные функции:")

        for index, code in enumerate(variant["CORES"], start=1):
            spec = CORES[code]
            lines.append("")
            lines.append(f"{index}. {spec.title}")
            core_params = _format_core_params(spec, params)
            if core_params:
                lines.append(f"Параметры: {core_params}.")
            lines.append("")
            lines.append(spec.prototype)
            lines.append(spec.description)

        return "\n".join(lines)

    def _make_array(self, salt: str) -> list[int]:
        rnd = self.make_random(salt)
        n = rnd.randint(0, 10)
        return [rnd.randint(-8, 12) for _ in range(n)]

    def _expected_lines_for_array(self, arr: list[int]) -> list[str]:
        v = self._build_variant()
        p = v["params"]
        lines = [
            f"INPUT_ARRAY: {' '.join(map(str, arr)) if arr else 'empty'}",
            f"LIST_COUNT: {len(arr)}",
            f"SORTED: {' '.join(map(str, sorted(arr))) if arr else 'empty'}",
        ]

        for core_index, code in enumerate(v["CORES"], start=1):
            spec = CORES[code]
            prefix = f"CORE_{core_index} {spec.prototype}"

            if code == 0:
                lines.append(f"{prefix} -> {_count_greater(arr, p['X'])}")
            elif code == 1:
                lines.append(f"{prefix} -> {_sum_divisible(arr, p['D'])}")
            elif code == 2:
                lines.append(f"{prefix} -> {_count_range(arr, p['A'], p['B'])}")
            elif code == 3:
                lines.append(f"{prefix} -> {_sum_by_step(arr, p['P'], p['K'])}")
            elif code == 4:
                expected = _rotate_right(arr, p['K'])
                lines.append(f"{prefix} -> {' '.join(map(str, expected)) if expected else 'empty'}")
            elif code == 5:
                idx = _first_greater(arr, p['X'])
                lines.append(f"{prefix} -> {'NULL' if idx == -1 else 'index ' + str(idx)}")
            elif code == 6:
                expected = _partition(arr, p['X'])
                lines.append(f"{prefix} -> {' '.join(map(str, expected)) if expected else 'empty'}")
            elif code == 7:
                expected = _remove_equal(arr, p['X'])
                lines.append(f"{prefix} -> {' '.join(map(str, expected)) if expected else 'empty'}")
            elif code == 8:
                expected = _replace_value(arr, p['X'], p['VALUE'])
                lines.append(f"{prefix} -> {' '.join(map(str, expected)) if expected else 'empty'}")
            elif code == 9:
                lines.append(f"{prefix} -> {_last_less(arr, p['X'])}")
            elif code == 10:
                lines.append(f"{prefix} -> {str(_has_range(arr, p['A'], p['B'])).lower()}")
            elif code == 11:
                expected = _remove_out(arr, p['A'], p['B'])
                lines.append(f"{prefix} -> {' '.join(map(str, expected)) if expected else 'empty'}")
            elif code == 12:
                lines.append(f"{prefix} -> {_sum_index_range(arr, p['P'], p['R'])}")
            elif code == 13:
                expected = _multiply_step(arr, p['P'], p['K'], p['M'])
                lines.append(f"{prefix} -> {' '.join(map(str, expected)) if expected else 'empty'}")
            elif code == 14:
                lines.append(f"{prefix} -> {str(_alternating(arr, p['X'])).lower()}")
            elif code == 15:
                expected = _clamp(arr, p['A'], p['B'])
                lines.append(f"{prefix} -> {' '.join(map(str, expected)) if expected else 'empty'}")
            elif code == 16:
                expected = _insert_after_divisible(arr, p['D'], p['VALUE'])
                lines.append(f"{prefix} -> {' '.join(map(str, expected)) if expected else 'empty'}")
            elif code == 17:
                expected = _compress_x(arr, p['X'])
                lines.append(f"{prefix} -> {' '.join(map(str, expected)) if expected else 'empty'}")
            elif code == 18:
                lines.append(f"{prefix} -> {_pairs_sum(arr, p['S'])}")
            elif code == 19:
                lines.append(f"{prefix} -> {str(_all_step_gt(arr, p['P'], p['K'], p['X'])).lower()}")

        return lines

    def generate_tests(self) -> list[dict[str, Any]]:
        tests: list[dict[str, Any]] = []
        variant = self._build_variant()

        for i in range(self.tests_count):
            arr = self._make_array(f"test-{i}")
            expected_details = "\n".join(self._expected_lines_for_array(arr)) + "\n"

            moodle_payload = {
                "seed": variant["seed"],
                "seed_hash": variant["seed_hash"],
                "LIST_TYPE": variant["LIST_TYPE"],
                "INSERT_MODE": variant["INSERT_MODE"],
                "CORES": variant["CORES"],
                "params": variant["params"],
                "input_array": arr,
            }

            stdin_text = json.dumps(moodle_payload, ensure_ascii=False, sort_keys=True)

            tests.append({
                "input_array": arr,
                "stdin": stdin_text,
                "expected_stdout": "OK\n",
                "expected_output": "OK\n",
                "expected_details": expected_details,
                "array": arr,
                "variant": moodle_payload,
            })

        return tests

    def _struct_code(self, list_type: int) -> str:
        if list_type == 0:
            return "struct ListNode { struct ListNode *next; int data; };\nstruct ListStruct { struct ListNode *head; };"
        if list_type == 1:
            return "struct ListNode { struct ListNode *next; struct ListNode *prev; int data; };\nstruct ListStruct { struct ListNode *head; };"
        if list_type == 2:
            return "#define BLOCK_SIZE 4\nstruct ListNode { int data[BLOCK_SIZE]; int count; struct ListNode *next; };\nstruct ListStruct { struct ListNode *head; };"
        return "struct ListNode { struct ListNode *link; int data; };\nstruct ListStruct { struct ListNode *head; };"

    def _dump_code(self, list_type: int) -> str:
        if list_type == 2:
            return """
int dump(struct ListStruct *l, int *out) {
    int n = 0;
    if (!l) return 0;
    for (struct ListNode *p = l->head; p && n < 1000; p = p->next) {
        for (int i = 0; i < p->count && n < 1000; i++) out[n++] = p->data[i];
    }
    return n;
}

struct ListNode *__lab6_expected_node(struct ListStruct *l, int index) {
    if (!l || index < 0) return NULL;
    int pos = 0;
    for (struct ListNode *p = l->head; p; p = p->next) {
        if (index < pos + p->count) return p;
        pos += p->count;
    }
    return NULL;
}

struct ListNode *__lab6_expected_tail(struct ListStruct *l) {
    if (!l || !l->head) return NULL;
    struct ListNode *p = l->head;
    while (p->next) p = p->next;
    return p;
}

int __lab6_validate_structure(struct ListStruct *l, int expected_n) {
    if (!l) return 0;
    if (expected_n == 0) return l->head == NULL;

    int total = 0;
    for (struct ListNode *p = l->head; p; p = p->next) {
        if (p->count <= 0 || p->count > BLOCK_SIZE) return 0;
        total += p->count;
        if (p->next && p->count != BLOCK_SIZE) return 0;
        if (total > expected_n) return 0;
    }
    return total == expected_n;
}
"""
        if list_type == 1:
            return """
int dump(struct ListStruct *l, int *out) {
    if (!l || !l->head) return 0;
    int n = 0;
    struct ListNode *p = l->head;
    do {
        out[n++] = p->data;
        p = p->next;
    } while (p && p != l->head && n < 1000);
    return n;
}

struct ListNode *__lab6_expected_node(struct ListStruct *l, int index) {
    if (!l || !l->head || index < 0) return NULL;
    int i = 0;
    struct ListNode *p = l->head;
    do {
        if (i == index) return p;
        i++;
        p = p->next;
    } while (p && p != l->head && i < 1000);
    return NULL;
}

struct ListNode *__lab6_expected_tail(struct ListStruct *l) {
    if (!l || !l->head) return NULL;
    return l->head->prev;
}

int __lab6_validate_structure(struct ListStruct *l, int expected_n) {
    if (!l) return 0;
    if (expected_n == 0) return l->head == NULL;
    if (!l->head || !l->head->prev || !l->head->next) return 0;

    int n = 0;
    struct ListNode *p = l->head;
    do {
        if (!p || !p->next || !p->prev) return 0;
        if (p->next->prev != p) return 0;
        if (p->prev->next != p) return 0;
        p = p->next;
        n++;
        if (n > expected_n) return 0;
    } while (p != l->head);
    return n == expected_n;
}
"""
        if list_type == 3:
            return """
static struct ListNode *hx(struct ListNode *a, struct ListNode *b) {
    return (struct ListNode*)((uintptr_t)a ^ (uintptr_t)b);
}

int dump(struct ListStruct *l, int *out) {
    int n = 0;
    if (!l) return 0;
    struct ListNode *prev = NULL;
    struct ListNode *cur = l->head;
    while (cur && n < 1000) {
        out[n++] = cur->data;
        struct ListNode *next = hx(prev, cur->link);
        prev = cur;
        cur = next;
    }
    return n;
}

struct ListNode *__lab6_expected_node(struct ListStruct *l, int index) {
    if (!l || index < 0) return NULL;
    int i = 0;
    struct ListNode *prev = NULL;
    struct ListNode *cur = l->head;
    while (cur && i < 1000) {
        if (i == index) return cur;
        struct ListNode *next = hx(prev, cur->link);
        prev = cur;
        cur = next;
        i++;
    }
    return NULL;
}

struct ListNode *__lab6_expected_tail(struct ListStruct *l) {
    if (!l) return NULL;
    struct ListNode *prev = NULL;
    struct ListNode *cur = l->head;
    while (cur) {
        struct ListNode *next = hx(prev, cur->link);
        if (!next) return cur;
        prev = cur;
        cur = next;
    }
    return NULL;
}

int __lab6_validate_structure(struct ListStruct *l, int expected_n) {
    int out[1000];
    return dump(l, out) == expected_n;
}
"""
        return """
int dump(struct ListStruct *l, int *out) {
    int n = 0;
    if (!l) return 0;
    for (struct ListNode *p = l->head; p && n < 1000; p = p->next) out[n++] = p->data;
    return n;
}

struct ListNode *__lab6_expected_node(struct ListStruct *l, int index) {
    if (!l || index < 0) return NULL;
    int i = 0;
    for (struct ListNode *p = l->head; p; p = p->next) {
        if (i == index) return p;
        i++;
    }
    return NULL;
}

struct ListNode *__lab6_expected_tail(struct ListStruct *l) {
    if (!l || !l->head) return NULL;
    struct ListNode *p = l->head;
    while (p->next) p = p->next;
    return p;
}

int __lab6_validate_structure(struct ListStruct *l, int expected_n) {
    if (!l) return 0;
    if (expected_n == 0) return l->head == NULL;

    int n = 0;
    for (struct ListNode *p = l->head; p; p = p->next) {
        n++;
        if (n > expected_n) return 0;
    }
    return n == expected_n;
}
"""

    def _expect_code(self, arr: list[int], name: str) -> str:
        if arr:
            return f"int {name}[] = {{{', '.join(map(str, arr))}}}; int {name}_n = {len(arr)};"
        return f"int {name}[1] = {{0}}; int {name}_n = 0;"

    def _list_literal(self, arr: list[int]) -> str:
        return ", ".join(map(str, arr)) or "0"

    def _assert_accessors_code(self, arr: list[int], name: str) -> str:
        return self._expect_code(arr, name) + f"\nASSERT_ACCESSORS({name}, {name}_n);"

    def _standard_test_code(self, arr: list[int], idx: int) -> str:
        v = self._build_variant()
        list_type = v["LIST_TYPE"]
        insert_mode = v["INSERT_MODE"]
        blocks: list[str] = []

        empty_name = f"std_{idx}_empty"
        blocks.append(
            "{\n"
            "struct ListStruct *l = list_init();\n"
            "ASSERT_PTR_NOT_NULL(l);\n"
            + self._assert_accessors_code([], empty_name)
            + "\nlist_pop(l, NULL);\n"
            + self._assert_accessors_code([], f"{empty_name}_after_pop_null")
            + "\nlist_destroy(l);\n"
            "}"
        )

        model: list[int] = []
        lines = ["{", "struct ListStruct *l = list_init();"]
        lines.append(self._assert_accessors_code(model, f"std_{idx}_push_back_0"))
        for step, value in enumerate(arr, start=1):
            model.append(value)
            lines.append(f"list_push_back(l, {value});")
            lines.append(self._assert_accessors_code(model, f"std_{idx}_push_back_{step}"))
        lines.append("list_destroy(l);")
        lines.append("}")
        blocks.append("\n".join(lines))

        model = []
        lines = ["{", "struct ListStruct *l = list_init();"]
        lines.append(self._assert_accessors_code(model, f"std_{idx}_push_front_0"))
        for step, value in enumerate(arr, start=1):
            model.insert(0, value)
            lines.append(f"list_push_front(l, {value});")
            lines.append(self._assert_accessors_code(model, f"std_{idx}_push_front_{step}"))
        lines.append("list_destroy(l);")
        lines.append("}")
        blocks.append("\n".join(lines))

        sort_expected = sorted(arr)
        blocks.append(
            "{\n"
            f"struct ListStruct *l = make_list((int[]){{{self._list_literal(arr)}}}, {len(arr)});\n"
            "list_sort(l);\n"
            + self._assert_accessors_code(sort_expected, f"std_{idx}_sort")
            + "\nlist_destroy(l);\n"
            "}"
        )

        if list_type != 2:
            model = [10, 20, 30, 40]
            lines = [
                "{",
                f"struct ListStruct *l = make_list((int[]){{{self._list_literal(model)}}}, {len(model)});",
                self._assert_accessors_code(model, f"std_{idx}_pop_start"),
                "list_pop(l, NULL);",
                self._assert_accessors_code(model, f"std_{idx}_pop_null"),
            ]

            model = model[1:]
            lines.extend([
                "list_pop(l, list_get(l, 0));",
                self._assert_accessors_code(model, f"std_{idx}_pop_head"),
            ])

            model = model[:-1]
            lines.extend([
                "list_pop(l, list_get(l, list_count(l) - 1));",
                self._assert_accessors_code(model, f"std_{idx}_pop_tail"),
            ])

            model = [model[0]]
            lines.extend([
                "list_pop(l, list_get(l, 1));",
                self._assert_accessors_code(model, f"std_{idx}_pop_middle"),
            ])

            model = []
            lines.extend([
                "list_pop(l, list_get(l, 0));",
                self._assert_accessors_code(model, f"std_{idx}_pop_last"),
                "list_destroy(l);",
                "}",
            ])
            blocks.append("\n".join(lines))

        if list_type == 2:
            model = []
            lines = ["{", "struct ListStruct *l = list_init();"]

            model = [10]
            lines.extend([
                "list_insert_at(l, 0, 10);",
                self._assert_accessors_code(model, f"std_{idx}_insert_at_0"),
            ])

            model = [5, 10]
            lines.extend([
                "list_insert_at(l, -5, 5);",
                self._assert_accessors_code(model, f"std_{idx}_insert_at_front"),
            ])

            model = [5, 7, 10]
            lines.extend([
                "list_insert_at(l, 1, 7);",
                self._assert_accessors_code(model, f"std_{idx}_insert_at_middle"),
            ])

            model = [5, 7, 10, 12]
            lines.extend([
                "list_insert_at(l, 99, 12);",
                self._assert_accessors_code(model, f"std_{idx}_insert_at_back"),
            ])

            model = [5, 7, 10, 9, 12]
            lines.extend([
                "list_insert_at(l, 3, 9);",
                self._assert_accessors_code(model, f"std_{idx}_insert_at_second_middle"),
                "list_destroy(l);",
                "}",
            ])
            blocks.append("\n".join(lines))
        elif insert_mode == 0:
            model = [1, 2, 3]
            lines = [
                "{",
                f"struct ListStruct *l = make_list((int[]){{{self._list_literal(model)}}}, {len(model)});",
                self._assert_accessors_code(model, f"std_{idx}_insert_before_start"),
            ]

            model = [1, 2, 3, 9]
            lines.extend([
                "list_insert_before(l, NULL, 9);",
                self._assert_accessors_code(model, f"std_{idx}_insert_before_null"),
            ])

            model = [8, 1, 2, 3, 9]
            lines.extend([
                "list_insert_before(l, list_get_head(l), 8);",
                self._assert_accessors_code(model, f"std_{idx}_insert_before_head"),
            ])

            model = [8, 1, 7, 2, 3, 9]
            lines.extend([
                "list_insert_before(l, list_get(l, 2), 7);",
                self._assert_accessors_code(model, f"std_{idx}_insert_before_middle"),
                "list_destroy(l);",
                "}",
            ])
            blocks.append("\n".join(lines))
        else:
            model = [1, 2, 3]
            lines = [
                "{",
                f"struct ListStruct *l = make_list((int[]){{{self._list_literal(model)}}}, {len(model)});",
                self._assert_accessors_code(model, f"std_{idx}_insert_after_start"),
            ]

            model = [9, 1, 2, 3]
            lines.extend([
                "list_insert_after(l, NULL, 9);",
                self._assert_accessors_code(model, f"std_{idx}_insert_after_null"),
            ])

            model = [9, 1, 2, 3, 8]
            lines.extend([
                "list_insert_after(l, list_get_tail(l), 8);",
                self._assert_accessors_code(model, f"std_{idx}_insert_after_tail"),
            ])

            model = [9, 1, 2, 7, 3, 8]
            lines.extend([
                "list_insert_after(l, list_get(l, 2), 7);",
                self._assert_accessors_code(model, f"std_{idx}_insert_after_middle"),
                "list_destroy(l);",
                "}",
            ])
            blocks.append("\n".join(lines))

        return "\n".join(blocks)


    def _core_call(self, code: int, arr: list[int], params: dict[str, int], idx: int) -> str:
        p = params
        if code == 0: return f"ASSERT_INT(list_count_greater(l, {p['X']}), {_count_greater(arr, p['X'])});"
        if code == 1: return f"ASSERT_INT(list_sum_divisible(l, {p['D']}), {_sum_divisible(arr, p['D'])});"
        if code == 2: return f"ASSERT_INT(list_count_range(l, {p['A']}, {p['B']}), {_count_range(arr, p['A'], p['B'])});"
        if code == 3: return f"ASSERT_INT(list_sum_by_step(l, {p['P']}, {p['K']}), {_sum_by_step(arr, p['P'], p['K'])});"
        if code == 5: return f"ASSERT_INT(__lab6_index_of_node(l, list_find_first_greater(l, {p['X']})), {_first_greater(arr, p['X'])});"
        if code == 9: return f"ASSERT_INT(list_find_last_less_index(l, {p['X']}), {_last_less(arr, p['X'])});"
        if code == 10: return f"ASSERT_INT(list_has_range_value(l, {p['A']}, {p['B']}) ? 1 : 0, {int(_has_range(arr, p['A'], p['B']))});"
        if code == 12: return f"ASSERT_INT(list_sum_index_range(l, {p['P']}, {p['R']}), {_sum_index_range(arr, p['P'], p['R'])});"
        if code == 14: return f"ASSERT_INT(list_is_alternating_by_x(l, {p['X']}) ? 1 : 0, {int(_alternating(arr, p['X']))});"
        if code == 18: return f"ASSERT_INT(list_count_neighbor_pairs_sum(l, {p['S']}), {_pairs_sum(arr, p['S'])});"
        if code == 19: return f"ASSERT_INT(list_all_by_step_greater(l, {p['P']}, {p['K']}, {p['X']}) ? 1 : 0, {int(_all_step_gt(arr, p['P'], p['K'], p['X']))});"
        if code == 4:
            exp = _rotate_right(arr, p['K'])
            return self._expect_code(exp, f"e{idx}") + f"\nlist_rotate_right(l, {p['K']}); ASSERT_LIST(e{idx}, e{idx}_n);"
        if code == 6:
            exp = _partition(arr, p['X'])
            return self._expect_code(exp, f"e{idx}") + f"\nlist_partition(l, {p['X']}); ASSERT_LIST(e{idx}, e{idx}_n);"
        if code == 7:
            exp = _remove_equal(arr, p['X'])
            return self._expect_code(exp, f"e{idx}") + f"\nlist_remove_all_equal(l, {p['X']}); ASSERT_LIST(e{idx}, e{idx}_n);"
        if code == 8:
            exp = _replace_value(arr, p['X'], p['VALUE'])
            return self._expect_code(exp, f"e{idx}") + f"\nlist_replace_value(l, {p['X']}, {p['VALUE']}); ASSERT_LIST(e{idx}, e{idx}_n);"
        if code == 11:
            exp = _remove_out(arr, p['A'], p['B'])
            return self._expect_code(exp, f"e{idx}") + f"\nlist_remove_out_of_range(l, {p['A']}, {p['B']}); ASSERT_LIST(e{idx}, e{idx}_n);"
        if code == 13:
            exp = _multiply_step(arr, p['P'], p['K'], p['M'])
            return self._expect_code(exp, f"e{idx}") + f"\nlist_multiply_by_step(l, {p['P']}, {p['K']}, {p['M']}); ASSERT_LIST(e{idx}, e{idx}_n);"
        if code == 15:
            exp = _clamp(arr, p['A'], p['B'])
            return self._expect_code(exp, f"e{idx}") + f"\nlist_clamp(l, {p['A']}, {p['B']}); ASSERT_LIST(e{idx}, e{idx}_n);"
        if code == 16:
            exp = _insert_after_divisible(arr, p['D'], p['VALUE'])
            return self._expect_code(exp, f"e{idx}") + f"\nlist_insert_value_after_divisible(l, {p['D']}, {p['VALUE']}); ASSERT_LIST(e{idx}, e{idx}_n);"
        exp = _compress_x(arr, p['X'])
        return self._expect_code(exp, f"e{idx}") + f"\nlist_compress_x_runs(l, {p['X']}); ASSERT_LIST(e{idx}, e{idx}_n);"

    def _make_harness(self, solution_name: str) -> str:
        v = self._build_variant()

        generated_arrays = [test["array"] for test in self.generate_tests()]
        fixed_arrays = [
            [],
            [5],
            [1, 2],
            [3, -1, 4, 3],
            [0, -2, 7, 7, -2, 5],
        ]

        standard_arrays: list[list[int]] = []
        for arr in generated_arrays + fixed_arrays:
            if arr not in standard_arrays:
                standard_arrays.append(arr)

        std_tests = [
            self._standard_test_code(arr, i)
            for i, arr in enumerate(standard_arrays)
        ]

        core_tests = []
        for i, arr in enumerate(generated_arrays + fixed_arrays):
            for code in v["CORES"]:
                core_tests.append(
                    "{\n"
                    + f"struct ListStruct *l = make_list((int[]){{{self._list_literal(arr)}}}, {len(arr)});\n"
                    + self._core_call(code, arr, v["params"], i * 100 + code)
                    + "\nlist_destroy(l);\n"
                    + "}"
                )

        return f"""
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

{self._struct_code(v['LIST_TYPE'])}

#include \"{solution_name}\"

{self._dump_code(v['LIST_TYPE'])}

int __lab6_index_of_node(struct ListStruct *l, struct ListNode *target) {{
    if (!target) return -1;
    int out[1000];
    int n = dump(l, out);
    for (int i = 0; i < n; i++) {{
        if (__lab6_expected_node(l, i) == target) return i;
    }}
    return -2;
}}

#define ASSERT_INT(a,b) do {{ \
    int _got = (int)(a); \
    int _expected = (int)(b); \
    if (_got != _expected) {{ \
        printf(\"FAIL int: %d != %d\\n\", _got, _expected); \
        return 1; \
    }} \
}} while(0)

#define ASSERT_PTR_NOT_NULL(p) do {{ \
    if ((p) == NULL) {{ \
        printf(\"FAIL ptr: unexpected NULL\\n\"); \
        return 1; \
    }} \
}} while(0)

#define ASSERT_PTR_EQ(a,b) do {{ \
    void *_got = (void *)(a); \
    void *_expected = (void *)(b); \
    if (_got != _expected) {{ \
        printf(\"FAIL ptr: %p != %p\\n\", _got, _expected); \
        return 1; \
    }} \
}} while(0)

#define ASSERT_LIST(e,n) do {{ \
    int out[1000]; \
    int got = dump(l, out); \
    if (got != (n)) {{ \
        printf(\"FAIL count: %d != %d\\n\", got, (n)); \
        return 1; \
    }} \
    for (int qi = 0; qi < got; qi++) {{ \
        if (out[qi] != (e)[qi]) {{ \
            printf(\"FAIL list at %d: %d != %d\\n\", qi, out[qi], (e)[qi]); \
            return 1; \
        }} \
    }} \
}} while(0)

#define ASSERT_ACCESSORS(e,n) do {{ \
    ASSERT_INT(__lab6_validate_structure(l, (n)), 1); \
    ASSERT_INT(list_count(l), (n)); \
    ASSERT_INT(list_is_empty(l) ? 1 : 0, ((n) == 0) ? 1 : 0); \
    ASSERT_PTR_EQ(list_get_head(l), (l)->head); \
    ASSERT_PTR_EQ(list_get_tail(l), __lab6_expected_tail(l)); \
    ASSERT_PTR_EQ(list_get(l, -1), NULL); \
    ASSERT_PTR_EQ(list_get(l, (n)), NULL); \
    for (int ai = 0; ai < (n); ai++) {{ \
        ASSERT_PTR_EQ(list_get(l, ai), __lab6_expected_node(l, ai)); \
    }} \
    ASSERT_LIST(e, n); \
}} while(0)

struct ListStruct *make_list(int *a, int n) {{
    struct ListStruct *l = list_init();
    if (!l) return NULL;
    for (int i = 0; i < n; i++) list_push_back(l, a[i]);
    return l;
}}

int main(void) {{
{chr(10).join(std_tests)}

{chr(10).join(core_tests)}

printf(\"OK\\n\");
return 0;
}}
"""

    def check(self, solution_path: str) -> tuple[bool, str]:
        src = Path(solution_path)
        if not src.exists():
            return False, f"Solution file not found: {solution_path}"
        build = Path(tempfile.mkdtemp(prefix="lab6-"))
        try:
            shutil.copy(src, build / "solution.c")
            (build / "test.c").write_text(self._make_harness("solution.c"), encoding="utf-8")
            exe = build / "test"
            cmd = [self.compiler, "-std=c11", "-Wall", "-Wextra", str(build / "test.c"), "-o", str(exe)]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            if res.returncode != 0:
                return False, "Ошибка компиляции решения:\n" + res.stdout
            run = subprocess.run([str(exe)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            if run.returncode != 0:
                details = run.stdout.strip()
                if not details:
                    details = f"Решение завершилось с кодом {run.returncode}, но не вывело диагностическое сообщение."
                return False, "Тесты не пройдены:\n" + details
            return True, "Все тесты пройдены"
        finally:
            shutil.rmtree(build, ignore_errors=True)
