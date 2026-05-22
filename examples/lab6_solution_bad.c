#include <stdbool.h>
#include <stdlib.h>

struct ListStruct *list_init(void) { return NULL; }
void list_destroy(struct ListStruct *list) { (void)list; }
void list_push_front(struct ListStruct *list, int data) { (void)list; (void)data; }
void list_push_back(struct ListStruct *list, int data) { (void)list; (void)data; }
void list_pop(struct ListStruct *list, struct ListNode *node) { (void)list; (void)node; }
int list_count(struct ListStruct *list) { (void)list; return 0; }
struct ListNode *list_get_head(struct ListStruct *list) { (void)list; return NULL; }
struct ListNode *list_get_tail(struct ListStruct *list) { (void)list; return NULL; }
struct ListNode *list_get(struct ListStruct *list, int index) { (void)list; (void)index; return NULL; }
bool list_is_empty(struct ListStruct *list) { (void)list; return true; }
void list_sort(struct ListStruct *list) { (void)list; }
void list_insert_after(struct ListStruct *list, struct ListNode *node, int data) { (void)list; (void)node; (void)data; }
int list_find_last_less_index(struct ListStruct *list, int x) { (void)list; (void)x; return -1; }
void list_clamp(struct ListStruct *list, int a, int b) { (void)list; (void)a; (void)b; }
void list_partition(struct ListStruct *list, int x) { (void)list; (void)x; }
bool list_is_alternating_by_x(struct ListStruct *list, int x) { (void)list; (void)x; return true; }
