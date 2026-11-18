# 扁平化改造实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标:** 将 Books CLI 从多级目录结构改造为扁平化存储，使用 tags 进行分类

**架构:**
- 将书籍从 `books/分类/books/` 迁移到 `library/` 扁平目录
- 每本书配对 `.pdf.md` 元数据文件，使用 YAML frontmatter 存储 tags
- 扩展数据库模型支持 tags 和 metadata_file 字段
- 改造 CLI 命令适配新结构

**技术栈:** Python 3.14, Click, SQLite, PyYAML, PyPDF2

---

## Task 1: 创建 library 目录和更新配置

**Files:**
- Create: `library/`
- Modify: `.config.yaml:1`

**Step 1: 创建 library 目录**

```bash
mkdir -p library
```

**Step 2: 更新配置文件**

在 `.config.yaml` 顶部添加：

```yaml
# 扁平化存储配置
library_dir: library
metadata_suffix: .pdf.md
global_tags:
  - "#书籍"
```

**Step 3: 提交**

```bash
git add library/ .config.yaml
git commit -m "feat: 添加扁平化存储配置"
```

---

## Task 2: 扩展数据库模型

**Files:**
- Modify: `.scripts/books_cli/models/database.py`

**Step 1: 添加 tags 字段到 Book 数据类**

在 `@dataclass` 中添加：

```python
@dataclass
class Book:
    # ... 现有字段 ...
    tags: str = ""  # 新增：JSON 数组字符串，如 '["#安全", "#Rust"]'
    metadata_file: str = ""  # 新增：元数据文件路径
```

**Step 2: 更新 init_tables() 方法**

在 `CREATE TABLE` 语句中添加：

```sql
tags TEXT DEFAULT '[]',
metadata_file TEXT DEFAULT '',
```

**Step 3: 提交**

```bash
git add .scripts/books_cli/models/database.py
git commit -m "feat: 数据库支持 tags 和元数据文件字段"
```

---

## Task 3: 创建元数据文件工具模块

**Files:**
- Create: `.scripts/books_cli/utils/metadata_file.py`

**Step 1: 创建元数据文件处理模块**

```python
"""元数据文件处理 - Obsidian 兼容的 .pdf.md 文件"""

import yaml
from pathlib import Path
from datetime import datetime
from typing import List


class MetadataFile:
    """Obsidian 兼容的元数据文件处理"""

    @staticmethod
    def create(book_data: dict, filepath: Path) -> Path:
        """创建元数据文件

        Args:
            book_data: 书籍数据字典
            filepath: PDF 文件路径

        Returns:
            元数据文件路径
        """
        metadata_path = filepath.with_suffix(filepath.suffix + ".md")

        # 解析 tags
        tags = book_data.get("tags", [])
        if isinstance(tags, str):
            import json
            tags = json.loads(tags)

        # 构建 frontmatter
        frontmatter = {
            "title": book_data.get("title", ""),
            "author": book_data.get("author", ""),
            "category": book_data.get("category", ""),
            "tags": tags,
            "status": book_data.get("status", "unread"),
            "rating": book_data.get("rating", 0),
            "pages": book_data.get("pages", 0),
            "filesize": book_data.get("filesize", 0),
            "added_at": book_data.get("added_at", datetime.now().strftime("%Y-%m-%d")),
            "updated_at": datetime.now().strftime("%Y-%m-%d"),
            "file": filepath.name
        }

        # 写入文件
        content = f"---\n{yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)}---\n\n"

        with open(metadata_path, "w", encoding="utf-8") as f:
            f.write(content)

        return metadata_path

    @staticmethod
    def load(metadata_path: Path) -> dict:
        """从元数据文件加载数据"""
        with open(metadata_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 解析 frontmatter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 2:
                frontmatter = parts[1]
                return yaml.safe_load(frontmatter)

        return {}

    @staticmethod
    def update(metadata_path: Path, book_data: dict):
        """更新元数据文件"""
        existing = MetadataFile.load(metadata_path)
        existing.update(book_data)
        MetadataFile.create(existing, metadata_path.with_suffix("").replace(".pdf.md", ".pdf"))
```

**Step 2: 提交**

```bash
git add .scripts/books_cli/utils/metadata_file.py
git commit -m "feat: 添加 Obsidian 兼容元数据文件处理"
```

---

## Task 4: 实现数据迁移命令

**Files:**
- Create: `.scripts/books_cli/commands/migrate.py`
- Modify: `.scripts/books_cli/cli.py`

**Step 1: 创建 migrate 命令**

