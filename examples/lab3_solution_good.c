#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define INITIAL_TEXT_CAPACITY 4096
#define INITIAL_WORD_CAPACITY 16

int main() {
    // Параметры варианта ЛР3
    const int WORD_COUNT = 9;       // для select_rule: число слов == 9
    const int KEYWORD_POS = 4;      // для keyword_rule: слово с номером 4
    const char TEXT_END[] = "###";  // маркер конца текста

    // Динамическая строка для хранения всего входного текста
    char *text = NULL;
    int size = 0;
    int capacity = INITIAL_TEXT_CAPACITY;
    int ch;

    // Выделяем начальную память
    text = (char*)malloc(capacity * sizeof(char));
    if (text == NULL) {
        fprintf(stderr, "Ошибка выделения памяти\n");
        return 1;
    }

    // Чтение текста из stdin
    while ((ch = getchar()) != EOF) {
        if (size + 1 >= capacity) {
            capacity *= 2;
            char *new_text = (char*)realloc(text, capacity * sizeof(char));
            if (new_text == NULL) {
                fprintf(stderr, "Ошибка выделения памяти\n");
                free(text);
                return 1;
            }
            text = new_text;
        }
        text[size++] = (char)ch;
    }
    text[size] = '\0';

    // Маркер ### не входит в обработку
    char *marker = strstr(text, TEXT_END);
    int process_size = marker == NULL ? size : (int)(marker - text);
}
