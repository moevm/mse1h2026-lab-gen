from __future__ import annotations

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
        for i in range(self.tests_count):
            arr = self._make_array(f"test-{i}")
            expected_stdout = "\n".join(self._expected_lines_for_array(arr)) + "\n"
            tests.append({
                "input_array": arr,
                "stdin": "",
                "expected_stdout": expected_stdout,
                "array": arr,
            })
        return tests


    def check(self, solution_path: str) -> tuple[bool, str]:
        return False, "Lab6 checker is not implemented yet"
