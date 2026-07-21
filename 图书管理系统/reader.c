#define _CRT_SECURE_NO_WARNINGS
#include "reader.h"
#include "borrow.h"

static Reader *head = NULL;
static int next_id = 1;

void reader_init(void) {
    ensure_data_dir();
    FILE *fp = NULL;
    if (fopen_s(&fp, READERS_FILE, "rb") != 0 || fp == NULL) return;
    int count;
    if (fread(&count, sizeof(int), 1, fp) != 1) { fclose(fp); return; }
    head = NULL;
    Reader *tail = NULL;
    for (int i = 0; i < count; i++) {
        Reader *r = (Reader *)malloc(sizeof(Reader));
        if (r == NULL) break;
        if (fread(r, sizeof(Reader) - sizeof(Reader *), 1, fp) != 1) {
            free(r); break;
        }
        r->next = NULL;
        if (head == NULL) {
            head = tail = r;
        } else {
            tail->next = r;
            tail = r;
        }
        if (r->id >= next_id) next_id = r->id + 1;
    }
    fclose(fp);
}

void reader_save(void) {
    ensure_data_dir();
    FILE *fp = NULL;
    if (fopen_s(&fp, READERS_FILE, "wb") != 0 || fp == NULL) return;
    int count = 0;
    for (Reader *p = head; p != NULL; p = p->next) count++;
    fwrite(&count, sizeof(int), 1, fp);
    for (Reader *p = head; p != NULL; p = p->next)
        fwrite(p, sizeof(Reader) - sizeof(Reader *), 1, fp);
    fclose(fp);
}

void reader_free(void) {
    while (head != NULL) {
        Reader *p = head;
        head = head->next;
        free(p);
    }
}

Reader *reader_get_head(void) { return head; }

Reader *reader_find_by_id(int id) {
    for (Reader *p = head; p != NULL; p = p->next)
        if (p->id == id) return p;
    return NULL;
}

void reader_add(void) {
    Reader *r = (Reader *)malloc(sizeof(Reader));
    if (r == NULL) { printf("内存分配失败！\n"); return; }
    r->id = next_id++;
    clear_screen();
    printf("========== 注册读者 ==========\n");
    get_string_input("姓名: ", r->name, MAX_NAME_LEN);
    get_string_input("院系/班级: ", r->dept, MAX_DEPT_LEN);
    get_string_input("联系电话: ", r->phone, MAX_PHONE_LEN);
    r->max_borrow = DEFAULT_MAX_BORROW;
    r->cur_borrowed = 0;
    r->next = NULL;

    if (head == NULL) {
        head = r;
    } else {
        Reader *p = head;
        while (p->next != NULL) p = p->next;
        p->next = r;
    }
    reader_save();
    printf("\n读者 [%s] 注册成功！编号: %d\n", r->name, r->id);
    pause_screen();
}

void reader_delete(int id) {
    if (borrow_has_active_for_reader(id)) {
        printf("该读者尚有未归还图书，无法删除。\n");
        pause_screen();
        return;
    }
    Reader *prev = NULL, *p = head;
    while (p != NULL && p->id != id) { prev = p; p = p->next; }
    if (p == NULL) { printf("未找到编号为 %d 的读者。\n", id); pause_screen(); return; }
    if (prev == NULL) head = p->next;
    else prev->next = p->next;
    free(p);
    reader_save();
    printf("读者删除成功。\n");
    pause_screen();
}

