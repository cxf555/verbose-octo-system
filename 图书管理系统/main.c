#define _CRT_SECURE_NO_WARNINGS
#include "book.h"
#include "reader.h"
#include "borrow.h"
#include "stats.h"

static void book_menu(void) {
    while (1) {
        clear_screen();
        printf("========== 图书管理 ==========\n");
        printf("1. 添加图书\n");
        printf("2. 删除图书\n");
        printf("3. 修改图书\n");
        printf("4. 查找图书\n");
        printf("5. 列出全部\n");
        printf("0. 返回主菜单\n");
        printf("==============================\n");
        int choice = get_int_input("请选择: ");
        if (choice == 0) return;
        switch (choice) {
        case 1: book_add(); break;
        case 2: {
            int id = get_int_input("输入要删除的图书编号: ");
            book_delete(id);
            break;
        }
        case 3: {
            int id = get_int_input("输入要修改的图书编号: ");
            book_modify(id);
            break;
        }
        case 4: book_search(); break;
        case 5: book_list_all(); break;
        default: printf("无效选项，请重新选择。\n"); pause_screen(); break;
        }
    }
}

static void reader_menu(void) {
    while (1) {
        clear_screen();
        printf("========== 读者管理 ==========\n");
        printf("1. 注册读者\n");
        printf("2. 删除读者\n");
        printf("3. 修改信息\n");
        printf("4. 查找读者\n");
        printf("5. 列出全部\n");
        printf("0. 返回主菜单\n");
        printf("==============================\n");
        int choice = get_int_input("请选择: ");
        if (choice == 0) return;
        switch (choice) {
        case 1: reader_add(); break;
        case 2: {
            int id = get_int_input("输入要删除的读者编号: ");
            reader_delete(id);
            break;
        }
        case 3: {
            int id = get_int_input("输入要修改的读者编号: ");
            reader_modify(id);
            break;
        }
        case 4: reader_search(); break;
        case 5: reader_list_all(); break;
        default: printf("无效选项，请重新选择。\n"); pause_screen(); break;
        }
    }
}

static void borrow_menu(void) {
    while (1) {
        clear_screen();
        printf("========== 借阅管理 ==========\n");
        printf("1. 借书\n");
        printf("2. 还书\n");
        printf("3. 查询记录\n");
        printf("4. 逾期检查\n");
        printf("0. 返回主菜单\n");
        printf("==============================\n");
        int choice = get_int_input("请选择: ");
        if (choice == 0) return;
        switch (choice) {
        case 1: borrow_book(); break;
        case 2: return_book(); break;
        case 3: borrow_search(); break;
        case 4: borrow_check_overdue(); break;
        default: printf("无效选项，请重新选择。\n"); pause_screen(); break;
        }
    }
}

static void stats_menu(void) {
    while (1) {
        clear_screen();
        printf("========== 统计报表 ==========\n");
        printf("1. 热门图书排行\n");
        printf("2. 分类借阅统计\n");
        printf("3. 读者借阅排行\n");
        printf("4. 库存预警\n");
        printf("5. 逾期统计\n");
        printf("0. 返回主菜单\n");
        printf("==============================\n");
        int choice = get_int_input("请选择: ");
        if (choice == 0) return;
        switch (choice) {
        case 1: stats_popular_books(); break;
        case 2: stats_category_count(); break;
        case 3: stats_reader_ranking(); break;
        case 4: stats_low_stock(); break;
        case 5: stats_overdue(); break;
        default: printf("无效选项，请重新选择。\n"); pause_screen(); break;
        }
    }
}

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    book_init();
    reader_init();
    borrow_init();

    while (1) {
        clear_screen();
        printf("========================================\n");
        printf("        欢迎使用图书管理系统        \n");
        printf("========================================\n");
        printf("1. 图书管理\n");
        printf("2. 读者管理\n");
        printf("3. 借阅管理\n");
        printf("4. 统计报表\n");
        printf("0. 退出系统\n");
        printf("========================================\n");
        int choice = get_int_input("请选择: ");
        switch (choice) {
        case 1: book_menu();   break;
        case 2: reader_menu(); break;
        case 3: borrow_menu(); break;
        case 4: stats_menu();  break;
        case 0:
            printf("\n正在保存数据...\n");
            book_save();
            reader_save();
            borrow_save();
            book_free();
            reader_free();
            borrow_free();
            printf("感谢使用，再见！\n");
            return 0;
        default:
            printf("无效选项，请重新选择。\n");
            pause_screen();
            break;
        }
    }
}
