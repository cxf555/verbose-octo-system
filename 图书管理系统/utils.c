#define _CRT_SECURE_NO_WARNINGS
#include "utils.h"
#include <sys/stat.h>
#include <sys/types.h>

#ifdef _WIN32
#include <direct.h>
#define MKDIR(path) _mkdir(path)
#else
#define MKDIR(path) mkdir(path, 0755)
#endif

void clear_screen(void) {
    system("cls");
}

void pause_screen(void) {
    printf("\n按任意键返回...");
    getchar();
}

int get_int_input(const char *prompt) {
    int value;
    char buffer[32];
    while (1) {
        printf("%s", prompt);
        if (fgets(buffer, sizeof(buffer), stdin) == NULL) continue;
        if (sscanf(buffer, "%d", &value) == 1) return value;
        printf("输入无效，请输入整数。\n");
    }
}

void get_string_input(const char *prompt, char *buffer, int max_len) {
    printf("%s", prompt);
    if (fgets(buffer, max_len, stdin) == NULL) {
        buffer[0] = '\0';
        return;
    }
    size_t len = strlen(buffer);
    if (len > 0 && buffer[len - 1] == '\n') buffer[len - 1] = '\0';
}

int is_valid_date(const char *date) {
    if (strlen(date) != 10) return 0;
    if (date[4] != '-' || date[7] != '-') return 0;
    for (int i = 0; i < 10; i++) {
        if (i == 4 || i == 7) continue;
        if (date[i] < '0' || date[i] > '9') return 0;
    }
    int year, month, day;
    sscanf(date, "%d-%d-%d", &year, &month, &day);
    if (year < 2000 || year > 2100) return 0;
    if (month < 1 || month > 12) return 0;
    int days_in_month[] = {0,31,28,31,30,31,30,31,31,30,31,30,31};
    if ((year % 4 == 0 && year % 100 != 0) || (year % 400 == 0))
        days_in_month[2] = 29;
    if (day < 1 || day > days_in_month[month]) return 0;
    return 1;
}

void calculate_due_date(const char *borrow_date, char *due_date, int days) {
    int year, month, day;
    sscanf(borrow_date, "%d-%d-%d", &year, &month, &day);
    int days_in_month[] = {0,31,28,31,30,31,30,31,31,30,31,30,31};
    while (days > 0) {
        if ((year % 4 == 0 && year % 100 != 0) || (year % 400 == 0))
            days_in_month[2] = 29;
        else
            days_in_month[2] = 28;
        int remaining = days_in_month[month] - day;
        if (days <= remaining) {
            day += days;
            days = 0;
        } else {
            days -= (remaining + 1);
            day = 1;
            month++;
            if (month > 12) { month = 1; year++; }
        }
    }
    sprintf(due_date, "%04d-%02d-%02d", year, month, day);
}

int is_overdue(const char *due_date) {
    char today[11];
    get_current_date(today);
    return strcmp(due_date, today) < 0;  /* due_date < today means overdue */
}

void get_current_date(char *date) {
    time_t t = time(NULL);
    struct tm *tm_info = localtime(&t);
    strftime(date, 11, "%Y-%m-%d", tm_info);
}

int str_contains(const char *str, const char *substr) {
    if (*substr == '\0') return 1;
    while (*str) {
        const char *s = str;
        const char *p = substr;
        while (*s && *p) {
            char c1 = *s, c2 = *p;
            if (c1 >= 'A' && c1 <= 'Z') c1 += 32;
            if (c2 >= 'A' && c2 <= 'Z') c2 += 32;
            if (c1 != c2) break;
            s++; p++;
        }
        if (*p == '\0') return 1;
        str++;
    }
    return 0;
}

void ensure_data_dir(void) {
    MKDIR(DATA_DIR);
}
