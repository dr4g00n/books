"""
数据访问层：直接读写 Books CLI 的 SQLite 数据库。
与 CLI 共用同一 schema，Web 端的修改 CLI 立即可见，反之亦然。
"""
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import yaml

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / ".metadata" / "library.db"
CONFIG_PATH = BASE_DIR / ".config.yaml"
CLI_ENTRY = BASE_DIR / ".scripts" / "books.py"
VENV_PYTHON = BASE_DIR / "venv" / "bin" / "python3"
COVERS_DIR = BASE_DIR / ".metadata" / "covers"

ALLOWED_STATUSES = ("unread", "reading", "finished", "reference")
STATUS_LABELS = {
    "unread": "未读",
    "reading": "在读",
    "finished": "读完",
    "reference": "参考",
}


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _row_to_book(row: sqlite3.Row) -> dict:
    book = dict(row)
    try:
        book["tags"] = json.loads(book.get("tags") or "[]")
    except json.JSONDecodeError:
        book["tags"] = []
    book["status_label"] = STATUS_LABELS.get(book["status"], book["status"])
    book["size_mb"] = round((book.get("filesize") or 0) / 1024 / 1024, 1)
    return book


def load_config() -> dict:
    if CONFIG_PATH.exists():
        return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
    return {}


def list_categories() -> list[str]:
    """从配置的分类关键词规则中取分类列表（保持与 CLI 一致）。"""
    cfg = load_config()
    cats = list((cfg.get("category_keywords") or {}).keys())
    default = cfg.get("default_category")
    if default and default not in cats:
        cats.append(default)
    return cats


def query_books(
    keyword: str = "",
    category: str = "",
    status: str = "",
    tag: str = "",
    min_rating: int = 0,
    sort: str = "updated",
    limit: int = 50,
    offset: int = 0,
) -> dict:
    where, params = [], []
    if keyword:
        where.append("(title LIKE ? OR author LIKE ? OR notes LIKE ?)")
        like = f"%{keyword}%"
        params += [like, like, like]
    if category:
        where.append("category = ?")
        params.append(category)
    if status:
        where.append("status = ?")
        params.append(status)
    if tag:
        where.append("tags LIKE ?")
        params.append(f'%"{tag}"%')
    if min_rating:
        where.append("rating >= ?")
        params.append(min_rating)

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    order_sql = {
        "updated": "updated_at DESC",
        "added": "added_at DESC",
        "rating": "rating DESC, updated_at DESC",
        "title": "title COLLATE NOCASE",
    }.get(sort, "updated_at DESC")

    with _conn() as conn:
        total = conn.execute(
            f"SELECT COUNT(*) FROM books {where_sql}", params
        ).fetchone()[0]
        rows = conn.execute(
            f"SELECT * FROM books {where_sql} ORDER BY {order_sql} LIMIT ? OFFSET ?",
            params + [limit, offset],
        ).fetchall()
    return {"total": total, "items": [_row_to_book(r) for r in rows]}


def get_book(book_id: int) -> dict | None:
    with _conn() as conn:
        row = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
    return _row_to_book(row) if row else None


def update_book(book_id: int, fields: dict) -> dict | None:
    """更新允许的元数据字段，返回更新后的书籍。"""
    allowed = {"title", "author", "isbn", "category", "status", "rating", "notes"}
    updates, params = [], []
    for key, value in fields.items():
        if key == "tags":
            updates.append("tags = ?")
            params.append(json.dumps(value, ensure_ascii=False))
        elif key in allowed:
            if key == "status" and value not in ALLOWED_STATUSES:
                raise ValueError(f"非法状态: {value}")
            if key == "rating" and not (0 <= int(value) <= 5):
                raise ValueError("评分需在 0-5 之间")
            updates.append(f"{key} = ?")
            params.append(value)
    if not updates:
        return get_book(book_id)
    updates.append("updated_at = CURRENT_TIMESTAMP")
    with _conn() as conn:
        conn.execute(
            f"UPDATE books SET {', '.join(updates)} WHERE id = ?",
            params + [book_id],
        )
        _sync_tags(conn)
        conn.commit()
    return get_book(book_id)


def delete_book(book_id: int) -> bool:
    with _conn() as conn:
        cur = conn.execute("DELETE FROM books WHERE id = ?", (book_id,))
        _sync_tags(conn)
        conn.commit()
        return cur.rowcount > 0


