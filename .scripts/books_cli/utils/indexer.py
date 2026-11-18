"""
目录索引器 - 扫描目录并建立索引
"""

import os
from pathlib import Path
from typing import List, Optional

try:
    import PyPDF2
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False

from ..models.database import Book
from .metadata import BookMetadata


class Indexer:
    """目录索引器"""

    def __init__(self, base_path: str, ignore_patterns: List[str] = None,
                 file_extensions: List[str] = None,
                 library_dir: str = "library", default_category: str = "99-参考资料"):
        self.base_path = Path(base_path)
        self.ignore_patterns = ignore_patterns or [".scripts", ".metadata", ".git"]
        self.file_extensions = file_extensions or [".pdf", ".epub", ".mobi", ".djvu"]
        self.library_dir = library_dir
        self.default_category = default_category

    def scan_directory(self) -> List[Path]:
        """扫描目录获取所有书籍文件"""
        books = []

        for root, dirs, files in os.walk(self.base_path):
            # 过滤忽略的目录
            dirs[:] = [d for d in dirs if d not in self.ignore_patterns
                      and not d.startswith(".")]

            for file in files:
                file_path = Path(root) / file

                # 检查文件扩展名
                if any(file.lower().endswith(ext) for ext in self.file_extensions):
                    books.append(file_path)

        return books

    def extract_pdf_metadata(self, filepath: str) -> dict:
        """提取 PDF 元数据"""
        metadata = {
            "title": "",
            "author": "",
            "pages": 0
        }

        if not HAS_PYPDF2:
            # 如果没有 PyPDF2，使用文件名作为标题
            path = Path(filepath)
            metadata["title"] = path.stem
            return metadata

        try:
            with open(filepath, "rb") as f:
                pdf_reader = PyPDF2.PdfReader(f)

                # 提取元数据
                info = pdf_reader.metadata
                if info:
                    metadata["title"] = info.get("/Title", "")
                    metadata["author"] = info.get("/Author", "")

                # 获取页数
                metadata["pages"] = len(pdf_reader.pages)

        except Exception as e:
            # 解析失败，使用文件名
            path = Path(filepath)
            metadata["title"] = path.stem

        # 如果没有提取到标题，使用文件名
        if not metadata["title"]:
            metadata["title"] = Path(filepath).stem

        return metadata

    def extract_category(self, filepath: str) -> str:
        """从文件路径提取分类"""
        path = Path(filepath)
        relative = path.relative_to(self.base_path)

        parts = relative.parts

        # 扁平化书库：文件直接放在 library/ 下时，目录名不是真实分类，
        # 使用默认分类（细分由 organize 或手动编辑完成）
        if len(parts) == 2 and parts[0] == self.library_dir:
            return self.default_category

        # 处理路径结构 books/分类/books/文件.pdf 或 books/分类/子目录/文件.pdf
        if len(parts) >= 2:
            # 如果第一级是 "books"，使用第二级作为分类
            if parts[0] == "books" and len(parts) >= 3:
                category = parts[1]
            else:
                # 否则使用第一级作为分类
                category = parts[0]

            # 不移除数字前缀，保持完整的分类名称（如 "88-开发技术"）
            return category

        return "未分类"

    def create_book_from_file(self, filepath: Path) -> Book:
        """从文件创建 Book 对象"""
        abs_path = str(filepath.resolve())
        rel_path = str(filepath.relative_to(self.base_path))

        # 提取 PDF 元数据
        pdf_metadata = self.extract_pdf_metadata(abs_path)

        # 提取分类
        category = self.extract_category(abs_path)

        # 获取文件大小
        file_size = filepath.stat().st_size

        # 查找元数据文件
        metadata = BookMetadata()
        metadata_file = BookMetadata.find_metadata_file(abs_path)
        if metadata_file:
            metadata = BookMetadata.from_file(metadata_file)

        # 如果元数据中有标题，优先使用
        title = metadata.title or pdf_metadata.get("title", "")
        if not title:
            title = filepath.stem

        # 创建 Book 对象
        book = Book(
            title=title,
            author=metadata.author or pdf_metadata.get("author", ""),
            category=category,
            filepath=rel_path,
            filesize=file_size,
            pages=pdf_metadata.get("pages", 0),
            tags=metadata.tags_to_json(),
            status=metadata.status,
            rating=metadata.rating,
            notes=metadata.notes
        )

        return book

    def index_directory(self, db, progress_callback=None) -> dict:
        """索引整个目录并更新数据库"""
        files = self.scan_directory()

        stats = {
            "scanned": len(files),
            "added": 0,
            "updated": 0,
            "skipped": 0
        }

        for i, filepath in enumerate(files):
            if progress_callback:
                progress_callback(i + 1, len(files), filepath.name)

            # 创建 Book 对象
            book = self.create_book_from_file(filepath)

            # 检查是否已存在
            existing = db.get_book_by_filepath(book.filepath)

            if existing:
                # 更新现有记录：只刷新文件派生信息，
                # 保留用户整理的元数据（分类/标签/状态/评分/笔记等）
                book.id = existing.id
                book.category = existing.category
                book.tags = existing.tags
                book.status = existing.status
                book.rating = existing.rating
                book.notes = existing.notes
                book.isbn = existing.isbn
                book.metadata_file = existing.metadata_file
                book.author = existing.author or book.author
                book.title = existing.title or book.title
                db.update_book(book)
                stats["updated"] += 1
            else:
                # 添加新记录
                db.add_book(book)
                stats["added"] += 1

        return stats