```python
"""迁移命令 - 从旧结构迁移到新的扁平化结构"""

import shutil
from pathlib import Path
import click

from ..models import Database
from ..utils import load_config, get_database_path
from ..utils.metadata_file import MetadataFile
from ..utils.indexer import Indexer


@click.command()
@click.option("--dry-run", is_flag=True, help="预览迁移操作")
def migrate(dry_run):
    """迁移现有书籍到扁平化结构"""
    config = load_config()
    db_path = get_database_path(config)
    base_path = Path(__file__).parent.parent.parent.parent

    db = Database(db_path)
    db.connect()

    library_dir = base_path / "library"
    library_dir.mkdir(exist_ok=True)

    # 扫描旧结构的书籍文件
    books_dir = base_path / "books"
    extensions = config.get("directories", {}).get("file_extensions",
                                                         [".pdf", ".epub", ".mobi", ".djvu", ".pptx", ".ppt"])

    # 标签映射规则
    tag_mapping = config.get("tag_mapping", {})

    migrated = 0
    errors = 0

    for ext in extensions:
        for pdf_file in books_dir.rglob(f"*{ext}"):
            # 跳过 swap 和 temp 目录
            if "swap" in str(pdf_file) or "temp" in str(pdf_file):
                continue

            # 提取原分类
            parts = pdf_file.relative_to(base_path).parts
            category = parts[1] if len(parts) > 1 else "未分类"

            # 映射到标签
            tags = tag_mapping.get(category, [f"#{category}", "#书籍"])

            # 从数据库获取书籍信息
            rel_path = str(pdf_file.relative_to(base_path))
            book = db.get_book_by_filepath(rel_path)

            if book:
                # 更新 tags
                book.tags = str(tags)

                # 目标路径
                dest_file = library_dir / pdf_file.name

                if dry_run:
                    click.echo(f"[预览] {pdf_file.name} -> {dest_file.name}")
                    click.echo(f"  标签: {tags}")
                else:
                    # 移动文件
                    shutil.move(str(pdf_file), str(dest_file))

                    # 创建元数据文件
                    book_dict = {
                        "title": book.title,
                        "author": book.author,
                        "category": book.category,
                        "tags": tags,
                        "status": book.status,
                        "rating": book.rating,
                        "pages": book.pages,
                        "filesize": book.filesize,
                        "added_at": book.added_at
                    }
                    MetadataFile.create(book_dict, dest_file)

                    # 更新数据库路径
                    book.filepath = f"library/{dest_file.name}"
                    book.metadata_file = f"library/{dest_file.name}.md"
                    db.update_book(book)

                    migrated += 1
                    click.echo(f"✓ {pdf_file.name}")
            else:
                errors += 1
                click.echo(f"✗ {pdf_file.name} (数据库中无记录)")

    click.echo(f"\n迁移完成! 成功: {migrated}, 错误: {errors}")

    if not dry_run and migrated > 0:
        # 清理旧目录
        click.echo("\n是否删除旧的 books/ 目录？")
        if click.confirm("这会删除所有空的分类目录"):
            for cat_dir in books_dir.iterdir():
                if cat_dir.is_dir() and not cat_dir.name.startswith("."):
                    try:
                        cat_dir.rmdir()  # 只删除空目录
                        click.echo(f"删除空目录: {cat_dir.name}")
                    except:
                        click.echo(f"跳过非空目录: {cat_dir.name}")

    db.close()
```

**Step 2: 注册命令**

在 `cli.py` 中添加：

```python
from .commands.migrate import migrate
cli.add_command(migrate)
```

**Step 3: 提交**

```bash
git add .scripts/books_cli/commands/migrate.py .scripts/books_cli/cli.py
git commit -m "feat: 添加数据迁移命令"
```

---

## Task 5: 改造 organize 命令

**Files:**
- Modify: `.scripts/books_cli/commands/organize.py`

**Step 1: 修改目标目录逻辑**

找到 `target_dir =` 行，修改为：

```python
target_dir = Path(base_path) / config.get("library_dir", "library")
```

**Step 2: 添加元数据文件创建**

在移动文件成功后添加：

```python
# 在 success 分支内，db.update_book() 之后
# 创建元数据文件
from ..utils.metadata_file import MetadataFile

book_dict = {
    "title": existing_book.title,
    "author": existing_book.author,
    "category": existing_book.category,
    "tags": eval(existing_book.tags) if existing_book.tags else ["#书籍"],
    "status": existing_book.status,
    "rating": existing_book.rating,
    "pages": existing_book.pages,
    "filesize": existing_book.filesize,
    "added_at": existing_book.added_at
}
MetadataFile.create(book_dict, new_path)
```

**Step 3: 提交**

```bash
git add .scripts/books_cli/commands/organize.py
git commit -m "refactor: organize 支持扁平化结构和元数据文件"
```

---

## Task 6: 扩展 query 命令支持 tags

**Files:**
- Modify: `.scripts/books_cli/commands/query.py`

**Step 1: 添加 tags 参数**

在 `@click.command()` 装饰器下添加：

```python
@click.option("--tags", "-T", help="按标签过滤")
@click.option("--tag", "-t", help="按单个标签精确匹配")
def query(keyword, category, status, tags, tag):
```

**Step 2: 修改搜索逻辑**

在过滤逻辑中添加 tags 处理：