void reader_modify(int id) {
    Reader *r = reader_find_by_id(id);
    if (r == NULL) { printf("未找到编号为 %d 的读者。\n", id); pause_screen(); return; }
    clear_screen();
    printf("========== 修改读者信息 (编号: %d) ==========\n", r->id);
    printf("(直接回车保留原值)\n");
    char buffer[256];

    printf("姓名 [%s]: ", r->name);
    if (fgets(buffer, sizeof(buffer), stdin) && buffer[0] != '\n') {
        size_t len = strlen(buffer);
        if (len > 0 && buffer[len - 1] == '\n') buffer[len - 1] = '\0';
        if (buffer[0] != '\0') strcpy(r->name, buffer);
    }
    printf("院系/班级 [%s]: ", r->dept);
    if (fgets(buffer, sizeof(buffer), stdin) && buffer[0] != '\n') {
        size_t len = strlen(buffer);
        if (len > 0 && buffer[len - 1] == '\n') buffer[len - 1] = '\0';
        if (buffer[0] != '\0') strcpy(r->dept, buffer);
    }
    printf("联系电话 [%s]: ", r->phone);
    if (fgets(buffer, sizeof(buffer), stdin) && buffer[0] != '\n') {
        size_t len = strlen(buffer);
        if (len > 0 && buffer[len - 1] == '\n') buffer[len - 1] = '\0';
        if (buffer[0] != '\0') strcpy(r->phone, buffer);
    }
    printf("最大借阅数 [%d]: ", r->max_borrow);
    if (fgets(buffer, sizeof(buffer), stdin) && buffer[0] != '\n') {
        int new_max;
        if (sscanf(buffer, "%d", &new_max) == 1 && new_max > 0) r->max_borrow = new_max;
    }
    reader_save();
    printf("\n读者信息修改成功。\n");
    pause_screen();
}

void reader_search(void) {
    clear_screen();
    printf("========== 查找读者 ==========\n");
    printf("1. 按编号查找\n2. 按姓名查找\n3. 按院系查找\n0. 返回\n");
    int choice = get_int_input("请选择: ");
    if (choice == 0) return;
    char keyword[256];
    int found = 0;
    clear_screen();

    switch (choice) {
    case 1: {
        int id = get_int_input("输入读者编号: ");
        Reader *r = reader_find_by_id(id);
        if (r) {
            printf("编号  姓名          院系          电话        最大借阅 当前借阅\n");
            printf("------ ------------- ------------ ----------- -------- --------\n");
            printf("%-6d %-13s %-12s %-11s %-8d %-8d\n",
                   r->id, r->name, r->dept, r->phone, r->max_borrow, r->cur_borrowed);
            found = 1;
        }
        break;
    }
    case 2: get_string_input("输入姓名关键词: ", keyword, sizeof(keyword)); break;
    case 3: get_string_input("输入院系关键词: ", keyword, sizeof(keyword)); break;
    default: return;
    }

    if (choice != 1) {
        printf("编号  姓名          院系          电话        最大借阅 当前借阅\n");
        printf("------ ------------- ------------ ----------- -------- --------\n");
        for (Reader *p = head; p != NULL; p = p->next) {
            const char *field = (choice == 2) ? p->name : p->dept;
            if (str_contains(field, keyword)) {
                printf("%-6d %-13s %-12s %-11s %-8d %-8d\n",
                       p->id, p->name, p->dept, p->phone, p->max_borrow, p->cur_borrowed);
                found++;
            }
        }
    }
    if (found == 0) printf("未找到匹配的读者。\n");
    pause_screen();
}

void reader_list_all(void) {
    clear_screen();
    printf("========== 全部读者 ==========\n");
    if (head == NULL) { printf("暂无读者。\n"); pause_screen(); return; }
    printf("编号  姓名          院系          电话        最大借阅 当前借阅\n");
    printf("------ ------------- ------------ ----------- -------- --------\n");
    int count = 0;
    for (Reader *p = head; p != NULL; p = p->next) {
        printf("%-6d %-13s %-12s %-11s %-8d %-8d\n",
               p->id, p->name, p->dept, p->phone, p->max_borrow, p->cur_borrowed);
        count++;
        if (count % 20 == 0) {
            printf("\n--- 已显示 %d 条，按任意键继续 ---\n", count);
            getchar();
        }
    }
    printf("\n共 %d 位读者。\n", count);
    pause_screen();
}

int reader_count_borrow(int reader_id) {
    int count = 0;
    Borrow *blist = borrow_get_head();
    for (Borrow *p = blist; p != NULL; p = p->next)
        if (p->reader_id == reader_id) count++;
    return count;
}
