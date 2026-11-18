# Books CLI 快速设置

## 一键初始化

运行初始化脚本自动配置：

```bash
cd ~/WorkSpace/books
bash .scripts/init.sh
```

然后执行：

```bash
source ~/.zshrc
```

## 手动配置

在 `~/.zshrc` 中添加：

```bash
source ~/WorkSpace/books/.scripts/books.sh

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
```

## 命令列表

### 核心命令

| 命令 | 功能 | 示例 |
|------|------|------|
| `books_search 关键词` | 搜索书籍 | `books_search sql` |
| `books_list [分类]` | 列出书籍 | `books_list "Web安全"` |
| `books_open ID` | 打开书籍 | `books_open 1` |
| `books_edit ID [选项]` | 编辑信息 | `books_edit 1 --status reading` |
| `books_stats` | 查看统计 | `books_stats` |
| `books_help` | 显示帮助 | `books_help` |
| `books_update` | 更新索引 | `books_update` |
| `books_delete ID` | 删除记录 | `books_delete 1` |

### 便捷命令

| 命令 | 功能 |
|------|------|
| `books_reading` | 查看阅读中的书 |
| `books_unread` | 查看未读的书 |
| `books_recent` | 查看最近添加 |
| `books_pick [关键词]` | 交互式选择打开 |

### 快捷别名

配置别名后可使用：

| 别名 | 对应命令 |
|------|----------|
| `bq 关键词` | `books_search` |
| `bl [分类]` | `books_list` |
| `bo ID` | `books_open` |
| `be ID [选项]` | `books_edit` |
| `bs` | `books_stats` |
| `bh` | `books_help` |
| `bu` | `books_update` |
| `br` | `books_reading` |
| `bp [关键词]` | `books_pick` |

## 使用示例

```bash
# 搜索书籍
books_search "web"
bq sql注入          # 使用别名

# 查看统计
books_stats
bs                 # 使用别名

# 打开书籍
books_open 5
bo 5               # 使用别名

# 编辑信息
books_edit 1 --status reading --rating 5 --tag "必读"

# 查看阅读中的书
books_reading
```

---

**注意**：命令使用下划线 `_` 而不是连字符 `-`，确保兼容性。