```python
# 在数据库查询部分
if tags:
    tag_list = tags.split(",")
    for tag in tag_list:
        query += f" AND tags LIKE ?"
        params.append(f"%{tag}%")

if tag:
    query += " AND tags LIKE ?"
    params.append(f"%{tag}%")
```

**Step 3: 提交**

```bash
git add .scripts/books_cli/commands/query.py
git commit -m "feat: query 命令支持 tags 过滤"
```

---

## Task 7: 改造 edit 命令同步元数据文件

**Files:**
- Modify: `.scripts/books_cli/commands/edit.py`

**Step 1: 添加标签操作支持**

更新 `--tag` 和 `--remove-tag` 选项的处理：

```python
# 在处理完数据库更新后
from ..utils.metadata_file import MetadataFile

if book.metadata_file:
    metadata_path = Path(base_path) / book.metadata_file
    if metadata_path.exists():
        # 重新生成元数据文件
        book_dict = {
            "title": book.title,
            "author": book.author,
            "category": book.category,
            "tags": eval(book.tags),
            "status": book.status,
            "rating": book.rating,
            "pages": book.pages,
            "filesize": book.filesize,
            "added_at": book.added_at
        }
        MetadataFile.update(metadata_path, book_dict)
```

**Step 2: 提交**

```bash
git add .scripts/books_cli/commands/edit.py
git commit -m "feat: edit 命令同步更新 .md 元数据文件"
```

---

## Task 8: 更新配置文件的标签映射

**Files:**
- Modify: `.config.yaml`

**Step 1: 添加完整的标签映射**

```yaml
# 标签映射规则（用于迁移和自动分类）
tag_mapping:
  "01-网络安全":
    - "#网络安全"
    - "#书籍"
  "02-Web安全":
    - "#Web安全"
    - "#书籍"
  "03-二进制安全":
    - "#二进制安全"
    - "#书籍"
  "04-移动安全":
    - "#移动安全"
    - "#书籍"
  "05-安全开发":
    - "#安全开发"
    - "#书籍"
  "06-安全运营":
    - "#安全运营"
    - "#书籍"
  "07-密码学":
    - "#密码学"
    - "#书籍"
  "08-合规与审计":
    - "#合规与审计"
    - "#书籍"
  "09-红蓝对抗":
    - "#红蓝对抗"
    - "#书籍"
  "10-恶意软件分析":
    - "#恶意软件分析"
    - "#书籍"
  "11-云安全":
    - "#云安全"
    - "#书籍"
  "12-人工智能安全":
    - "#人工智能安全"
    - "#书籍"
  "88-开发技术":
    - "#开发技术"
    - "#书籍"
  "99-参考资料":
    - "#参考资料"
    - "#书籍"
```

**Step 2: 提交**

```bash
git add .config.yaml
git commit -m "feat: 添加完整的标签映射配置"
```

---

## Task 9: 更新交互式菜单

**Files:**
- Modify: `start.sh`

**Step 1: 添加标签管理菜单项**

在菜单中添加新选项：

```bash
echo "  b. 标签管理"
```

**Step 2: 添加标签管理函数**

```bash
manage_tags() {
    echo ""
    echo "标签管理功能"
    echo "1. 查看所有标签"
    echo "2. 为书籍添加标签"
    echo ""
    read -p "请选择: " choice

    case "$choice" in
        1)
            "$PYTHON" "$CLI" query --format tags
            ;;
        2)
            read -p "输入书籍ID: " book_id
            read -p "输入标签(如 #Python): " tag
            "$PYTHON" "$CLI" edit "$book_id" --tag "$tag"
            ;;
    esac
    pause
}
```

**Step 3: 更新主循环**

在 case 语句中添加：

```bash
b|B) manage_tags ;;
```

**Step 4: 提交**

```bash
git add start.sh
git commit -m "feat: 添加标签管理功能到交互式菜单"
```

---

## Task 10: 测试迁移功能

**Files:**
- Test: 手动测试

**Step 1: 预演迁移**

```bash
# 预览迁移结果
venv/bin/python3 .scripts/books.py migrate --dry-run
```

**Step 2: 执行迁移**

```bash
# 实际执行迁移
venv/bin/python3 .scripts/books.py migrate
```

**Step 3: 验证结果**

```bash
# 检查 library 目录
ls -la library/

# 查看元数据文件
cat library/*.pdf.md | head -20

# 查询测试
venv/bin/python3 .scripts/books.py query --tags "#书籍"
```

**Step 4: 提交**

```bash
git add .
git commit -m "chore: 完成扁平化迁移测试"
```

---

## 测试验证

```bash
# 1. 测试元数据文件生成
python .scripts/books.py migrate --dry-run

# 2. 测试标签查询
python .scripts/books.py query --tags "#Python"

# 3. 测试标签编辑
python .scripts/books.py edit 1 --tag "#测试"

# 4. 验证 .md 文件格式
cat library/某本书.pdf.md
```
