"""
工具函数
"""

import os
import subprocess
from pathlib import Path
from typing import Optional


def format_filesize(size: int) -> str:
    """格式化文件大小"""
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def open_file(filepath: str, pdf_command: str = "open") -> bool:
    """用默认程序打开文件"""
    try:
        path = Path(filepath).resolve()
        if not path.exists():
            return False

        if pdf_command == "open":  # macOS
            subprocess.run(["open", str(path)], check=True)
        elif pdf_command == "xdg-open":  # Linux
            subprocess.run(["xdg-open", str(path)], check=True)
        elif pdf_command == "start":  # Windows
            subprocess.run(["start", str(path)], shell=True, check=True)
        else:
            subprocess.run(pdf_command.split() + [str(path)], check=True)

        return True
    except Exception:
        return False


def load_config(config_path: str = None) -> dict:
    """加载配置文件"""
    if config_path is None:
        # 默认配置文件路径
        script_dir = Path(__file__).parent.parent.parent.parent
        config_path = script_dir / ".config.yaml"

    import yaml
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_database_path(config: dict = None) -> str:
    """获取数据库路径"""
    if config is None:
        config = load_config()

    db_path = config.get("database", {}).get("path", ".metadata/library.db")
    base_path = Path(__file__).parent.parent.parent.parent

    return str(base_path / db_path)


def resolve_absolute_path(relative_path: str, base_path: str = None) -> str:
    """将相对路径转换为绝对路径"""
    if base_path is None:
        base_path = Path(__file__).parent.parent.parent.parent

    return str(base_path / relative_path)
