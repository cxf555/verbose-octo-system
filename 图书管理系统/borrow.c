#define _CRT_SECURE_NO_WARNINGS
#include "borrow.h"
#include "book.h"
#include "reader.h"

static Borrow *head = NULL;
static int next_id = 1;

void borrow_init(void) {
    ensure_data_dir();
    FILE *fp = NULL;
    if (fopen_s(&fp, BORROWS_FILE, "rb") != 0 || fp == NULL) return;
    int count;
    if (fread(&count, sizeof(int), 1, fp) != 1) { fclose(fp); return; }
    head = NULL;
    Borrow *tail = NULL;
    for (int i = 0; i < count; i++) {
        Borrow *b = (Borrow *)malloc(sizeof(Borrow));
        if (b == NULL) break;
        if (fread(b, sizeof(Borrow) - sizeof(Borrow *), 1, fp) != 1) {
            free(b); break;
        }
        b->next = NULL;
        if (head == NULL) {
            head = tail = b;
        } else {
            tail->next = b;
            tail = b;
        }
        if (b->id >= next_id) next_id = b->id + 1;
    }
    fclose(fp);
}

void borrow_save(void) {
    ensure_data_dir();
    FILE *fp = NULL;
    if (fopen_s(&fp, BORROWS_FILE, "wb") != 0 || fp == NULL) return;
    int count = 0;
    for (Borrow *p = head; p != NULL; p = p->next) count++;
    fwrite(&count, sizeof(int), 1, fp);
    for (Borrow *p = head; p != NULL; p = p->next)
        fwrite(p, sizeof(Borrow) - sizeof(Borrow *), 1, fp);
    fclose(fp);
}

void borrow_free(void) {
    while (head != NULL) {
        Borrow *p = head;
        head = head->next;
        free(p);
    }
}

Borrow *borrow_get_head(void) { return head; }

Borrow *borrow_find_by_id(int id) {
    for (Borrow *p = head; p != NULL; p = p->next)
        if (p->id == id) return p;
    return NULL;
}

int borrow_has_active_for_book(int book_id) {
    for (Borrow *p = head; p != NULL; p = p->next)
        if (p->book_id == book_id && p->return_date[0] == '\0') return 1;
    return 0;
}

int borrow_has_active_for_reader(int reader_id) {
    for (Borrow *p = head; p != NULL; p = p->next)
        if (p->reader_id == reader_id && p->return_date[0] == '\0') return 1;
    return 0;
}

int borrow_count_active_by_reader(int reader_id) {
    int count = 0;
    for (Borrow *p = head; p != NULL; p = p->next)
        if (p->reader_id == reader_id && p->return_date[0] == '\0') count++;
    return count;
}

void borrow_book(void) {
    clear_screen();
    printf("========== 借书 ==========\n");
    int reader_id = get_int_input("输入读者编号: ");
    Reader *reader = reader_find_by_id(reader_id);
    if (reader == NULL) {
        printf("读者不存在！\n"); pause_screen(); return;
    }

    int active = borrow_count_active_by_reader(reader_id);
    if (active >= reader->max_borrow) {
        printf("该读者已借阅 %d 本书，达到上限（%d 本），无法再借。\n",
               active, reader->max_borrow);
        pause_screen(); return;
    }

    int book_id = get_int_input("输入图书编号: ");
    Book *book = book_find_by_id(book_id);
    if (book == NULL) {
        printf("图书不存在！\n"); pause_screen(); return;
    }
    if (book->available <= 0) {
        printf("该书已全部借出，暂无库存。\n"); pause_screen(); return;
    }

    Borrow *b = (Borrow *)malloc(sizeof(Borrow));
    if (b == NULL) { printf("内存分配失败！\n"); return; }
    b->id = next_id++;
    b->book_id = book_id;
    b->reader_id = reader_id;
    get_current_date(b->borrow_date);
    calculate_due_date(b->borrow_date, b->due_date, DEFAULT_BORROW_DAYS);
    b->return_date[0] = '\0';
    b->next = NULL;

    book->available--;
    reader->cur_borrowed++;

    if (head == NULL) {
        head = b;
    } else {
        Borrow *p = head;
        while (p->next != NULL) p = p->next;
        p->next = b;
    }

    borrow_save();
    book_save();
    reader_save();

    printf("\n借书成功！\n");
    printf("  读者: %s\n", reader->name);
    printf("  图书: %s\n", book->title);
    printf("  借书日期: %s\n", b->borrow_date);
    printf("  应还日期: %s\n", b->due_date);
    pause_screen();
}