def _sync_tags(conn: sqlite3.Connection) -> None:
    """重建 tags 汇总表（与 books.tags 保持一致）。"""
    counts: dict[str, int] = {}
    for (tags_json,) in conn.execute("SELECT tags FROM books"):
        try:
            for t in json.loads(tags_json or "[]"):
                counts[t] = counts.get(t, 0) + 1
        except json.JSONDecodeError:
            continue
    conn.execute("DELETE FROM tags")
    conn.executemany(
        "INSERT INTO tags (name, count) VALUES (?, ?)",
        [(name, n) for name, n in sorted(counts.items())],
    )


def list_tags() -> list[dict]:
    with _conn() as conn:
        rows = conn.execute("SELECT name, count FROM tags ORDER BY count DESC").fetchall()
    return [dict(r) for r in rows]


def get_stats() -> dict:
    with _conn() as conn:
        total = conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]
        total_size = conn.execute("SELECT COALESCE(SUM(filesize),0) FROM books").fetchone()[0]
        by_status = dict(
            conn.execute("SELECT status, COUNT(*) FROM books GROUP BY status").fetchall()
        )
        by_category = dict(
            conn.execute("SELECT category, COUNT(*) FROM books GROUP BY category ORDER BY COUNT(*) DESC").fetchall()
        )
        by_rating = dict(
            conn.execute("SELECT rating, COUNT(*) FROM books WHERE rating > 0 GROUP BY rating").fetchall()
        )
        recent = conn.execute(
            "SELECT * FROM books ORDER BY added_at DESC LIMIT 5"
        ).fetchall()

    total_size_mb = round(total_size / 1024 / 1024, 1)
    unread = by_status.get("unread", 0)
    result = {
        "total": total,
        "total_size_mb": total_size_mb,
        "avg_size_mb": round(total_size_mb / total, 1) if total else 0,
        "unread": unread,
        "unread_pct": round(unread / total * 100) if total else 0,
        "category_count": len(by_category),
        "by_status": {STATUS_LABELS.get(k, k): v for k, v in by_status.items()},
        "by_category": by_category,
        "by_rating": {f"{k} 星": v for k, v in sorted(by_rating.items())},
        "recent": [_row_to_book(r) for r in recent],
        "insight": "",
    }
    if by_category and total:
        top_cat, top_count = next(iter(by_category.items()))
        pct = round(top_count / total * 100)
        short = top_cat.split("-", 1)[-1]
        result["insight"] = f"{short}类藏书最多，占全部藏书 {pct}%"
    return result


def get_cover(book: dict) -> Path | None:
    """生成并返回书籍封面缩略图（PDF 首页渲染，按源文件 mtime 缓存）。

    非 PDF 或渲染失败返回 None，由前端展示占位封面。
    """
    src = resolve_file(book)
    if not src or src.suffix.lower() != ".pdf":
        return None
    COVERS_DIR.mkdir(parents=True, exist_ok=True)
    cover = COVERS_DIR / f"{book['id']}.png"
    if cover.exists() and cover.stat().st_mtime >= src.stat().st_mtime:
        return cover
    try:
        import pymupdf

        with pymupdf.open(src) as doc:
            page = doc[0]
            zoom = 300 / page.rect.width
            pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
            pix.save(cover)
        return cover
    except Exception:
        return None


def resolve_file(book: dict) -> Path | None:
    """把数据库中的相对路径解析为绝对路径，并校验不越出项目目录。"""
    path = (BASE_DIR / book["filepath"]).resolve()
    if path.is_file() and str(path).startswith(str(BASE_DIR.resolve())):
        return path
    return None


def read_notes(book: dict) -> str | None:
    """读取伴生笔记（<文件名>.md 或 metadata_file 字段）。"""
    candidates = []
    if book.get("metadata_file"):
        candidates.append(BASE_DIR / book["metadata_file"])
    src = resolve_file(book)
    if src:
        candidates.append(Path(str(src) + ".md"))
    for p in candidates:
        if p.is_file():
            return p.read_text(encoding="utf-8", errors="replace")
    return None


def run_cli(*args: str, confirm: bool = False) -> dict:
    """复用 CLI 的重操作（index / organize），非交互调用。

    confirm=True 时向 stdin 写入 "y"，用于跳过 organize 等命令的确认提示。
    """
    cmd = [str(VENV_PYTHON), str(CLI_ENTRY), *args]
    proc = subprocess.run(
        cmd, cwd=BASE_DIR, capture_output=True, text=True, timeout=600,
        input="y\n" if confirm else None,
    )
    return {
        "ok": proc.returncode == 0,
        "output": (proc.stdout + proc.stderr).strip()[-4000:],
    }
