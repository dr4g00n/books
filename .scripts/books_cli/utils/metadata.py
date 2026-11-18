"""
元数据文件处理（YAML 格式）
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import yaml


@dataclass
class BookMetadata:
    """书籍元数据"""
    title: str = ""
    author: str = ""
    isbn: str = ""
    tags: List[str] = field(default_factory=list)
    status: str = "unread"
    rating: int = 0
    notes: str = ""

    @classmethod
    def from_file(cls, filepath: str) -> "BookMetadata":
        """从 YAML 文件加载元数据"""
        path = Path(filepath)
        if not path.exists():
            return cls()

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            return cls(
                title=data.get("title", ""),
                author=data.get("author", ""),
                isbn=data.get("isbn", ""),
                tags=data.get("tags", []),
                status=data.get("status", "unread"),
                rating=data.get("rating", 0),
                notes=data.get("notes", "")
            )

    def to_file(self, filepath: str):
        """保存元数据到 YAML 文件"""
        data = {
            "title": self.title,
            "author": self.author,
            "isbn": self.isbn,
            "tags": self.tags,
            "status": self.status,
            "rating": self.rating,
            "notes": self.notes
        }
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)

    @classmethod
    def find_metadata_file(cls, book_filepath: str) -> Optional[str]:
        """查找书籍对应的元数据文件"""
        book_path = Path(book_filepath)

        # 尝试同目录下的 .book.yaml
        metadata_path = book_path.with_suffix(".yaml")
        if metadata_path.exists():
            return str(metadata_path)

        # 尝试 .metadata 目录
        metadata_dir = Path(book_path.parent.parent) / ".metadata"
        if metadata_dir.exists():
            metadata_file = metadata_dir / f"{book_path.stem}.yaml"
            if metadata_file.exists():
                return str(metadata_file)

        return None

    def tags_to_json(self) -> str:
        """将标签列表转换为 JSON 字符串"""
        return json.dumps(self.tags, ensure_ascii=False)

    @classmethod
    def tags_from_json(cls, tags_json: str) -> List[str]:
        """从 JSON 字符串解析标签列表"""
        try:
            return json.loads(tags_json)
        except:
            return []
