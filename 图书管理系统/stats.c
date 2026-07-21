#define _CRT_SECURE_NO_WARNINGS
#include "stats.h"

typedef struct {
    int  id;
    char name[256];
    int  count;
} RankItem;

void stats_popular_books(void) {
    clear_screen();
    printf("========== 热门图书排行 (Top 10) ==========\n");

    int book_count = 0;
    for (Book *p = book_get_head(); p != NULL; p = p->next) book_count++;
    if (book_count == 0) { printf("暂无图书数据。\n"); pause_screen(); return; }

    RankItem *items = (RankItem *)malloc(sizeof(RankItem) * book_count);
    if (items == NULL) return;
    int idx = 0;
    for (Book *p = book_get_head(); p != NULL; p = p->next) {
        items[idx].id = p->id;
        strcpy_s(items[idx].name, sizeof(items[idx].name), p->title);
        items[idx].count = 0;
        for (Borrow *b = borrow_get_head(); b != NULL; b = b->next)
            if (b->book_id == p->id) items[idx].count++;
        idx++;
    }

    /* bubble sort descending */
    for (int i = 0; i < book_count - 1; i++)
        for (int j = 0; j < book_count - 1 - i; j++)
            if (items[j].count < items[j + 1].count) {
                RankItem tmp = items[j];
                items[j] = items[j + 1];
                items[j + 1] = tmp;
            }

    printf("排名  图书                          借阅次数\n");
    printf("----- ----------------------------- --------\n");
    int limit = book_count < 10 ? book_count : 10;
    for (int i = 0; i < limit; i++)
        printf("%-5d %-29s %-8d\n", i + 1, items[i].name, items[i].count);
    free(items);
    pause_screen();
}

void stats_category_count(void) {
    clear_screen();
    printf("========== 分类借阅统计 ==========\n");

    /* collect unique categories */
    char cats[100][MAX_CATEGORY_LEN];
    int  counts[100] = {0};
    int  cat_count = 0;

    for (Book *p = book_get_head(); p != NULL; p = p->next) {
        int found = -1;
        for (int i = 0; i < cat_count; i++)
            if (strcmp(cats[i], p->category) == 0) { found = i; break; }
        if (found == -1) {
            strcpy_s(cats[cat_count], MAX_CATEGORY_LEN, p->category);
            found = cat_count;
            cat_count++;
        }
        for (Borrow *b = borrow_get_head(); b != NULL; b = b->next)
            if (b->book_id == p->id) counts[found]++;
    }

    if (cat_count == 0) { printf("暂无数据。\n"); pause_screen(); return; }
    printf("分类            借阅量\n");
    printf("--------------- ------\n");
    for (int i = 0; i < cat_count; i++)
        printf("%-15s %-6d\n", cats[i], counts[i]);
    pause_screen();
}

void stats_reader_ranking(void) {
    clear_screen();
    printf("========== 读者借阅排行 ==========\n");

    int reader_count = 0;
    for (Reader *p = reader_get_head(); p != NULL; p = p->next) reader_count++;
    if (reader_count == 0) { printf("暂无读者数据。\n"); pause_screen(); return; }

    RankItem *items = (RankItem *)malloc(sizeof(RankItem) * reader_count);
    if (items == NULL) return;
    int idx = 0;
    for (Reader *p = reader_get_head(); p != NULL; p = p->next) {
        items[idx].id = p->id;
        strcpy_s(items[idx].name, sizeof(items[idx].name), p->name);
        items[idx].count = 0;
        for (Borrow *b = borrow_get_head(); b != NULL; b = b->next)
            if (b->reader_id == p->id) items[idx].count++;
        idx++;
    }

    for (int i = 0; i < reader_count - 1; i++)
        for (int j = 0; j < reader_count - 1 - i; j++)
            if (items[j].count < items[j + 1].count) {
                RankItem tmp = items[j];
                items[j] = items[j + 1];
                items[j + 1] = tmp;
            }

    printf("排名  读者          借阅次数\n");
    printf("----- ------------- --------\n");
    for (int i = 0; i < reader_count; i++)
        printf("%-5d %-13s %-8d\n", i + 1, items[i].name, items[i].count);
    free(items);
    pause_screen();
}

void stats_low_stock(void) {
    clear_screen();
    printf("========== 库存预警 (可借数量 <= 1) ==========\n");
    int found = 0;
    printf("编号  书名                    作者        库存 可借\n");
    printf("------ ----------------------- ---------- ---- ----\n");
    for (Book *p = book_get_head(); p != NULL; p = p->next) {
        if (p->available <= 1) {
            printf("%-6d %-23s %-10s %-4d %-4d\n",
                   p->id, p->title, p->author, p->total, p->available);
            found++;
        }
    }
    if (found == 0) printf("所有图书库存充足。\n");
    else printf("\n共 %d 本图书库存紧张。\n", found);
    pause_screen();
}

void stats_overdue(void) {
    clear_screen();
    printf("========== 逾期统计 ==========\n");
    int overdue_count = 0;
    for (Borrow *p = borrow_get_head(); p != NULL; p = p->next)
        if (p->return_date[0] == '\0' && is_overdue(p->due_date)) overdue_count++;

    printf("\n当前逾期未还记录: %d 条\n", overdue_count);

    if (overdue_count > 0) {
        int reader_od[1000] = {0};
        int reader_ids[1000];
        int od_idx = 0;
        for (Borrow *p = borrow_get_head(); p != NULL; p = p->next) {
            if (p->return_date[0] == '\0' && is_overdue(p->due_date)) {
                int found = -1;
                for (int i = 0; i < od_idx; i++)
                    if (reader_ids[i] == p->reader_id) { found = i; break; }
                if (found == -1) {
                    reader_ids[od_idx] = p->reader_id;
                    reader_od[od_idx] = 1;
                    od_idx++;
                } else {
                    reader_od[found]++;
                }
            }
        }
        printf("\n逾期读者列表:\n");
        printf("读者          逾期数量\n");
        printf("------------- --------\n");
        for (int i = 0; i < od_idx; i++) {
            Reader *r = reader_find_by_id(reader_ids[i]);
            printf("%-13s %-8d\n", r ? r->name : "未知", reader_od[i]);
        }
    }
    pause_screen();
}
