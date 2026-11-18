"""
数据库模型和操作
"""

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional


@dataclass
class Book:
    """书籍数据模型"""
    id: Optional[int] = None
    title: str = ""
    author: str = ""
    isbn: str = ""
    category: str = ""
    filepath: str = ""
    filesize: int = 0
    pages: int = 0
    tags: str = ""  # JSON 格式存储标签列表
    metadata_file: str = ""  # 元数据文件路径
    status: str = "unread"
    rating: int = 0
    added_at: str = ""
    updated_at: str = ""
    notes: str = ""


class Database:
    """数据库操作类"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self):
        """建立数据库连接"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()

    def init_tables(self):
        """初始化数据库表结构"""
        cursor = self.conn.cursor()

        # 书籍表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT,
                isbn TEXT,
                category TEXT NOT NULL,
                filepath TEXT NOT NULL UNIQUE,
                filesize INTEGER DEFAULT 0,
                pages INTEGER DEFAULT 0,
                tags TEXT DEFAULT '[]',
                status TEXT DEFAULT 'unread',
                rating INTEGER DEFAULT 0,
                added_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                metadata_file TEXT DEFAULT ''
            )
        """)

        # 标签表（用于快速查询）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                count INTEGER DEFAULT 0
            )
        """)

        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON books(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON books(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rating ON books(rating)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_title ON books(title)")

        self.conn.commit()

    def add_book(self, book: Book) -> int:
        """添加书籍"""
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        book.added_at = now
        book.updated_at = now

        cursor.execute("""
            INSERT INTO books (title, author, isbn, category, filepath,
                             filesize, pages, tags, metadata_file, status, rating, added_at, updated_at, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (book.title, book.author, book.isbn, book.category, book.filepath,
              book.filesize, book.pages, book.tags, book.metadata_file, book.status, book.rating,
              book.added_at, book.updated_at, book.notes))

        self.conn.commit()
        return cursor.lastrowid

    def get_book(self, book_id: int) -> Optional[Book]:
        """根据 ID 获取书籍"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM books WHERE id = ?", (book_id,))
        row = cursor.fetchone()
        if row:
            return self._row_to_book(row)
        return None

    def get_book_by_filepath(self, filepath: str) -> Optional[Book]:
        """根据文件路径获取书籍"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM books WHERE filepath = ?", (filepath,))
        row = cursor.fetchone()
        if row:
            return self._row_to_book(row)
        return None

    def update_book(self, book: Book) -> bool:
        """更新书籍信息"""
        cursor = self.conn.cursor()
        book.updated_at = datetime.now().isoformat()

        cursor.execute("""
            UPDATE books SET title=?, author=?, isbn=?, category=?, filepath=?, tags=?, metadata_file=?,
                            status=?, rating=?, notes=?, updated_at=?
            WHERE id=?
        """, (book.title, book.author, book.isbn, book.category, book.filepath, book.tags, book.metadata_file,
              book.status, book.rating, book.notes, book.updated_at, book.id))

        self.conn.commit()
        return cursor.rowcount > 0

    def delete_book(self, book_id: int) -> bool:
        """删除书籍"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    def search_books(self, keyword: str = "", category: str = "",
                    status: str = "", tags: List[str] = None,
                    min_rating: int = 0, limit: int = 50) -> List[Book]:
        """搜索书籍"""
        cursor = self.conn.cursor()

        query = "SELECT * FROM books WHERE 1=1"
        params = []

        if keyword:
            query += " AND (title LIKE ? OR author LIKE ? OR notes LIKE ?)"
            params.extend([f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"])

        if category:
            query += " AND category LIKE ?"
            params.append(f"%{category}%")

        if status:
            query += " AND status = ?"
            params.append(status)

        if min_rating > 0:
            query += " AND rating >= ?"
            params.append(min_rating)

        if tags:
            for tag in tags:
                query += " AND tags LIKE ?"
                params.append(f"%{tag}%")

        query += " ORDER BY added_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [self._row_to_book(row) for row in rows]

    def get_all_categories(self) -> List[str]:
        """获取所有分类"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT category FROM books ORDER BY category")
        return [row[0] for row in cursor.fetchall()]

    def get_all_tags(self) -> List[str]:
        """获取所有标签"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT tags FROM books WHERE tags != '[]'")
        all_tags = set()
        for row in cursor.fetchall():
            import json
            try:
                tags = json.loads(row[0])
                all_tags.update(tags)
            except:
                pass
        return sorted(list(all_tags))

    def get_stats(self) -> dict:
        """获取统计信息"""
        cursor = self.conn.cursor()

        # 总书数
        cursor.execute("SELECT COUNT(*) FROM books")
        total = cursor.fetchone()[0]

        # 按状态统计
        cursor.execute("SELECT status, COUNT(*) FROM books GROUP BY status")
        status_stats = {row[0]: row[1] for row in cursor.fetchall()}

        # 按分类统计
        cursor.execute("SELECT category, COUNT(*) FROM books GROUP BY category ORDER BY COUNT(*) DESC")
        category_stats = {row[0]: row[1] for row in cursor.fetchall()}

        # 按评分统计
        cursor.execute("SELECT rating, COUNT(*) FROM books WHERE rating > 0 GROUP BY rating")
        rating_stats = {row[0]: row[1] for row in cursor.fetchall()}

        return {
            "total": total,
            "by_status": status_stats,
            "by_category": category_stats,
            "by_rating": rating_stats
        }

    def _row_to_book(self, row) -> Book:
        """将数据库行转换为 Book 对象"""
        return Book(
            id=row["id"],
            title=row["title"],
            author=row["author"],
            isbn=row["isbn"],
            category=row["category"],
            filepath=row["filepath"],
            filesize=row["filesize"],
            pages=row["pages"],
            tags=row["tags"],
            metadata_file=row["metadata_file"] if "metadata_file" in row.keys() else "",
            status=row["status"],
            rating=row["rating"],
            added_at=row["added_at"],
            updated_at=row["updated_at"],
            notes=row["notes"]
        )
