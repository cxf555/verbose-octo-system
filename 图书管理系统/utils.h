#pragma once

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define MAX_TITLE_LEN      100
#define MAX_AUTHOR_LEN      50
#define MAX_PUBLISHER_LEN   50
#define MAX_CATEGORY_LEN    30
#define MAX_NAME_LEN        50
#define MAX_DEPT_LEN        50
#define MAX_PHONE_LEN       20
#define MAX_DATE_LEN        11
#define DEFAULT_BORROW_DAYS 30
#define DEFAULT_MAX_BORROW  5
#define DATA_DIR            "data"
#define BOOKS_FILE          "data/books.dat"
#define READERS_FILE        "data/readers.dat"
#define BORROWS_FILE        "data/borrows.dat"

void clear_screen(void);
void pause_screen(void);
int  get_int_input(const char *prompt);
void get_string_input(const char *prompt, char *buffer, int max_len);
int  is_valid_date(const char *date);
void calculate_due_date(const char *borrow_date, char *due_date, int days);
int  is_overdue(const char *due_date);
void get_current_date(char *date);
int  str_contains(const char *str, const char *substr);
void ensure_data_dir(void);
