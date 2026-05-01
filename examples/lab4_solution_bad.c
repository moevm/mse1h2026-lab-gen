#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

#define MAX_LEN 1024


/*Пример неправильного решения варианта задачи для seed = 2:
Напишите программу на языке Си, которая читает строку элементов, обрабатывает её и выводит результат, используя функции стандартной библиотеки.
На вход программе подаются:
- строка с элементами
- строка-запрос
Общие требования:
- Считать строку элементов и стоку-запрос
- Разделить строку на элементы по следующим разделителям (сами разделители удаляются): ', '
- После разделения строки пустые элементы необходимо удалить
- Среди оставшихся элементов выполнить отбор по правилу:
        Выбрать только те элементы, каждый символ которых является буквой.
Отсортировать оставшиеся элементы по правилу:
        Отсортировать выбранные элементы лексикографически по возрастанию.
- Если образовались одинаковые элементы, то нужно оставить все из них
- определить наличие строки-запроса среди выбранных элементов через bsearch
В качестве ответа нужно вывести:
- Полученные после обработки элементы в одну строку через пробел
- Вывести результат поиска строки-запроса среди элементов (exists/doesn't exist)
- Вывести Вывести длину самого короткого элемента в отобранном наборе*/


// Проверка: состоит ли строка только из букв
int is_alpha_string(const char *str) {
    for (int i = 0; str[i]; i++) {
        if (!isalpha((unsigned char)str[i])) {
            return 0;
        }
    }
    return 1;
}

// Компаратор для qsort / bsearch
int cmp_str(const void *a, const void *b) {
    const char *s1 = *(const char **)a;
    const char *s2 = *(const char **)b;
    return strcmp(s1, s2);
}

int main() {
    char input[MAX_LEN];
    char query[MAX_LEN];

    // Чтение строк
    fgets(input, MAX_LEN, stdin);
    fgets(query, MAX_LEN, stdin);

    // Удаляем '\n'
    input[strcspn(input, "\n")] = '\0';
    query[strcspn(query, "\n")] = '\0';

    // Массив для хранения подходящих строк
    char **words = NULL;
    int count = 0;

    // Разбиение строки
    char *token = strtok(input, ", ");
    while (token != NULL) {
        if (strlen(token) > 0 && is_alpha_string(token)) {
            words = realloc(words, (count + 1) * sizeof(char *));
            words[count] = strdup(token);
            count++;
        }
        token = strtok(NULL, ", ");
    }

    // Сортировка
    qsort(words, count, sizeof(char *), cmp_str);

    // Вывод элементов
    for (int i = 0; i < count; i++) {
        printf("%s", words[i]);
        if (i < count - 1) printf(" ");
    }
    if (count == 0) {
        printf("empty");
    }
    printf("\n");

    // Поиск через bsearch
    char *key = query;
    char **found = bsearch(&key, words, count, sizeof(char *), cmp_str);

    if (found) {
        printf("exists\n");
    } else {
        printf("doesn't exist\n");
    }

    // Поиск минимальной длины
    if (count > 0) {
        int min_len = strlen(words[0]);
        for (int i = 1; i < count; i++) {
            int len = strlen(words[i]);
            if (len > min_len) {
                min_len = len;
            }
        }
        printf("summary: minlen=%d\n", min_len);
    } else {
        printf("summary: minlen=0\n");
    }

    // Освобождение памяти
    for (int i = 0; i < count; i++) {
        free(words[i]);
    }
    free(words);

    return 0;
}