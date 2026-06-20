#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>

#define BASE 234
#define TOKEN_SIZE 256

int parse_number(const char *text) {
    int sign = 1;
    int value = 0;
    int index = 0;

    if (text[index] == '-') {
        sign = -1;
        index++;
    }

    while (text[index] != '\0') {
        int digit = 0;

        if (!isdigit((unsigned char)text[index])) {
            exit(1);
        }

        while (isdigit((unsigned char)text[index])) {
            digit = digit * 10 + text[index] - '0';
            index++;
        }

        if (digit >= BASE) {
            exit(1);
        }

        value = value * BASE + digit;

        if (text[index] == ':') {
            index++;
            if (text[index] == '\0') {
                exit(1);
            }
        } else if (text[index] != '\0') {
            exit(1);
        }
    }

    return sign * value;
}

void print_number(int value) {
    int parts[64];
    int count = 0;

    if (value < 0) {
        putchar('-');
        value = -value;
    }

    if (value == 0) {
        printf("0\n");
        return;
    }

    while (value > 0) {
        parts[count++] = value % BASE;
        value /= BASE;
    }

    for (int i = count - 1; i >= 0; i--) {
        printf("%d", parts[i]);
        if (i > 0) {
            putchar(':');
        }
    }

    putchar('\n');
}

int main(void) {
    const int M = 9;
    const int P = 8;
    const int K = 5;
    const int L = 2;

    int *arr = NULL;
    int size = 0;
    int capacity = 16;
    char token[TOKEN_SIZE];

    arr = (int *)malloc((size_t)capacity * sizeof(int));
    if (arr == NULL) {
        return 1;
    }

    while (scanf("%255s", token) == 1) {
        if (size >= capacity) {
            capacity *= 2;
            int *new_arr = (int *)realloc(arr, (size_t)capacity * sizeof(int));
            if (new_arr == NULL) {
                free(arr);
                return 1;
            }
            arr = new_arr;
        }

        arr[size++] = parse_number(token);
    }

    int result1 = -1;
    for (int i = 0; i < size; i++) {
        if (arr[i] % M == 0) {
            result1 = i;
            break;
        }
    }
    print_number(result1);

    int result2 = 0;
    for (int i = P; i < size; i += K) {
        result2 += abs(arr[i]);
    }
    print_number(result2);

    int result3 = 0;
    for (int i = 0; i < size; i++) {
        if (abs(arr[i]) < L) {
            result3++;
        }
    }
    print_number(result3);

    free(arr);
    return 0;
}