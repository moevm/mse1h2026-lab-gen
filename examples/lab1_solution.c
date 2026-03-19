#include <stdio.h>

#define MAX_SIZE 128

static int read_array(int arr[], int max_size) {
    int size = 0;

    while (size < max_size && scanf("%d", &arr[size]) == 1) {
        size++;
        int ch = getchar();
        if (ch == '\n' || ch == EOF) {
            break;
        }
        if (ch != ' ') {
            ungetc(ch, stdin);
        }
    }

    return size;
}

static int ans_first_multiple_index(const int arr[], int size, int m) {
    if (m == 0) {
        return -1;
    }
    for (int i = 0; i < size; ++i) {
        if (arr[i] % m == 0) {
            return i;
        }
    }
    return -1;
}

static int ans_last_abs_gt_index(const int arr[], int size, int t) {
    for (int i = size - 1; i >= 0; --i) {
        int value = arr[i] < 0 ? -arr[i] : arr[i];
        if (value > t) {
            return i;
        }
    }
    return -1;
}

static int ans_count_in_range(const int arr[], int size, int a, int b) {
    int count = 0;
    for (int i = 0; i < size; ++i) {
        if (a <= arr[i] && arr[i] <= b) {
            count++;
        }
    }
    return count;
}

static int ans_sum_abs_step(const int arr[], int size, int p, int k_step) {
    int total = 0;
    if (p >= size || k_step < 1) {
        return 0;
    }
    for (int i = p; i < size; i += k_step) {
        total += arr[i] < 0 ? -arr[i] : arr[i];
    }
    return total;
}

static int ans_sum_divisible(const int arr[], int size, int d) {
    int total = 0;
    if (d == 0) {
        return 0;
    }
    for (int i = 0; i < size; ++i) {
        if (arr[i] % d == 0) {
            total += arr[i];
        }
    }
    return total;
}

static int ans_count_abs_lt(const int arr[], int size, int limit) {
    int count = 0;
    for (int i = 0; i < size; ++i) {
        int value = arr[i] < 0 ? -arr[i] : arr[i];
        if (value < limit) {
            count++;
        }
    }
    return count;
}

int main(void) {
    int arr[MAX_SIZE];
    int size = read_array(arr, MAX_SIZE);

    printf("%d\n", ans_last_abs_gt_index(arr, size, 2));
    printf("%d\n", ans_count_in_range(arr, size, 8, 85));
    printf("%d\n", ans_sum_divisible(arr, size, 7));

    return 0;
}
