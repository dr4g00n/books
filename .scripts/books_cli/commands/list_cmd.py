"""
列表命令 - 按分类列出书籍
"""

import click
from tabulate import tabulate

from ..models import Database
from ..utils import load_config, get_database_path


@click.command()
@click.argument("category", required=False)
@click.option("--status", "-s", help="按状态筛选")
def list_cmd(category, status):
    """列出书籍（可指定分类）"""
    config = load_config()
    db_path = get_database_path(config)

    db = Database(db_path)
    db.connect()

    if category:
        # 列出指定分类的书籍
        books = db.search_books(category=category, status=status or "")
        if not books:
            click.echo(f"分类 '{category}' 下没有书籍")
            db.close()
            return
    else:
        # 列出所有分类
        categories = db.get_all_categories()
        if not categories:
            click.echo("暂无书籍")
            db.close()
            return

        table_format = config.get("display", {}).get("table_format", "pretty")

        # 显示分类列表
        rows = []
        for cat in categories:
            count = len(db.search_books(category=cat))
            rows.append([cat, count])

        click.echo(tabulate(rows, headers=["分类", "数量"], tablefmt=table_format))
        db.close()
        return

    db.close()

    # 显示该分类下的书籍
    table_format = config.get("display", {}).get("table_format", "pretty")

    headers = ["ID", "标题", "作者", "状态", "评分"]
    rows = []
    for book in books:
        rows.append([
            book.id,
            book.title[:40] if len(book.title) > 40 else book.title,
            book.author[:20] if len(book.author) > 20 else book.author or "-",
            _status_symbol(book.status),
            "⭐" * book.rating if book.rating > 0 else "-"
        ])

    click.echo(f"\n分类: {category}")
    click.echo(tabulate(rows, headers=headers, tablefmt=table_format))
    click.echo(f"\n共 {len(books)} 本书籍")


def _status_symbol(status: str) -> str:
    """状态符号映射"""
    symbols = {
        "unread": "📚 未读",
        "reading": "📖 阅读",
        "finished": "✅ 已读",
        "reference": "📋 参考"
    }
    return symbols.get(status, status)
