"""
编辑命令 - 编辑书籍元数据
"""

import click
from pathlib import Path

from ..models import Database
from ..utils import (
    load_config, get_database_path, resolve_absolute_path,
    BookMetadata, MetadataFile
)


@click.command()
@click.argument("book_id", type=int)
@click.option("--title", help="书名")
@click.option("--author", help="作者")
@click.option("--status", type=click.Choice(["unread", "reading", "finished", "reference"]),
              help="阅读状态")
@click.option("--rating", type=int, help="评分 (1-5)")
@click.option("--tag", multiple=True, help="添加标签")
@click.option("--remove-tag", multiple=True, help="删除标签")
@click.option("--notes", help="笔记")
def edit(book_id, title, author, status, rating, tag, remove_tag, notes):
    """编辑书籍元数据"""
    config = load_config()
    db_path = get_database_path(config)

    # 获取 library_dir 用于元数据文件路径解析
    library_dir = config.get("library_dir", "library")
    base_path = Path(__file__).parent.parent.parent.parent / library_dir

    db = Database(db_path)
    db.connect()

    book = db.get_book(book_id)

    if not book:
        db.close()
        click.echo(f"错误: 找不到 ID 为 {book_id} 的书籍")
        return

    # 更新字段
    if title:
        book.title = title
    if author:
        book.author = author
    if status:
        book.status = status
    if rating is not None:
        book.rating = max(0, min(5, rating))
    if notes:
        book.notes = notes

    # 处理标签
    if tag or remove_tag:
        from ..utils.metadata import BookMetadata
        current_tags = BookMetadata.tags_from_json(book.tags)

        # 添加新标签
        for t in tag:
            if t not in current_tags:
                current_tags.append(t)

        # 删除标签
        for t in remove_tag:
            if t in current_tags:
                current_tags.remove(t)

        book.tags = BookMetadata(current_tags).tags_to_json()

    # 保存到数据库
    if db.update_book(book):
        click.echo(f"✅ 已更新书籍: {book.title}")

        # 同步更新元数据文件（如果是扁平化存储的新结构）
        if book.metadata_file:
            metadata_path = base_path / book.metadata_file
            if metadata_path.exists():
                # 重新生成元数据文件
                book_dict = {
                    "title": book.title,
                    "author": book.author,
                    "category": book.category,
                    "tags": BookMetadata.tags_from_json(book.tags),
                    "status": book.status,
                    "rating": book.rating,
                    "pages": book.pages,
                    "filesize": book.filesize,
                    "added_at": book.added_at,
                    "notes": book.notes
                }
                try:
                    MetadataFile.update(metadata_path, book_dict)
                    click.echo(f"  元数据文件已更新: {metadata_path}")
                except Exception as e:
                    click.echo(f"  警告: 元数据文件更新失败 - {e}")
    else:
        click.echo("❌ 更新失败")

    db.close()
