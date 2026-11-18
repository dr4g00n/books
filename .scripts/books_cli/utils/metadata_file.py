"""元数据文件处理 - Obsidian 兼容的 .pdf.md 文件"""

import yaml
from pathlib import Path
from datetime import datetime
from typing import List


class MetadataFile:
    """Obsidian 兼容的元数据文件处理"""

    @staticmethod
    def create(book_data: dict, filepath: Path) -> Path:
        """创建元数据文件

        Args:
            book_data: 书籍数据字典
            filepath: PDF 文件路径

        Returns:
            元数据文件路径
        """
        metadata_path = filepath.with_suffix(filepath.suffix + ".md")

        # 解析 tags
        tags = book_data.get("tags", [])
        if isinstance(tags, str):
            import json
            tags = json.loads(tags)

        # 构建 frontmatter
        frontmatter = {
            "title": book_data.get("title", ""),
            "author": book_data.get("author", ""),
            "category": book_data.get("category", ""),
            "tags": tags,
            "status": book_data.get("status", "unread"),
            "rating": book_data.get("rating", 0),
            "pages": book_data.get("pages", 0),
            "filesize": book_data.get("filesize", 0),
            "added_at": book_data.get("added_at", datetime.now().strftime("%Y-%m-%d")),
            "updated_at": datetime.now().strftime("%Y-%m-%d"),
            "file": filepath.name
        }

        # 写入文件
        content = f"---\n{yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)}---\n\n"

        with open(metadata_path, "w", encoding="utf-8") as f:
            f.write(content)

        return metadata_path

    @staticmethod
    def load(metadata_path: Path) -> dict:
        """从元数据文件加载数据"""
        with open(metadata_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 解析 frontmatter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 2:
                frontmatter = parts[1]
                return yaml.safe_load(frontmatter)

        return {}

    @staticmethod
    def update(metadata_path: Path, book_data: dict):
        """更新元数据文件"""
        existing = MetadataFile.load(metadata_path)
        existing.update(book_data)
        MetadataFile.create(existing, metadata_path.with_suffix("").replace(".pdf.md", ".pdf"))
