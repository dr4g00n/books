#!/bin/bash
#
# Books CLI 初始化脚本
#

BOOKS_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BOOKS_SHELL="$BOOKS_ROOT/.scripts/books.sh"

echo "📚 Books CLI 初始化"
echo ""

# 检测 shell 类型
if [ -n "$ZSH_VERSION" ]; then
    SHELL_CONFIG="$HOME/.zshrc"
    SHELL_NAME="zsh"
elif [ -n "$BASH_VERSION" ]; then
    SHELL_CONFIG="$HOME/.bashrc"
    SHELL_NAME="bash"
else
    echo "❌ 无法检测 shell 类型"
    echo "请手动将以下内容添加到你的 shell 配置文件:"
    echo ""
    echo "source \"$BOOKS_SHELL\""
    exit 1
fi

echo "检测到 shell: $SHELL_NAME"
echo "配置文件: $SHELL_CONFIG"
echo ""

# 检查是否已添加
if grep -q "books.sh" "$SHELL_CONFIG" 2>/dev/null; then
    echo "⚠️  检测到已添加过配置"
    echo "如需重新配置，请先手动删除旧配置"
    exit 0
fi

# 添加配置
cat >> "$SHELL_CONFIG" << EOF

# ============================================
# Books CLI - 书籍管理系统
# ============================================
source "$BOOKS_SHELL"

# 快捷别名（可选）
alias bq='books_search'
alias bl='books_list'
alias bo='books_open'
alias be='books_edit'
alias bs='books_stats'
alias bu='books_update'
alias br='books_reading'
alias bp='books_pick'
alias bh='books_help'
EOF

echo "✅ 已添加到 $SHELL_CONFIG"
echo ""
echo "请执行以下命令使配置生效:"
echo ""
echo "  source $SHELL_CONFIG"
echo ""
echo "或重新打开终端窗口"
echo ""
echo "命令列表："
echo "  books_search   搜索书籍"
echo "  books_list     列出书籍"
echo "  books_open     打开书籍"
echo "  books_edit     编辑信息"
echo "  books_stats    查看统计"
echo "  books_help     显示帮助"
echo "  books_update   更新索引"
echo ""
echo "快捷别名："
echo "  bq  搜索 (books_search)"
echo "  bl  列表 (books_list)"
echo "  bo  打开 (books_open)"
echo "  be  编辑 (books_edit)"
echo "  bs  统计 (books_stats)"
echo "  bh  帮助 (books_help)"
echo ""
