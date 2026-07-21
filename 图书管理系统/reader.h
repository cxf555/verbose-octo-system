#pragma once
#include "utils.h"

typedef struct Reader {
    int    id;
    char   name[MAX_NAME_LEN];
    char   dept[MAX_DEPT_LEN];
    char   phone[MAX_PHONE_LEN];
    int    max_borrow;
    int    cur_borrowed;
    struct Reader *next;
} Reader;

void    reader_init(void);
void    reader_save(void);
void    reader_free(void);
void    reader_add(void);
void    reader_delete(int id);
void    reader_modify(int id);
void    reader_search(void);
void    reader_list_all(void);
Reader *reader_find_by_id(int id);
Reader *reader_get_head(void);
int     reader_count_borrow(int reader_id);
