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

    // Массив ключевых слов
    char **keywords = NULL;
    int keyword_count = 0;
    int keyword_capacity = INITIAL_WORD_CAPACITY;

    keywords = (char**)malloc(keyword_capacity * sizeof(char*));
    if (keywords == NULL) {
        fprintf(stderr, "Ошибка выделения памяти\n");
        free(text);
        return 1;
    }

    int printed = 0;
    int sentence_start = 0;

    // Разбор предложений по символам . ; ? !
    for (int i = 0; i < process_size; i++) {
        if (text[i] != '.' && text[i] != ';' && text[i] != '?' && text[i] != '!') {
            continue;
        }

        char ending = text[i];
        int sentence_len = i - sentence_start;

        char *sentence = (char*)malloc((sentence_len + 1) * sizeof(char));
        if (sentence == NULL) {
            fprintf(stderr, "Ошибка выделения памяти\n");
            free(keywords);
            free(text);
            return 1;
        }

        memcpy(sentence, text + sentence_start, sentence_len);
        sentence[sentence_len] = '\0';
        sentence_start = i + 1;

        // Пробелы и табуляции в начале предложения удаляются
        char *normalized = sentence;
        while (*normalized == ' ' || *normalized == '\t') {
            normalized++;
        }

        // Делим предложение на слова
        char **words = NULL;
        int word_count = 0;
        int word_capacity = INITIAL_WORD_CAPACITY;

        words = (char**)malloc(word_capacity * sizeof(char*));
        if (words == NULL) {
            fprintf(stderr, "Ошибка выделения памяти\n");
            free(sentence);
            free(keywords);
            free(text);
            return 1;
        }

        char *token = strtok(normalized, " \t\n\r");
        while (token != NULL) {
            if (word_count >= word_capacity) {
                word_capacity *= 2;
                char **new_words = (char**)realloc(words, word_capacity * sizeof(char*));
                if (new_words == NULL) {
                    fprintf(stderr, "Ошибка выделения памяти\n");
                    free(words);
                    free(sentence);
                    free(keywords);
                    free(text);
                    return 1;
                }
                words = new_words;
            }
            words[word_count++] = token;
            token = strtok(NULL, " \t\n\r");
        }

        // select_rule: выбрать предложение, если число слов == WORD_COUNT
        if (word_count == WORD_COUNT) {
            // rewrite_rule: развернуть порядок слов
            for (int j = word_count - 1; j >= 0; j--) {
                printf("%s", words[j]);
                if (j > 0) {
                    printf(" ");
                }
            }
            printf("%c\n", ending);

            // keyword_rule: выбрать слово с номером KEYWORD_POS после преобразования
            if (keyword_count >= keyword_capacity) {
                keyword_capacity *= 2;
                char **new_keywords = (char**)realloc(keywords, keyword_capacity * sizeof(char*));
                if (new_keywords == NULL) {
                    fprintf(stderr, "Ошибка выделения памяти\n");
                    free(words);
                    free(sentence);
                    free(keywords);
                    free(text);
                    return 1;
                }
                keywords = new_keywords;
            }
            keywords[keyword_count] = strdup(words[word_count - KEYWORD_POS]);
            if (keywords[keyword_count] == NULL) {
                fprintf(stderr, "Ошибка выделения памяти\n");
                free(words);
                free(sentence);
                free(keywords);
                free(text);
                return 1;
            }
            keyword_count++;
            printed = 1;
        }

        free(words);
        free(sentence);
    }

    // Печать итогового результата
    if (!printed) {
        printf("EMPTY\n");
        printf("Key words: EMPTY\n");
    } else {
        printf("Key words:");
        for (int i = 0; i < keyword_count; i++) {
            printf(" %s", keywords[i]);
        }
        printf("\n");
    }

    // Освобождаем память
    for (int i = 0; i < keyword_count; i++) {
        free(keywords[i]);
    }
    free(keywords);
    free(text);

    return 0;
}
