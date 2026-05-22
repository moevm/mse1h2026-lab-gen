#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <regex.h>

#define MAX_LINE 4096
#define MAX_MATCHES 1024

static void strip_newline(char *s) {
    size_t n = strlen(s);
    while (n > 0 && (s[n - 1] == '\n' || s[n - 1] == '\r')) {
        s[n - 1] = '\0';
        n--;
    }
}

int main(void) {
    const char *pattern = "^((http|https|ftp)://)?[A-Za-z0-9-]+(\\.[A-Za-z0-9-]+)+(\\?[^#[:space:]]*)?(#[^[:space:]]*)?$";

    regex_t url_regex;
    if (regcomp(&url_regex, pattern, REG_EXTENDED) != 0) {
        return 1;
    }

    char line[MAX_LINE];
    char *matched[MAX_MATCHES];
    int stage1_count = 0;
    int out_count = 0;

    while (fgets(line, sizeof(line), stdin) != NULL) {
        strip_newline(line);
        if (strcmp(line, "Fin.") == 0) {
            break;
        }

        if (regexec(&url_regex, line, 0, NULL, 0) == 0) {
            stage1_count++;
            if (out_count < MAX_MATCHES) {
                matched[out_count] = strdup(line);
                if (matched[out_count] == NULL) {
                    regfree(&url_regex);
                    return 1;
                }
                out_count++;
            }
        }
    }

    printf("%d\n", stage1_count);
    if (out_count == 0) {
        printf("Empty\n");
    } else {
        for (int i = 0; i < out_count; i++) {
            printf("%s\n", matched[i]);
            free(matched[i]);
        }
    }

    regfree(&url_regex);
    return 0;
}
