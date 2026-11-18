"""
索引命令 - 扫描并建立数据库索引
"""

import sys
from pathlib import Path

import click

from ..models import Database
from ..utils import Indexer, load_config, get_database_path


@click.command()
@click.option("--force", is_flag=True, help="强制重新索引所有文件")
def index(force):
    """扫描目录并建立索引"""
    config = load_config()
    db_path = get_database_path(config)

    # 初始化数据库
    db = Database(db_path)
    db.connect()
    db.init_tables()

    # 如果是强制模式，清空现有数据
    if force:
        if click.confirm("确定要清空现有索引并重新建立吗？"):
            db.conn.execute("DELETE FROM books")
            db.conn.commit()
            click.echo("已清空现有索引")
        else:
            db.close()
            return

    # 创建索引器
    base_path = Path(__file__).parent.parent.parent.parent
    indexer = Indexer(
        base_path=str(base_path),
        ignore_patterns=config.get("directories", {}).get("ignore_patterns", []),
        file_extensions=config.get("directories", {}).get("file_extensions", []),
        library_dir=config.get("library_dir", "library"),
        default_category=config.get("default_category", "99-参考资料")
    )

    click.echo("正在扫描目录...")

    # 执行索引
    def progress_callback(current, total, filename):
        # 使用 \033[K 清除行尾残留内容
        click.echo(f"\r[{current}/{total}] {filename}\033[K", nl=False)

    stats = indexer.index_directory(db, progress_callback=progress_callback)

    click.echo(f"\n\n索引完成！")
    click.echo(f"  扫描: {stats['scanned']} 个文件")
    click.echo(f"  新增: {stats['added']} 本")
    click.echo(f"  更新: {stats['updated']} 本")

    db.close()
