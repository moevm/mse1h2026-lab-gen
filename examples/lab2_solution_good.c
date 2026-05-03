#include <stdio.h>

#define MAX_SIZE 100

static int input(int arr[], int max_size) {
    int size = 0;
    while (size < max_size && scanf("%d", &arr[size]) == 1) {
        size++;
    }
    return size;
}

static void output(const int arr[], int size) {
    for (int i = 0; i < size; ++i) {
        if (i > 0) {
            printf(" ");
        }
        printf("%d", arr[i]);
    }
    printf("\n");
}

static void reverse_1_1(int arr[], int size) {
    (void)arr;
    (void)size;
}

static void interleave_ends(int arr[], int size) {
    int tmp[MAX_SIZE];
    int left = 0;
    int right = size - 1;
    int pos = 0;

    while (left <= right) {
        tmp[pos++] = arr[left];
        if (left != right) {
            tmp[pos++] = arr[right];
        }
        left++;
        right--;
    }

    for (int i = 0; i < size; ++i) {
        arr[i] = tmp[i];
    }
}

static void shift_left_1(int arr[], int size) {
    if (size <= 1) {
        return;
    }

    int first = arr[0];
    for (int i = 0; i + 1 < size; ++i) {
        arr[i] = arr[i + 1];
    }
    arr[size - 1] = first;
}

static void swap_pairs(int arr[], int size) {
    for (int i = 0; i + 1 < size; i += 2) {
        int tmp = arr[i];
        arr[i] = arr[i + 1];
        arr[i + 1] = tmp;
    }
}

int main(void) {
    int arr[MAX_SIZE];
    int size = input(arr, MAX_SIZE);

    interleave_ends(arr, size);
    reverse_1_1(arr, size);
    reverse_1_1(arr, size);
    output(arr, size);

    shift_left_1(arr, size);
    shift_left_1(arr, size);
    output(arr, size);

    shift_left_1(arr, size);
    swap_pairs(arr, size);
    swap_pairs(arr, size);
    output(arr, size);

    return 0;
}
