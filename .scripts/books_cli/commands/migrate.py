"""
迁移命令 - 从旧结构迁移到新的扁平化结构
"""

import json
import shutil
from pathlib import Path

import click

from ..models import Database
from ..utils import load_config, get_database_path
from ..utils.metadata_file import MetadataFile


def handle_name_conflict(dest_file: Path) -> Path:
    """处理同名文件冲突，返回新的目标路径"""
    if not dest_file.exists():
        return dest_file

    original_name = dest_file.stem
    extension = dest_file.suffix
    counter = 1

    while dest_file.exists():
        new_name = f"{original_name}_{counter}{extension}"
        dest_file = dest_file.parent / new_name
        counter += 1

    return dest_file


@click.command()
@click.option("--dry-run", is_flag=True, help="预览迁移操作")
def migrate(dry_run):
    """迁移现有书籍到扁平化结构"""
    config = load_config()
    db_path = get_database_path(config)
    base_path = Path(__file__).parent.parent.parent.parent

    db = Database(db_path)

    try:
        db.connect()

        library_dir = base_path / "library"
        library_dir.mkdir(exist_ok=True)

        # 扫描旧结构的书籍文件
        books_dir = base_path / "books"
        extensions = config.get("directories", {}).get("file_extensions",
                                                             [".pdf", ".epub", ".mobi", ".djvu", ".pptx", ".ppt"])

        # 标签映射规则 - 使用 category_keywords 进行智能标签映射
        category_keywords = config.get("category_keywords", {})
        global_tags = config.get("global_tags", ["#书籍"])

        # 统计变量
        stats = {
            "migrated": 0,
            "errors": 0,
            "not_found": 0,
            "total": 0
        }

        click.echo("扫描旧结构中的书籍文件...\n")

        for ext in extensions:
            for pdf_file in books_dir.rglob(f"*{ext}"):
                # 跳过 swap 和 temp 目录
                if "swap" in str(pdf_file) or "temp" in str(pdf_file) or "tmp" in str(pdf_file):
                    continue

                stats["total"] += 1

                # 提取原分类
                parts = pdf_file.relative_to(books_dir).parts
                if len(parts) > 0:
                    category = parts[0]
                else:
                    category = "未分类"

                # 构建标签：使用 category_keywords 映射规则
                # 如果分类在映射规则中，使用映射的标签；否则使用分类名和全局标签
                if category in category_keywords:
                    # 从 category_keywords 中提取关键词并转换为标签
                    keywords = category_keywords[category]
                    category_tags = [f"#{kw}" for kw in keywords]
                    tags = category_tags + global_tags
                else:
                    # 如果没有映射规则，使用分类名和全局标签
                    tags = [f"#{category}"] + global_tags

                # 从数据库获取书籍信息
                rel_path = str(pdf_file.relative_to(base_path))
                book = db.get_book_by_filepath(rel_path)

                if book:
                    # 目标路径
                    dest_file = library_dir / pdf_file.name

                    # 处理同名冲突
                    final_dest = handle_name_conflict(dest_file)

                    # 检查是否是重命名的文件
                    is_renamed = final_dest.name != pdf_file.name

                    if dry_run:
                        click.echo(f"[预览] {pdf_file.name}")
                        click.echo(f"  源路径: {rel_path}")
                        click.echo(f"  目标路径: library/{final_dest.name}")
                        if is_renamed:
                            click.echo(f"  (原名冲突，自动重命名)")
                        click.echo(f"  分类: {category}")
                        click.echo(f"  标签: {tags}")
                        click.echo()
                        stats["migrated"] += 1
                    else:
                        # 移动文件 - 使用事务处理确保数据一致性
                        file_moved = False
                        metadata_created = False
                        original_file = pdf_file

                        try:
                            # 步骤 1: 移动文件
                            shutil.move(str(original_file), str(final_dest))
                            file_moved = True

                            # 步骤 2: 创建元数据文件
                            try:
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
                                MetadataFile.create(book_dict, final_dest)
                                metadata_created = True

                                # 步骤 3: 更新数据库路径
                                book.filepath = f"library/{final_dest.name}"
                                book.metadata_file = f"library/{final_dest.name}.md"
                                # 更新标签为 JSON 格式
                                book.tags = json.dumps(tags, ensure_ascii=False)
                                db.update_book(book)

                                stats["migrated"] += 1
                                status_str = f"[成功] {pdf_file.name}"
                                if is_renamed:
                                    status_str += f" -> {final_dest.name}"
                                click.echo(status_str)

                            except Exception as e:
                                # 元数据创建或数据库更新失败，回滚文件移动
                                if file_moved:
                                    try:
                                        shutil.move(str(final_dest), str(original_file))
                                    except:
                                        pass
                                stats["errors"] += 1
                                click.echo(f"[错误] {pdf_file.name}: 元数据或数据库更新失败 - {e}")

                        except Exception as e:
                            # 文件移动失败
                            stats["errors"] += 1
                            click.echo(f"[错误] {pdf_file.name}: 文件移动失败 - {e}")
                else:
                    stats["not_found"] += 1
                    if dry_run:
                        click.echo(f"[未找到] {pdf_file.name} (数据库中无记录)")

        if dry_run:
            # 预览模式下显示汇总
            click.echo("\n" + "="*60)
            click.echo("预览汇总:")
            click.echo(f"  扫描到: {stats['total']} 个文件")
            click.echo(f"  可迁移: {stats['migrated']} 个文件")
            click.echo(f"  未找到: {stats['not_found']} 个文件 (数据库中无记录)")
            if stats['not_found'] > 0:
                click.echo("\n提示: 未找到的文件不会迁移，需先运行 index 命令建立索引")
        else:
            click.echo(f"\n迁移完成!")
            click.echo(f"  成功: {stats['migrated']}")
            click.echo(f"  错误: {stats['errors']}")
            click.echo(f"  未找到: {stats['not_found']}")

        if not dry_run and stats["migrated"] > 0:
            # 清理旧目录
            click.echo("\n是否删除旧的 books/ 目录中的空分类目录？")
            if click.confirm("这会删除所有空的分类目录"):
                for cat_dir in books_dir.iterdir():
                    if cat_dir.is_dir() and not cat_dir.name.startswith("."):
                        try:
                            # 尝试删除空目录
                            cat_dir.rmdir()
                            click.echo(f"删除空目录: {cat_dir.name}")
                        except OSError:
                            # 目录非空，跳过
                            pass
                click.echo("清理完成，非空目录已保留")

    finally:
        # 确保数据库连接总是被关闭
        db.close()
