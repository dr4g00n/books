#!/usr/bin/env bash
# Books CLI - 交互式界面

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$SCRIPT_DIR/venv/bin/python3"
CLI="$SCRIPT_DIR/.scripts/books.py"

# 颜色定义
BOLD='\033[1m'
GREEN='\033[32m'
BLUE='\033[34m'
YELLOW='\033[33m'
CYAN='\033[36m'
GRAY='\033[90m'
NC='\033[0m' # No Color

# 清屏并显示标题
show_header() {
    clear
    echo ""
    echo -e "${CYAN}═════════════════════════════════════════${NC}"
    echo -e "  ${BOLD}📚 Books CLI - 书籍管理系统${NC}"
    echo -e "${CYAN}═════════════════════════════════════════${NC}"
    echo ""
}

# 显示主菜单
show_menu() {
    show_header
    echo -e "${GREEN}【查询】${NC}"
    echo "  1. 搜索书籍"
    echo "  2. 列出所有书籍"
    echo "  3. 查看统计信息"
    echo "  4. 正在阅读"
    echo "  5. 未读书籍"
    echo "  6. 最近添加"
    echo ""
    echo -e "${BLUE}【操作】${NC}"
    echo "  7. 打开书籍 (按 ID)"
    echo "  8. 编辑书籍"
    echo "  9. 删除书籍"
    echo "  0. 更新索引"
    echo "  a. 整理书籍 (从 swap 目录)"
    echo "  b. 标签管理"
    echo ""
    echo -e "${YELLOW}  q. 退出${NC}"
    echo ""
    echo -ne "${GRAY}请选择 [0-9/a/b/q]: ${NC}"
}

# 搜索书籍
search_books() {
    echo ""
    read -p "输入搜索关键词: " keyword
    if [ -n "$keyword" ]; then
        echo ""
        "$PYTHON" "$CLI" query -k "$keyword"
    fi
    pause
}

# 列出书籍
list_books() {
    echo ""
    "$PYTHON" "$CLI" list
    pause
}

# 查看统计
show_stats() {
    echo ""
    "$PYTHON" "$CLI" stats
    pause
}

# 正在阅读
show_reading() {
    echo ""
    "$PYTHON" "$CLI" query -s reading
    pause
}

# 未读书籍
show_unread() {
    echo ""
    "$PYTHON" "$CLI" query -s unread
    pause
}

# 最近添加
show_recent() {
    echo ""
    "$PYTHON" "$CLI" query --limit 10
    pause
}

# 打开书籍
open_book() {
    echo ""
    read -p "输入书籍 ID: " book_id
    if [ -n "$book_id" ]; then
        echo ""
        "$PYTHON" "$CLI" open "$book_id"
    fi
}

# 编辑书籍
edit_book() {
    echo ""
    read -p "输入书籍 ID: " book_id
    if [ -z "$book_id" ]; then
        pause
        return
    fi
    echo ""
    echo "编辑选项："
    echo "  --title 书名     设置书名"
    echo "  --author 作者    设置作者"
    echo "  --status 状态    设置阅读状态"
    echo "  --rating 1-5     设置评分"
    echo "  --tag 标签       添加标签"
    echo "  --remove-tag 标签 删除标签"
    echo "  --notes 笔记     添加笔记"
    echo ""
    read -p "输入编辑参数 (如: --status reading --rating 5): " edit_args
    if [ -n "$edit_args" ]; then
        echo ""
        "$PYTHON" "$CLI" edit "$book_id" $edit_args
    fi
    pause
}

# 删除书籍
delete_book() {
    echo ""
    read -p "输入要删除的书籍 ID: " book_id
    if [ -n "$book_id" ]; then
        read -p "确认删除 ID $book_id? [y/N]: " confirm
        if [[ "$confirm" =~ ^[Yy]$ ]]; then
            echo ""
            "$PYTHON" "$CLI" delete "$book_id"
        else
            echo "已取消"
        fi
    fi
    pause
}

# 更新索引
update_index() {
    echo ""
    echo "正在更新索引..."
    "$PYTHON" "$CLI" index
    pause
}

# 整理书籍
organize_books() {
    echo ""
    "$PYTHON" "$CLI" organize
    pause
}

# 标签管理
manage_tags() {
    echo ""
    echo "标签管理功能"
    echo "1. 查看所有标签"
    echo "2. 为书籍添加标签"
    echo "3. 删除书籍标签"
    echo ""
    read -p "请选择: " choice

    case "$choice" in
        1)
            echo ""
            "$PYTHON" "$CLI" stats
            ;;
        2)
            read -p "输入书籍ID: " book_id
            read -p "输入标签(如 #Python): " tag
            if [ -n "$book_id" ] && [ -n "$tag" ]; then
                echo ""
                "$PYTHON" "$CLI" edit "$book_id" --tag "$tag"
            fi
            ;;
        3)
            read -p "输入书籍ID: " book_id
            read -p "输入要删除的标签(如 #Python): " tag
            if [ -n "$book_id" ] && [ -n "$tag" ]; then
                echo ""
                "$PYTHON" "$CLI" edit "$book_id" --remove-tag "$tag"
            fi
            ;;
        *)
            echo "无效选项"
            ;;
    esac
    pause
}

# 暂停等待用户
pause() {
    echo ""
    read -s -n 1 -p "按任意键继续..."
}

# 主循环
main() {
    while true; do
        show_menu
        read -n 1 choice
        echo ""  # 换行

        case "$choice" in
            1) search_books ;;
            2) list_books ;;
            3) show_stats ;;
            4) show_reading ;;
            5) show_unread ;;
            6) show_recent ;;
            7) open_book; pause ;;
            8) edit_book ;;
            9) delete_book ;;
            0) update_index ;;
            a|A) organize_books ;;
            b|B) manage_tags ;;
            q|Q)
                echo ""
                echo "再见！"
                exit 0
                ;;
            *)
                echo ""
                echo -e "${YELLOW}无效选项，请重试${NC}"
                sleep 1
                ;;
        esac
    done
}

# 启动
main
