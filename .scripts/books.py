#!/usr/bin/env python3
"""
Books CLI 命令行入口
"""
import sys
from pathlib import Path

# 添加脚本目录到 Python 路径
script_dir = Path(__file__).parent.resolve()
sys.path.insert(0, str(script_dir))

from books_cli.cli import cli

if __name__ == "__main__":
    cli()
