#pragma once
#include "utils.h"

typedef struct Book {
    int    id;
    char   title[MAX_TITLE_LEN];
    char   author[MAX_AUTHOR_LEN];
    char   publisher[MAX_PUBLISHER_LEN];
    char   category[MAX_CATEGORY_LEN];
    int    total;
    int    available;
    struct Book *next;
} Book;

void  book_init(void);
void  book_save(void);
void  book_free(void);
void  book_add(void);
void  book_delete(int id);
void  book_modify(int id);
void  book_search(void);
void  book_list_all(void);
Book *book_find_by_id(int id);
Book *book_get_head(void);
int   book_count_borrow(int book_id);
