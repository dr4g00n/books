"""
整理命令 - 从 swap 目录整理书籍到扁平化图书库
"""

import json
import shutil
from pathlib import Path

import click

from ..models import Database
from ..utils import load_config, get_database_path
from ..utils.metadata_file import MetadataFile


def get_swap_files(base_path: str, file_extensions: list) -> list:
    """扫描 swap 目录获取书籍文件"""
    swap_dir = Path(base_path) / "swap"
    if not swap_dir.exists():
        return []

    files = []
    for file in swap_dir.iterdir():
        if file.is_file() and any(file.name.lower().endswith(ext) for ext in file_extensions):
            files.append(file)
    return sorted(files, key=lambda x: x.name)


def get_available_categories(base_path: str, config: dict) -> list:
    """获取可用的图书分类（从配置文件读取）"""
    # 从配置的 category_keywords 中获取分类列表
    category_keywords = config.get("category_keywords", {})
    categories = sorted(category_keywords.keys())

    # 确保默认分类也在列表中
    default_category = config.get("default_category", "99-参考资料")
    if default_category not in categories:
        categories.append(default_category)

    return categories


def move_file_with_rename(src_file: Path, dst_dir: Path) -> tuple[bool, str, Path]:
    """移动文件，处理同名冲突

    返回: (成功标志, 消息, 新文件路径)
    """
    dst_dir.mkdir(parents=True, exist_ok=True)

    dst_file = dst_dir / src_file.name
    original_name = src_file.stem
    extension = src_file.suffix

    # 处理同名冲突
    counter = 1
    while dst_file.exists():
        new_name = f"{original_name}_{counter}{extension}"
        dst_file = dst_dir / new_name
        counter += 1

    try:
        shutil.move(str(src_file), str(dst_file))
        return True, "移动成功", dst_file
    except Exception as e:
        return False, f"移动失败: {e}", dst_file


def smart_categorize_file(filename: str, db: Database, config: dict) -> tuple[str, str]:
    """根据文件名和配置规则智能判断文件分类

    返回: (分类, 原因说明)
    """
    # 从配置文件读取关键词规则
    CATEGORY_KEYWORDS = config.get("category_keywords", {})

    # 从配置文件读取默认分类
    default_category = config.get("default_category", "99-参考资料")

    # 1. 优先使用关键词规则匹配
    filename_lower = filename.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in filename_lower:
                return category, f"关键词匹配: {keyword}"

    # 2. 尝试数据库匹配（过滤临时目录）
    temp_categories = {"swap", "temp", "tmp", "books"}
    keyword = Path(filename).stem
    books = db.search_books(keyword=keyword, limit=5)

    if books:
        for book in books:
            if book.title.lower() == keyword.lower():
                if book.category.lower() not in temp_categories:
                    return book.category, "数据库匹配"
            if keyword.lower() in book.title.lower():
                if book.category.lower() not in temp_categories:
                    return book.category, "数据库匹配"
        for book in books:
            if book.category.lower() not in temp_categories:
                return book.category, "数据库匹配"

    # 3. 使用默认分类
    return default_category, "默认分类"


def create_metadata_for_book(book, category: str, tags: list, filepath: Path) -> bool:
    """为书籍创建元数据文件

    Args:
        book: 书籍对象（现有或新创建的）
        category: 分类名称
        tags: 标签列表
        filepath: PDF 文件路径

    Returns:
        bool: 是否成功
    """
    try:
        book_dict = {
            "title": book.title,
            "author": book.author,
            "category": category,
            "tags": tags,
            "status": book.status,
            "rating": book.rating,
            "pages": book.pages,
            "filesize": book.filesize,
            "added_at": book.added_at
        }
        MetadataFile.create(book_dict, filepath)
        return True
    except Exception as e:
        return False


