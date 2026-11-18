"""
统计命令 - 显示书籍统计信息
"""

import click
from tabulate import tabulate

from ..models import Database
from ..utils import load_config, get_database_path, format_filesize


@click.command()
def stats():
    """显示书籍统计信息"""
    config = load_config()
    db_path = get_database_path(config)

    db = Database(db_path)
    db.connect()

    stats = db.get_stats()
    all_books = db.search_books(limit=10000)
    tags = db.get_all_tags()

    db.close()

    table_format = config.get("display", {}).get("table_format", "pretty")

    # 总体统计
    click.echo("=" * 50)
    click.echo("📚 书籍统计")
    click.echo("=" * 50)

    click.echo(f"\n总计: {stats['total']} 本")

    # 按状态统计
    click.echo("\n📊 阅读状态:")
    status_map = {
        "unread": ("📚 未读", "未读"),
        "reading": ("📖 阅读中", "阅读中"),
        "finished": ("✅ 已读完", "已读完"),
        "reference": ("📋 参考书", "参考书")
    }

    for status, (label, cn_name) in status_map.items():
        count = stats['by_status'].get(status, 0)
        if count > 0:
            percentage = (count / stats['total'] * 100) if stats['total'] > 0 else 0
            click.echo(f"  {label}: {count} 本 ({percentage:.1f}%)")

    # 按评分统计
    if stats['by_rating']:
        click.echo("\n⭐ 评分分布:")
        for rating in sorted(stats['by_rating'].keys(), reverse=True):
            count = stats['by_rating'][rating]
            click.echo(f"  {'⭐' * rating} {rating} 星: {count} 本")

    # 按分类统计（前 10）
    click.echo("\n📂 分类统计:")
    rows = []
    for category, count in list(stats['by_category'].items())[:10]:
        rows.append([category, count])

    click.echo(tabulate(rows, headers=["分类", "数量"], tablefmt=table_format))

    # 标签统计
    if tags:
        click.echo(f"\n🏷️  热门标签 (共 {len(tags)} 个):")
        click.echo(f"  {', '.join(tags[:20])}")

    # 文件大小统计
    total_size = sum(b.filesize for b in all_books)
    click.echo(f"\n💾 总大小: {format_filesize(total_size)}")
