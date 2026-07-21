#define _CRT_SECURE_NO_WARNINGS
#include "book.h"
#include "borrow.h"

static Book *head = NULL;
static int next_id = 1;

void book_init(void) {
    ensure_data_dir();
    FILE *fp = NULL;
    if (fopen_s(&fp, BOOKS_FILE, "rb") != 0 || fp == NULL) return;
    int count;
    if (fread(&count, sizeof(int), 1, fp) != 1) { fclose(fp); return; }
    head = NULL;
    Book *tail = NULL;
    for (int i = 0; i < count; i++) {
        Book *b = (Book *)malloc(sizeof(Book));
        if (b == NULL) break;
        if (fread(b, sizeof(Book) - sizeof(Book *), 1, fp) != 1) {
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

void book_save(void) {
    ensure_data_dir();
    FILE *fp = NULL;
    if (fopen_s(&fp, BOOKS_FILE, "wb") != 0 || fp == NULL) return;
    int count = 0;
    for (Book *p = head; p != NULL; p = p->next) count++;
    fwrite(&count, sizeof(int), 1, fp);
    for (Book *p = head; p != NULL; p = p->next)
        fwrite(p, sizeof(Book) - sizeof(Book *), 1, fp);
    fclose(fp);
}

void book_free(void) {
    while (head != NULL) {
        Book *p = head;
        head = head->next;
        free(p);
    }
}

Book *book_get_head(void) { return head; }

Book *book_find_by_id(int id) {
    for (Book *p = head; p != NULL; p = p->next)
        if (p->id == id) return p;
    return NULL;
}

void book_add(void) {
    Book *b = (Book *)malloc(sizeof(Book));
    if (b == NULL) { printf("内存分配失败！\n"); return; }
    b->id = next_id++;
    clear_screen();
    printf("========== 添加图书 ==========\n");
    get_string_input("书名: ", b->title, MAX_TITLE_LEN);
    get_string_input("作者: ", b->author, MAX_AUTHOR_LEN);
    get_string_input("出版社: ", b->publisher, MAX_PUBLISHER_LEN);
    get_string_input("分类: ", b->category, MAX_CATEGORY_LEN);
    b->total = get_int_input("库存数量: ");
    if (b->total < 1) b->total = 1;
    b->available = b->total;
    b->next = NULL;

    if (head == NULL) {
        head = b;
    } else {
        Book *p = head;
        while (p->next != NULL) p = p->next;
        p->next = b;
    }
    book_save();
    printf("\n图书 [%s] 添加成功！编号: %d\n", b->title, b->id);
    pause_screen();
}

void book_delete(int id) {
    if (borrow_has_active_for_book(id)) {
        printf("该图书尚有未归还记录，无法删除。\n");
        pause_screen();
        return;
    }
    Book *prev = NULL, *p = head;
    while (p != NULL && p->id != id) { prev = p; p = p->next; }
    if (p == NULL) { printf("未找到编号为 %d 的图书。\n", id); pause_screen(); return; }
    if (prev == NULL) head = p->next;
    else prev->next = p->next;
    free(p);
    book_save();
    printf("图书删除成功。\n");
    pause_screen();
}

void book_modify(int id) {
    Book *b = book_find_by_id(id);
    if (b == NULL) { printf("未找到编号为 %d 的图书。\n", id); pause_screen(); return; }
    clear_screen();
    printf("========== 修改图书 (编号: %d) ==========\n", b->id);
    printf("(直接回车保留原值)\n");
    char buffer[256];

    printf("书名 [%s]: ", b->title);
    if (fgets(buffer, sizeof(buffer), stdin) && buffer[0] != '\n') {
        size_t len = strlen(buffer);
        if (len > 0 && buffer[len - 1] == '\n') buffer[len - 1] = '\0';
        if (buffer[0] != '\0') strcpy(b->title, buffer);
    }
    printf("作者 [%s]: ", b->author);
    if (fgets(buffer, sizeof(buffer), stdin) && buffer[0] != '\n') {
        size_t len = strlen(buffer);
        if (len > 0 && buffer[len - 1] == '\n') buffer[len - 1] = '\0';
        if (buffer[0] != '\0') strcpy(b->author, buffer);
    }
    printf("出版社 [%s]: ", b->publisher);
    if (fgets(buffer, sizeof(buffer), stdin) && buffer[0] != '\n') {
        size_t len = strlen(buffer);
        if (len > 0 && buffer[len - 1] == '\n') buffer[len - 1] = '\0';
        if (buffer[0] != '\0') strcpy(b->publisher, buffer);
    }
    printf("分类 [%s]: ", b->category);
    if (fgets(buffer, sizeof(buffer), stdin) && buffer[0] != '\n') {
        size_t len = strlen(buffer);
        if (len > 0 && buffer[len - 1] == '\n') buffer[len - 1] = '\0';
        if (buffer[0] != '\0') strcpy(b->category, buffer);
    }
    printf("总库存 [%d]: ", b->total);
    if (fgets(buffer, sizeof(buffer), stdin) && buffer[0] != '\n') {
        int new_total;
        if (sscanf(buffer, "%d", &new_total) == 1 && new_total >= b->total - b->available) {
            int borrowed = b->total - b->available;
            b->total = new_total;
            b->available = new_total - borrowed;
            if (b->available < 0) b->available = 0;
        }
    }
    book_save();
    printf("\n图书信息修改成功。\n");
    pause_screen();
}

void book_search(void) {
    clear_screen();
    printf("========== 查找图书 ==========\n");
    printf("1. 按编号查找\n2. 按书名查找\n3. 按作者查找\n4. 按分类查找\n0. 返回\n");
    int choice = get_int_input("请选择: ");
    if (choice == 0) return;
    char keyword[256];
    int found = 0;
    clear_screen();

    switch (choice) {
    case 1: {
        int id = get_int_input("输入图书编号: ");
        Book *b = book_find_by_id(id);
        if (b) {
            printf("编号  书名                    作者        出版社      分类    库存 可借\n");
            printf("------ ----------------------- ----------- ---------- ------ ---- ----\n");
            printf("%-6d %-23s %-11s %-10s %-6s %-4d %-4d\n",
                   b->id, b->title, b->author, b->publisher, b->category, b->total, b->available);
            found = 1;
        }
        break;
    }
    case 2: get_string_input("输入书名关键词: ", keyword, sizeof(keyword)); break;
    case 3: get_string_input("输入作者关键词: ", keyword, sizeof(keyword)); break;
    case 4: get_string_input("输入分类关键词: ", keyword, sizeof(keyword)); break;
    default: return;
    }

    if (choice != 1) {
        printf("编号  书名                    作者        出版社      分类    库存 可借\n");
        printf("------ ----------------------- ----------- ---------- ------ ---- ----\n");
        for (Book *p = head; p != NULL; p = p->next) {
            const char *field = (choice == 2) ? p->title :
                                (choice == 3) ? p->author : p->category;
            if (str_contains(field, keyword)) {
                printf("%-6d %-23s %-11s %-10s %-6s %-4d %-4d\n",
                       p->id, p->title, p->author, p->publisher, p->category, p->total, p->available);
                found++;
            }
        }
    }
    if (found == 0) printf("未找到匹配的图书。\n");
    pause_screen();
}

void book_list_all(void) {
    clear_screen();
    printf("========== 全部图书 ==========\n");
    if (head == NULL) { printf("暂无图书。\n"); pause_screen(); return; }
    printf("编号  书名                    作者        出版社      分类    库存 可借\n");
    printf("------ ----------------------- ----------- ---------- ------ ---- ----\n");
    int count = 0;
    for (Book *p = head; p != NULL; p = p->next) {
        printf("%-6d %-23s %-11s %-10s %-6s %-4d %-4d\n",
               p->id, p->title, p->author, p->publisher, p->category, p->total, p->available);
        count++;
        if (count % 20 == 0) {
            printf("\n--- 已显示 %d 条，按任意键继续 ---\n", count);
            getchar();
        }
    }
    printf("\n共 %d 本图书。\n", count);
    pause_screen();
}

int book_count_borrow(int book_id) {
    int count = 0;
    Borrow *blist = borrow_get_head();
    for (Borrow *p = blist; p != NULL; p = p->next)
        if (p->book_id == book_id) count++;
    return count;
}
