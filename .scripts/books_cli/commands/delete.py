"""
删除命令 - 从数据库删除书籍记录
"""

import click

from ..models import Database
from ..utils import load_config, get_database_path


@click.command()
@click.argument("book_id", type=int)
@click.option("--force", is_flag=True, help="强制删除，不提示确认")
def delete(book_id, force):
    """从数据库删除书籍记录（不删除实际文件）"""
    config = load_config()
    db_path = get_database_path(config)

    db = Database(db_path)
    db.connect()

    book = db.get_book(book_id)

    if not book:
        db.close()
        click.echo(f"错误: 找不到 ID 为 {book_id} 的书籍")
        return

    # 确认删除
    if not force:
        click.echo(f"即将删除: {book.title}")
        click.echo(f"  分类: {book.category}")
        click.echo(f"  路径: {book.filepath}")
        if not click.confirm("\n确定要从数据库中删除此记录吗？"):
            click.echo("已取消")
            db.close()
            return

    if db.delete_book(book_id):
        click.echo(f"✅ 已删除书籍记录: {book.title}")
        click.echo("   注意: 实际文件未被删除")
    else:
        click.echo("❌ 删除失败")

    db.close()