@click.command()
@click.option("--category", "-c", help="指定目标分类")
@click.option("--dry-run", is_flag=True, help="预览操作，不实际移动文件")
def organize(category, dry_run):
    """整理 swap 目录的书籍文件到扁平化图书库 (library/)"""
    # 加载配置
    config = load_config()
    db_path = get_database_path(config)
    base_path = Path(__file__).parent.parent.parent.parent

    # 初始化数据库
    db = Database(db_path)
    db.connect()

    # 获取文件扩展名配置
    file_extensions = config.get("directories", {}).get("file_extensions",
                                                         [".pdf", ".epub", ".mobi", ".djvu", ".pptx", ".ppt"])

    # 扫描 swap 目录
    swap_files = get_swap_files(str(base_path), file_extensions)

    if not swap_files:
        click.echo("swap 目录为空或不存在")
        db.close()
        return

    click.echo(f"找到 {len(swap_files)} 个待整理文件:")

    # 获取可用分类
    categories = get_available_categories(str(base_path), config)

    if not categories:
        click.echo("没有可用的目标分类")
        db.close()
        return

    # 为每个文件智能分类
    file_categories = {}
    for f in swap_files:
        cat, reason = smart_categorize_file(f.name, db, config)
        file_categories[f] = (cat, reason)
        size_mb = f.stat().st_size / (1024 * 1024)
        click.echo(f"  {f.name:<50} → {cat:<20} ({reason})")

    click.echo()

    # 确定目标分类（手动指定模式）
    target_category = category

    # 如果指定了手动分类，验证分类是否在配置中
    if target_category:
        category_keywords = config.get("category_keywords", {})
        valid_categories = set(category_keywords.keys()) | {config.get("default_category", "99-参考资料")}
        if target_category not in valid_categories:
            click.echo(f"分类 '{target_category}' 不在配置文件中")
            click.echo("可用分类: " + ", ".join(sorted(valid_categories)))
            db.close()
            return
        # 手动模式下所有文件使用同一分类
        for f in swap_files:
            file_categories[f] = (target_category, "手动指定")
        click.echo(f"手动指定分类: {target_category}")
    else:
        click.echo("智能自动分类模式")

    if dry_run:
        click.echo("(预览模式，不会实际移动文件)")

    if not click.confirm("\n确认开始整理?"):
        click.echo("已取消")
        db.close()
        return

    # 执行整理
    click.echo()
    stats = {"success": 0, "failed": 0, "skipped": 0}

    # 目标目录为扁平化的 library/
    target_dir = Path(base_path) / config.get("library_dir", "library")
    target_dir.mkdir(parents=True, exist_ok=True)

    # 获取全局标签配置
    global_tags = config.get("global_tags", ["#书籍"])
    category_keywords = config.get("category_keywords", {})

    for src_file in swap_files:
        # 获取该文件的分类
        file_category, _ = file_categories[src_file]

        click.echo(f"处理: {src_file.name} -> {file_category}", nl=False)

        if dry_run:
            # 预览模式，只显示会移动到哪里
            dst_file = target_dir / src_file.name
            if dst_file.exists():
                click.echo(f" (已存在，将被重命名)")
            else:
                click.echo()
            stats["success"] += 1
            continue

        # 使用事务处理确保数据一致性
        file_moved = False
        metadata_created = False

        try:
            # 步骤 1: 移动文件
            success, msg, new_path = move_file_with_rename(src_file, target_dir)
            if not success:
                click.echo(f" ✗ {msg}")
                stats["failed"] += 1
                continue
            file_moved = True

            # 计算新的相对路径
            rel_path = str(new_path.relative_to(base_path))
            old_rel_path = str(src_file.relative_to(base_path))

            # 构建标签：使用 category_keywords 映射规则
            if file_category in category_keywords:
                keywords = category_keywords[file_category]
                category_tags = [f"#{kw}" for kw in keywords]
                tags = category_tags + global_tags
            else:
                tags = [f"#{file_category}"] + global_tags

            # 步骤 2: 创建元数据文件和更新数据库
            try:
                # 检查数据库中是否已有该文件的记录
                existing_book = db.get_book_by_filepath(old_rel_path)

                if existing_book:
                    # 更新现有记录
                    existing_book.filepath = rel_path
                    existing_book.category = file_category
                    existing_book.tags = json.dumps(tags, ensure_ascii=False)
                    existing_book.metadata_file = f"{rel_path}.md"
                    db.update_book(existing_book)

                    # 创建元数据文件
                    if create_metadata_for_book(existing_book, file_category, tags, new_path):
                        metadata_created = True
                        stats["success"] += 1
                        click.echo(f" ✓ (已更新数据库记录和元数据)")
                    else:
                        raise Exception("元数据文件创建失败")
                else:
                    # 添加新记录
                    from ..utils.indexer import Indexer
                    indexer = Indexer(str(base_path), [], file_extensions)
                    book = indexer.create_book_from_file(new_path)
                    book.category = file_category
                    book.tags = json.dumps(tags, ensure_ascii=False)
                    book.metadata_file = f"{rel_path}.md"
                    db.add_book(book)

                    # 创建元数据文件
                    if create_metadata_for_book(book, file_category, tags, new_path):
                        metadata_created = True
                        stats["success"] += 1
                        click.echo(f" ✓ (已添加数据库记录和元数据)")
                    else:
                        raise Exception("元数据文件创建失败")

            except Exception as e:
                # 元数据或数据库更新失败，回滚文件移动
                if file_moved:
                    try:
                        # 将文件移回原处
                        shutil.move(str(new_path), str(src_file))
                    except:
                        pass
                stats["failed"] += 1
                click.echo(f" ✗ (元数据或数据库更新失败: {e})")

        except Exception as e:
            # 文件移动或其他未预期的错误
            stats["failed"] += 1
            click.echo(f" ✗ {e}")

    # 显示统计
    click.echo()
    click.echo("整理完成!")
    click.echo(f"  成功: {stats['success']} 个")
    click.echo(f"  失败: {stats['failed']} 个")

    db.close()
