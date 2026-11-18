"""
查询命令 - 搜索和过滤书籍
"""

import json
from typing import List

import click
from tabulate import tabulate

from ..models import Database
from ..utils import load_config, get_database_path, format_filesize


@click.command()
@click.option("--keyword", "-k", help="关键词搜索（标题/作者/笔记）")
@click.option("--category", "-c", help="按分类筛选")
@click.option("--status", "-s", help="按状态筛选 (unread/reading/finished/reference)")
@click.option("--tags", "-T", help="按标签过滤（逗号分隔）")
@click.option("--tag", "-t", help="按单个标签精确匹配")
@click.option("--rating", "-r", type=int, help="最低评分")
@click.option("--limit", "-l", default=20, help="最大结果数")
def query(keyword, category, status, tags, tag, rating, limit):
    """查询书籍"""
    config = load_config()
    db_path = get_database_path(config)

    db = Database(db_path)
    db.connect()

    # 处理标签参数
    tag_list = []
    if tags:
        # 处理逗号分隔的标签，过滤空标签
        tag_list.extend([t.strip() for t in tags.split(",") if t.strip()])
    if tag:
        # 添加单个标签（如果非空）
        if tag.strip():
            tag_list.append(tag.strip())

    # 去重（避免重复查询条件）
    if tag_list:
        tag_list = list(set(tag_list))

    # 执行查询
    books = db.search_books(
        keyword=keyword or "",
        category=category or "",
        status=status or "",
        tags=tag_list if tag_list else None,
        min_rating=rating or 0,
        limit=limit
    )

    db.close()

    # 显示结果
    if not books:
        click.echo("没有找到匹配的书籍")
        return

    # 格式化输出
    table_format = config.get("display", {}).get("table_format", "pretty")
    show_path = config.get("display", {}).get("show_path", True)

    headers = ["ID", "标题", "作者", "分类", "状态", "评分"]
    if show_path:
        headers.append("路径")

    rows = []
    for book in books:
        row = [
            book.id,
            book.title[:30] if len(book.title) > 30 else book.title,
            book.author[:15] if len(book.author) > 15 else book.author or "-",
            book.category[:10] if len(book.category) > 10 else book.category,
            _status_symbol(book.status),
            "⭐" * book.rating if book.rating > 0 else "-"
        ]
        if show_path:
            row.append(book.filepath[:40] if len(book.filepath) > 40 else book.filepath)
        rows.append(row)

    click.echo(tabulate(rows, headers=headers, tablefmt=table_format))
    click.echo(f"\n共找到 {len(books)} 本书籍")


def _status_symbol(status: str) -> str:
    """状态符号映射"""
    symbols = {
        "unread": "📚 未读",
        "reading": "📖 阅读",
        "finished": "✅ 已读",
        "reference": "📋 参考"
    }
    return symbols.get(status, status)
