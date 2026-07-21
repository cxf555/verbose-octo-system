#pragma once
#include "utils.h"

typedef struct Borrow {
    int    id;
    int    book_id;
    int    reader_id;
    char   borrow_date[MAX_DATE_LEN];
    char   due_date[MAX_DATE_LEN];
    char   return_date[MAX_DATE_LEN];  /* "" means not returned */
    struct Borrow *next;
} Borrow;

void    borrow_init(void);
void    borrow_save(void);
void    borrow_free(void);
void    borrow_book(void);
void    return_book(void);
void    borrow_search(void);
void    borrow_check_overdue(void);
Borrow *borrow_find_by_id(int id);
Borrow *borrow_get_head(void);
int     borrow_has_active_for_book(int book_id);
int     borrow_has_active_for_reader(int reader_id);
int     borrow_count_active_by_reader(int reader_id);
