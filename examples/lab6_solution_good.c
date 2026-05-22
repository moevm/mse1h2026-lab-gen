#include <stdbool.h>
#include <stdint.h>
#include <stdlib.h>

static struct ListNode *xnode(struct ListNode *a, struct ListNode *b) {
    return (struct ListNode *)((uintptr_t)a ^ (uintptr_t)b);
}

static struct ListNode *new_node(int data) {
    struct ListNode *n = malloc(sizeof(struct ListNode));
    n->data = data;
    n->link = NULL;
    return n;
}

struct ListStruct *list_init(void) {
    struct ListStruct *l = malloc(sizeof(struct ListStruct));
    l->head = NULL;
    return l;
}

void list_destroy(struct ListStruct *list) {
    if (!list) return;
    struct ListNode *prev = NULL, *cur = list->head;
    while (cur) {
        struct ListNode *next = xnode(prev, cur->link);
        free(cur);
        prev = cur;
        cur = next;
    }
    free(list);
}

bool list_is_empty(struct ListStruct *list) {
    return !list || !list->head;
}

int list_count(struct ListStruct *list) {
    int c = 0;
    struct ListNode *prev = NULL, *cur = list ? list->head : NULL;
    while (cur) {
        struct ListNode *next = xnode(prev, cur->link);
        c++;
        prev = cur;
        cur = next;
    }
    return c;
}

struct ListNode *list_get_head(struct ListStruct *list) {
    return list ? list->head : NULL;
}

struct ListNode *list_get_tail(struct ListStruct *list) {
    struct ListNode *prev = NULL, *cur = list ? list->head : NULL;
    while (cur) {
        struct ListNode *next = xnode(prev, cur->link);
        if (!next) return cur;
        prev = cur;
        cur = next;
    }
    return NULL;
}

struct ListNode *list_get(struct ListStruct *list, int index) {
    int i = 0;
    struct ListNode *prev = NULL, *cur = list ? list->head : NULL;
    while (cur) {
        if (i == index) return cur;
        struct ListNode *next = xnode(prev, cur->link);
        prev = cur;
        cur = next;
        i++;
    }
    return NULL;
}

void list_push_front(struct ListStruct *list, int data) {
    struct ListNode *n = new_node(data);
    struct ListNode *old = list->head;
    n->link = xnode(NULL, old);
    if (old) {
        struct ListNode *second = xnode(NULL, old->link);
        old->link = xnode(n, second);
    }
    list->head = n;
}

void list_push_back(struct ListStruct *list, int data) {
    if (!list->head) {
        list_push_front(list, data);
        return;
    }
    struct ListNode *prev = NULL, *cur = list->head;
    while (xnode(prev, cur->link)) {
        struct ListNode *next = xnode(prev, cur->link);
        prev = cur;
        cur = next;
    }
    struct ListNode *n = new_node(data);
    cur->link = xnode(prev, n);
    n->link = xnode(cur, NULL);
}

void list_pop(struct ListStruct *list, struct ListNode *node) {
    if (!list || !node) return;
    struct ListNode *prev = NULL, *cur = list->head;
    while (cur && cur != node) {
        struct ListNode *next = xnode(prev, cur->link);
        prev = cur;
        cur = next;
    }
    if (!cur) return;
    struct ListNode *next = xnode(prev, cur->link);
    if (prev) {
        struct ListNode *pp = xnode(prev->link, cur);
        prev->link = xnode(pp, next);
    } else {
        list->head = next;
    }
    if (next) {
        struct ListNode *nn = xnode(next->link, cur);
        next->link = xnode(prev, nn);
    }
    free(cur);
}

void list_insert_after(struct ListStruct *list, struct ListNode *node, int data) {
    if (!node) {
        list_push_front(list, data);
        return;
    }
    struct ListNode *prev = NULL, *cur = list->head;
    while (cur && cur != node) {
        struct ListNode *next = xnode(prev, cur->link);
        prev = cur;
        cur = next;
    }
    if (!cur) return;
    struct ListNode *next = xnode(prev, cur->link);
    struct ListNode *n = new_node(data);
    n->link = xnode(cur, next);
    cur->link = xnode(prev, n);
    if (next) {
        struct ListNode *nn = xnode(next->link, cur);
        next->link = xnode(n, nn);
    }
}

void list_sort(struct ListStruct *list) {
    int n = list_count(list);
    for (int i = 0; i < n; i++) {
        struct ListNode *a = list_get(list, i);
        for (int j = i + 1; j < n; j++) {
            struct ListNode *b = list_get(list, j);
            if (a->data > b->data) {
                int t = a->data;
                a->data = b->data;
                b->data = t;
            }
        }
    }
}

int list_find_last_less_index(struct ListStruct *list, int x) {
    int ans = -1, i = 0;
    struct ListNode *prev = NULL, *cur = list ? list->head : NULL;
    while (cur) {
        if (cur->data < x) ans = i;
        struct ListNode *next = xnode(prev, cur->link);
        prev = cur;
        cur = next;
        i++;
    }
    return ans;
}

void list_clamp(struct ListStruct *list, int a, int b) {
    struct ListNode *prev = NULL, *cur = list ? list->head : NULL;
    while (cur) {
        if (cur->data < a) cur->data = a;
        if (cur->data > b) cur->data = b;
        struct ListNode *next = xnode(prev, cur->link);
        prev = cur;
        cur = next;
    }
}

void list_partition(struct ListStruct *list, int x) {
    int n = list_count(list);
    int *v = malloc(sizeof(int) * (n > 0 ? n : 1));
    int k = 0;
    for (int pass = 0; pass < 2; pass++) {
        struct ListNode *prev = NULL, *cur = list->head;
        while (cur) {
            if ((pass == 0 && cur->data < x) || (pass == 1 && cur->data >= x)) v[k++] = cur->data;
            struct ListNode *next = xnode(prev, cur->link);
            prev = cur;
            cur = next;
        }
    }
    for (int i = 0; i < n; i++) list_get(list, i)->data = v[i];
    free(v);
}

bool list_is_alternating_by_x(struct ListStruct *list, int x) {
    struct ListNode *prev = NULL, *cur = list ? list->head : NULL;
    int have = 0, last = 0;
    while (cur) {
        int now = cur->data < x;
        if (have && now == last) return false;
        have = 1;
        last = now;
        struct ListNode *next = xnode(prev, cur->link);
        prev = cur;
        cur = next;
    }
    return true;
}
