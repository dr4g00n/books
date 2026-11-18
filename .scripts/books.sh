#!/usr/bin/env bash
# Books CLI Shell 函数库
# 兼容 bash 和 zsh

# 获取脚本所在目录
_get_script_dir() {
    local dir=""

    if [ -n "${BASH_SOURCE:-}" ]; then
        dir="$(cd "${BASH_SOURCE[0]%/*}" && pwd)"
    elif [ -n "$ZSH_VERSION" ]; then
        # zsh
        dir="$(cd "$(dirname "${(%):-%x}")" && pwd)"
    else
        dir="$(cd "$(dirname "$0")" && pwd)"
    fi

    echo "$dir"
}

SCRIPT_DIR="$(_get_script_dir)"
# 脚本在 .scripts/ 目录下，需要返回上一级
BOOKS_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BOOKS_CLI="$BOOKS_ROOT/.scripts/books.py"
BOOKS_PYTHON="$BOOKS_ROOT/venv/bin/python3"

# 使用下划线命名，更兼容
books_search() { "$BOOKS_PYTHON" "$BOOKS_CLI" query -k "$@"; }
books_list() { "$BOOKS_PYTHON" "$BOOKS_CLI" list "$@"; }
books_open() { "$BOOKS_PYTHON" "$BOOKS_CLI" open "$@"; }
books_edit() { "$BOOKS_PYTHON" "$BOOKS_CLI" edit "$@"; }
books_stats() { "$BOOKS_PYTHON" "$BOOKS_CLI" stats; }
books_update() { "$BOOKS_PYTHON" "$BOOKS_CLI" index; }
books_delete() { "$BOOKS_PYTHON" "$BOOKS_CLI" delete "$@"; }
books_reading() { "$BOOKS_PYTHON" "$BOOKS_CLI" query -s reading "$@"; }
books_unread() { "$BOOKS_PYTHON" "$BOOKS_CLI" query -s unread "$@"; }
books_recent() { "$BOOKS_PYTHON" "$BOOKS_CLI" query --limit 10 "$@"; }

books_pick() {
    local keyword="$1"
    if [ -n "$keyword" ]; then
        local results=$("$BOOKS_PYTHON" "$BOOKS_CLI" query -k "$keyword" --limit 20 2>/dev/null)
    else
        local results=$("$BOOKS_PYTHON" "$BOOKS_CLI" query --limit 20 2>/dev/null)
    fi
    if [ -z "$results" ]; then
        echo "No books found"
        return 1
    fi
    echo "$results"
    read -p "Enter book ID: " book_id
    if [ -n "$book_id" ] && [[ "$book_id" =~ ^[0-9]+$ ]]; then
        "$BOOKS_PYTHON" "$BOOKS_CLI" open "$book_id"
    fi
}

books_help() {
    cat << 'HELP'
📚 Books CLI - 书籍管理系统命令帮助

核心命令:
  books_search 关键词         搜索书籍（标题/作者/笔记）
  books_list [分类]           列出指定分类的书籍
  books_open ID               打开指定 ID 的书籍
  books_edit ID [选项]        编辑书籍元数据
  books_stats                 显示统计信息
  books_update                更新索引
  books_delete ID             删除书籍记录
  books_help                  显示帮助信息

便捷命令:
  books_reading               显示正在阅读的书籍
  books_unread                显示未读的书籍
  books_recent                显示最近添加的书籍
  books_pick [关键词]         交互式选择并打开书籍

编辑选项:
  --title 书名                设置书名
  --author 作者               设置作者
  --status 状态               设置阅读状态
  --rating 1-5                设置评分
  --tag 标签                  添加标签（可多次使用）
  --remove-tag 标签           删除标签
  --notes 笔记                添加笔记

快捷别名（需配置）:
  bq                          books_search
  bl                          books_list
  bo                          books_open
  be                          books_edit
  bs                          books_stats
  bu                          books_update
  br                          books_reading
  bp                          books_pick
  bh                          books_help

使用示例:
  books_search web            搜索包含 "web" 的书籍
  books_list "Web安全"        列出 Web 安全分类的书籍
  books_open 5                打开 ID 为 5 的书籍
  books_edit 1 --status reading --rating 5
  books_pick sql              搜索并交互选择打开

更多信息: ~/WorkSpace/books/QUICKSTART.md
HELP
}