void return_book(void) {
    clear_screen();
    printf("========== 还书 ==========\n");
    int record_id = get_int_input("输入借阅记录编号: ");
    Borrow *b = borrow_find_by_id(record_id);
    if (b == NULL) {
        printf("借阅记录不存在！\n"); pause_screen(); return;
    }
    if (b->return_date[0] != '\0') {
        printf("该书已于 %s 归还。\n", b->return_date); pause_screen(); return;
    }

    Book *book = book_find_by_id(b->book_id);
    Reader *reader = reader_find_by_id(b->reader_id);

    get_current_date(b->return_date);
    if (book != NULL) book->available++;
    if (reader != NULL && reader->cur_borrowed > 0) reader->cur_borrowed--;

    borrow_save();
    if (book != NULL) book_save();
    if (reader != NULL) reader_save();

    printf("\n还书成功！\n");
    if (book) printf("  图书: %s (库存恢复)\n", book->title);
    if (reader) printf("  读者: %s\n", reader->name);
    printf("  归还日期: %s\n", b->return_date);
    if (is_overdue(b->due_date)) {
        printf("  *** 该记录已逾期！***\n");
    }
    pause_screen();
}

void borrow_search(void) {
    clear_screen();
    printf("========== 查询借阅记录 ==========\n");
    printf("1. 按读者编号查询\n2. 按图书编号查询\n3. 查询所有未还记录\n0. 返回\n");
    int choice = get_int_input("请选择: ");
    if (choice == 0) return;
    clear_screen();

    int id;
    if (choice == 1) id = get_int_input("输入读者编号: ");
    else if (choice == 2) id = get_int_input("输入图书编号: ");

    printf("记录号 读者      图书              借书日期   应还日期   归还日期   状态\n");
    printf("------ --------- ----------------- ---------- ---------- ---------- ------\n");
    int found = 0;
    for (Borrow *p = head; p != NULL; p = p->next) {
        int match = 0;
        if (choice == 1 && p->reader_id == id) match = 1;
        else if (choice == 2 && p->book_id == id) match = 1;
        else if (choice == 3 && p->return_date[0] == '\0') match = 1;

        if (match) {
            Reader *r = reader_find_by_id(p->reader_id);
            Book *bk = book_find_by_id(p->book_id);
            const char *status;
            if (p->return_date[0] != '\0') status = "已还";
            else if (is_overdue(p->due_date)) status = "逾期";
            else status = "借出";

            printf("%-6d %-9s %-17s %-10s %-10s %-10s %s\n",
                   p->id,
                   r ? r->name : "?",
                   bk ? bk->title : "?",
                   p->borrow_date,
                   p->due_date,
                   p->return_date[0] ? p->return_date : "-",
                   status);
            found++;
        }
    }
    if (found == 0) printf("未找到匹配的借阅记录。\n");
    else printf("\n共 %d 条记录。\n", found);
    pause_screen();
}

void borrow_check_overdue(void) {
    clear_screen();
    printf("========== 逾期未还记录 ==========\n");
    printf("记录号 读者      图书              借书日期   应还日期   逾期天数\n");
    printf("------ --------- ----------------- ---------- ---------- --------\n");
    int found = 0;
    char today[11];
    get_current_date(today);
    for (Borrow *p = head; p != NULL; p = p->next) {
        if (p->return_date[0] == '\0' && is_overdue(p->due_date)) {
            Reader *r = reader_find_by_id(p->reader_id);
            Book *bk = book_find_by_id(p->book_id);
            /* rough overdue days calculation */
            int y1, m1, d1, y2, m2, d2;
            sscanf(p->due_date, "%d-%d-%d", &y1, &m1, &d1);
            sscanf(today, "%d-%d-%d", &y2, &m2, &d2);
            int days = (y2 - y1) * 365 + (m2 - m1) * 30 + (d2 - d1);
            if (days < 0) days = 0;

            printf("%-6d %-9s %-17s %-10s %-10s %d天\n",
                   p->id,
                   r ? r->name : "?",
                   bk ? bk->title : "?",
                   p->borrow_date,
                   p->due_date,
                   days);
            found++;
        }
    }
    if (found == 0) printf("当前无逾期记录。\n");
    else printf("\n共 %d 条逾期记录。\n", found);
    pause_screen();
}
