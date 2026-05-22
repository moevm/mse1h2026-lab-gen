#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <regex.h>

#define MAX_LINE 4096
#define MAX_MATCHES 1024

/*
Пример правильного решения для ЛР5, seed = test123.

Вариант:
- задача: URL-ссылки;
- protocol: может быть или отсутствовать;
- path: запрещён;
- query: может быть или отсутствовать;
- port: запрещён;
- этап 2: домен оканчивается на .edu;
- этап 2: query содержит не менее 2 параметров.

Программа читает строки до Fin., считает URL, прошедшие этап 1,
и выводит URL, прошедшие оба фильтра этапа 2.
*/

static void strip_newline(char *s) {
    size_t n = strlen(s);
    while (n > 0 && (s[n - 1] == '\n' || s[n - 1] == '\r')) {
        s[n - 1] = '\0';
        n--;
    }
}

static int starts_with(const char *s, const char *prefix) {
    return strncmp(s, prefix, strlen(prefix)) == 0;
}

static int ends_with(const char *s, size_t len, const char *suffix) {
    size_t suffix_len = strlen(suffix);
    if (len < suffix_len) return 0;
    return strncmp(s + len - suffix_len, suffix, suffix_len) == 0;
}

static int is_stage1_url(const char *line, regex_t *url_regex) {
    return regexec(url_regex, line, 0, NULL, 0) == 0;
}

static const char *skip_optional_protocol(const char *line) {
    if (starts_with(line, "http://")) return line + 7;
    if (starts_with(line, "https://")) return line + 8;
    if (starts_with(line, "ftp://")) return line + 6;
    return line;
}

static int domain_ends_with_edu(const char *line) {
    const char *p = skip_optional_protocol(line);
    const char *domain_start = p;

    while (*p && *p != '?' && *p != '#') {
        p++;
    }

    return ends_with(domain_start, (size_t)(p - domain_start), ".edu");
}

static int query_param_count(const char *line) {
    const char *q = strchr(line, '?');
    if (q == NULL) return 0;

    q++;
    int count = 0;
    int current_len = 0;

    for (const char *p = q; ; p++) {
        if (*p == '&' || *p == '#' || *p == '\0') {
            if (current_len > 0) count++;
            current_len = 0;
            if (*p == '#' || *p == '\0') break;
        } else {
            current_len++;
        }
    }

    return count;
}

static int passes_stage2(const char *line) {
    return domain_ends_with_edu(line) && query_param_count(line) >= 2;
}

int main(void) {
    /*
    Этап 1 для seed=test123:
    - допустимый protocol: http://, https://, ftp:// или отсутствие protocol;
    - domain: минимум две части, латинские буквы/цифры/дефис;
    - port запрещён, поэтому ':' после domain не допускается;
    - path запрещён, поэтому '/' после domain не допускается;
    - query optional: начинается с '?';
    - fragment optional: начинается с '#'.
    */
    const char *pattern = "^((http|https|ftp)://)?[A-Za-z0-9-]+(\\.[A-Za-z0-9-]+)+(\\?[^#[:space:]]*)?(#[^[:space:]]*)?$";

    regex_t url_regex;
    if (regcomp(&url_regex, pattern, REG_EXTENDED) != 0) {
        return 1;
    }

    char line[MAX_LINE];
    char *matched[MAX_MATCHES];
    int stage1_count = 0;
    int stage2_count = 0;

    while (fgets(line, sizeof(line), stdin) != NULL) {
        strip_newline(line);
        if (strcmp(line, "Fin.") == 0) {
            break;
        }

        if (is_stage1_url(line, &url_regex)) {
            stage1_count++;
            if (passes_stage2(line) && stage2_count < MAX_MATCHES) {
                matched[stage2_count] = strdup(line);
                if (matched[stage2_count] == NULL) {
                    regfree(&url_regex);
                    return 1;
                }
                stage2_count++;
            }
        }
    }

    printf("%d\n", stage1_count);
    if (stage2_count == 0) {
        printf("Empty\n");
    } else {
        for (int i = 0; i < stage2_count; i++) {
            printf("%s\n", matched[i]);
            free(matched[i]);
        }
    }

    regfree(&url_regex);
    return 0;
}
