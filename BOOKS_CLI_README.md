# Books CLI 使用说明

> 个人安全技术书籍查询系统

## 快速开始

### 1. 安装依赖

```bash
cd books
pip install -r requirements.txt
```

### 2. 建立索引

首次使用需要扫描目录建立索引：

```bash
python .scripts/books.py index
```

### 3. 查询书籍

```bash
# 搜索关键词
python .scripts/books.py query -k "web"

# 按分类筛选
python .scripts/books.py query -c "Web安全"

# 按状态筛选
python .scripts/books.py query -s "reading"

# 组合查询
python .scripts/books.py query -k "sql" -t "注入" -r 4
```

## 命令说明

### index - 建立索引

扫描 books 目录，提取书籍元数据并建立数据库索引。

```bash
python .scripts/books.py index [--force]
```

**选项：**
- `--force`: 强制重新索引（清空现有数据）

---

### query - 查询书籍

多维度查询书籍。

```bash
python .scripts/books.py query [OPTIONS]
```

**选项：**
- `-k, --keyword TEXT`: 关键词搜索（标题/作者/笔记）
- `-c, --category TEXT`: 按分类筛选
- `-s, --status TEXT`: 按状态筛选 (unread/reading/finished/reference)
- `-t, --tag TEXT`: 按标签筛选（可多选）
- `-r, --rating INT`: 最低评分
- `-l, --limit INT`: 最大结果数（默认 20）

**示例：**
```bash
# 搜索包含 "sql" 的书籍
python .scripts/books.py query -k "sql"

# 查找 Web 安全分类下评分 4+ 的书
python .scripts/books.py query -c "Web安全" -r 4

# 查找阅读中的书籍
python .scripts/books.py query -s "reading"

# 按标签筛选
python .scripts/books.py query -t "渗透测试" -t "web"
```

---

### list - 列出书籍

按分类列出书籍。

```bash
python .scripts/books.py list [CATEGORY] [OPTIONS]
```

**参数：**
- `CATEGORY`: 分类名称（可选，不指定则显示所有分类）

**选项：**
- `-s, --status TEXT`: 按状态筛选

**示例：**
```bash
# 显示所有分类
python .scripts/books.py list

# 显示 Web 安全分类下的书籍
python .scripts/books.py list "Web安全"

# 显示阅读中的 Web 安全书籍
python .scripts/books.py list "Web安全" -s "reading"
```

---

### open - 打开书籍

用默认阅读器打开书籍。

```bash
python .scripts/books.py open BOOK_ID [OPTIONS]
```

**参数：**
- `BOOK_ID`: 书籍 ID（通过 query/list 命令查看）

**选项：**
- `--path-only`: 只显示文件路径，不打开

**示例：**
```bash
# 打开 ID 为 5 的书籍
python .scripts/books.py open 5

# 查看文件路径
python .scripts/books.py open 5 --path-only
```

---

### stats - 统计信息

显示书籍统计信息。

```bash
python .scripts/books.py stats
```

**输出：**
- 总书籍数
- 阅读状态分布
- 评分分布
- 分类统计
- 标签统计
- 总文件大小

---

### edit - 编辑元数据

编辑书籍的元数据信息。

```bash
python .scripts/books.py edit BOOK_ID [OPTIONS]
```

**选项：**
- `--title TEXT`: 书名
- `--author TEXT`: 作者
- `--status TEXT`: 阅读状态
- `--rating INT`: 评分 (1-5)
- `--tag TEXT`: 添加标签（可多选）
- `--remove-tag TEXT`: 删除标签（可多选）
- `--notes TEXT`: 笔记

**示例：**
```bash
# 更新阅读状态
python .scripts/books.py edit 5 --status "reading"

# 添加评分和标签
python .scripts/books.py edit 5 --rating 5 --tag "必读" --tag "经典"

# 添加笔记
python .scripts/books.py edit 5 --notes "重点章节：第3、5章"
```

---

### delete - 删除记录

从数据库中删除书籍记录（不删除实际文件）。

```bash
python .scripts/books.py delete BOOK_ID [OPTIONS]
```

**选项：**
- `--force`: 强制删除，不提示确认

---

## 元数据文件

你可以为每本书创建 `.book.yaml` 文件来手动指定元数据：

```yaml
# AI图片自动分类系统架构设计.pdf.book.yaml
title: AI图片自动分类系统架构设计
author: 张三
isbn: 978-7-xxx-xxxx-x
tags:
  - 人工智能
  - 计算机视觉
  - 深度学习
status: reading
rating: 4
notes: 重点研究分类算法部分
```

元数据文件可以放在：
- 与书籍同目录下（同名 `.yaml` 文件）
- `.metadata/` 目录下（按文件名命名）

## 配置文件

配置文件位于 `.config.yaml`，可自定义：

```yaml
database:
  path: .metadata/library.db

directories:
  file_extensions:
    - ".pdf"
    - ".epub"
    - ".mobi"

viewer:
  pdf_command: open  # macOS
  # pdf_command: xdg-open  # Linux
```

## 快捷命令（可选）

将以下内容添加到你的 shell 配置（`~/.zshrc` 或 `~/.bashrc`）：

```bash
# Books CLI 快捷命令
alias books='python ~/WorkSpace/books/.scripts/books.py'

# 常用命令快捷方式
alias bq='books query'
alias bl='books list'
alias bo='books open'
alias bs='books stats'
alias be='books edit'
```

使用方式：
```bash
# 搜索
bq -k "web"

# 列出
bl "Web安全"

# 打开
bo 5

# 统计
bs
```

## 工作流示例

```bash
# 1. 添加新书到对应目录
cp新书.pdf books/02-Web安全/books/

# 2. 更新索引
books index

# 3. 编辑元数据
be 1 --title "新书名" --tag "web" --tag "2024"

# 4. 标记为阅读中
be 1 --status "reading"

# 5. 打开阅读
bo 1

# 6. 阅读完成，添加评分
be 1 --status "finished" --rating 5

# 7. 查看统计
bs
```

---

**版本**: 0.1.0
**更新**: 2026-01-08
