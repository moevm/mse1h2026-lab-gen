#include <stdio.h>
#include <stdlib.h>

int main() {
    // Параметры подзадач
    const int M = 9;      // для подзадачи 1
    const int P = 8;      // для подзадачи 2
    const int K = 5;      // для подзадачи 2
    const int L = 2;      // для подзадачи 3

    // Динамический массив для хранения чисел
    int *arr = NULL;
    int size = 0;
    int capacity = 10;
    int num;

    // Выделяем начальную память
    arr = (int*)malloc(capacity * sizeof(int));
    if (arr == NULL) {
        fprintf(stderr, "Ошибка выделения памяти\n");
        return 1;
    }

    // Чтение массива из stdin
    while (scanf("%d", &num) == 1) {
        // Если нужно расширить массив
        if (size >= capacity) {
            capacity *= 2;
            int *new_arr = (int*)realloc(arr, capacity * sizeof(int));
            if (new_arr == NULL) {
                fprintf(stderr, "Ошибка выделения памяти\n");
                free(arr);
                return 1;
            }
            arr = new_arr;
        }
        arr[size++] = num;
    }

    // Подзадача 1: первый элемент, кратный M
    int result1 = -1;
    for (int i = 0; i < size; i++) {
        if (arr[i] % M == 0) {
            result1 = i;
            break;
        }
    }
    printf("%d\n", result1);

    // Подзадача 2: сумма модулей на позициях P, P+K, P+2K, ...
    int result2 = 0;
    for (int i = P; i < size; i += K) {
        result2 += abs(arr[i]);
    }
    printf("%d\n", result2);

    // Подзадача 3: количество элементов с |a[i]| < L
    int result3 = 0;
    for (int i = 0; i < size; i++) {
        if (abs(arr[i]) < L) {
            result3++;
        }
    }
    printf("%d\n", result3);

    // Освобождаем память
    free(arr);

    return 0;
}