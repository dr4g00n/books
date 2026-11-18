"""
Books CLI - 个人安全技术书籍查询系统
主命令入口
"""

import click

from .commands.index import index
from .commands.query import query
from .commands.list_cmd import list_cmd
from .commands.open_cmd import open_cmd
from .commands.stats import stats
from .commands.edit import edit
from .commands.delete import delete
from .commands.organize import organize
from .commands.migrate import migrate


@click.group()
@click.version_option(version="0.1.0", prog_name="books-cli")
def cli():
    """
    📚 Books CLI - 个人安全技术书籍查询系统

    快速查询、管理和打开你的安全技术书籍资料。
    """
    pass


# 注册命令
cli.add_command(index)
cli.add_command(query)
cli.add_command(list_cmd, name="list")
cli.add_command(open_cmd, name="open")
cli.add_command(stats)
cli.add_command(edit)
cli.add_command(delete)
cli.add_command(organize)
cli.add_command(migrate)


if __name__ == "__main__":
    cli()
