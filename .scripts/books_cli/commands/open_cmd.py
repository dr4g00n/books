"""
打开命令 - 用默认阅读器打开书籍
"""

import click

from ..models import Database
from ..utils import load_config, get_database_path, open_file, resolve_absolute_path


@click.command()
@click.argument("book_id", type=int)
@click.option("--path-only", is_flag=True, help="只显示文件路径，不打开")
def open_cmd(book_id, path_only):
    """打开指定 ID 的书籍"""
    config = load_config()
    db_path = get_database_path(config)

    db = Database(db_path)
    db.connect()

    book = db.get_book(book_id)

    db.close()

    if not book:
        click.echo(f"错误: 找不到 ID 为 {book_id} 的书籍")
        return

    # 解析绝对路径
    abs_path = resolve_absolute_path(book.filepath)

    if path_only:
        click.echo(abs_path)
    else:
        pdf_command = config.get("viewer", {}).get("pdf_command", "open")
        if open_file(abs_path, pdf_command):
            click.echo(f"正在打开: {book.title}")
        else:
            click.echo(f"错误: 无法打开文件 {abs_path}")
