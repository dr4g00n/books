"""
REST API v1：所有对外能力的程序化入口。
未来的移动端、小程序、其他前端都通过这套 API 扩展。
"""
from pathlib import Path

import markdown as md_lib
from fastapi import APIRouter, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from . import services

router = APIRouter(prefix="/api/v1")

UPLOAD_EXTS = {".pdf", ".epub", ".mobi", ".djvu", ".pptx", ".ppt"}


class BookUpdate(BaseModel):
    title: str | None = None
    author: str | None = None
    isbn: str | None = None
    category: str | None = None
    status: str | None = None
    rating: int | None = Field(default=None, ge=0, le=5)
    tags: list[str] | None = None
    notes: str | None = None


@router.get("/books")
def list_books(
    keyword: str = "",
    category: str = "",
    status: str = "",
    tag: str = "",
    min_rating: int = Query(default=0, ge=0, le=5),
    sort: str = "updated",
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    return services.query_books(keyword, category, status, tag, min_rating, sort, limit, offset)


@router.get("/books/{book_id}")
def get_book(book_id: int):
    book = services.get_book(book_id)
    if not book:
        raise HTTPException(404, "书籍不存在")
    return book


@router.patch("/books/{book_id}")
def update_book(book_id: int, payload: BookUpdate):
    fields = payload.model_dump(exclude_none=True)
    try:
        book = services.update_book(book_id, fields)
    except ValueError as e:
        raise HTTPException(422, str(e))
    if not book:
        raise HTTPException(404, "书籍不存在")
    return book


@router.delete("/books/{book_id}")
def delete_book(book_id: int):
    if not services.delete_book(book_id):
        raise HTTPException(404, "书籍不存在")
    return {"ok": True}


@router.get("/books/{book_id}/file")
def get_file(book_id: int, download: bool = False):
    book = services.get_book(book_id)
    if not book:
        raise HTTPException(404, "书籍不存在")
    path = services.resolve_file(book)
    if not path:
        raise HTTPException(404, "文件不在磁盘上")
    disposition = "attachment" if download else "inline"
    return FileResponse(
        path,
        filename=path.name,
        content_disposition_type=disposition,
    )


@router.get("/books/{book_id}/cover")
def get_cover(book_id: int):
    """书籍封面缩略图（PDF 首页渲染，带缓存）；无封面时 404，前端用占位图。"""
    book = services.get_book(book_id)
    if not book:
        raise HTTPException(404, "书籍不存在")
    path = services.get_cover(book)
    if not path:
        raise HTTPException(404, "无封面")
    return FileResponse(path)


@router.get("/books/{book_id}/notes")
def get_notes(book_id: int):
    book = services.get_book(book_id)
    if not book:
        raise HTTPException(404, "书籍不存在")
    text = services.read_notes(book)
    if text is None:
        return {"has_notes": False, "html": ""}
    html = md_lib.markdown(text, extensions=["fenced_code", "tables", "toc"])
    return {"has_notes": True, "html": html}


@router.get("/stats")
def get_stats():
    return services.get_stats()


@router.get("/tags")
def get_tags():
    return services.list_tags()


@router.get("/categories")
def get_categories():
    return services.list_categories()


@router.post("/reindex")
def reindex():
    return services.run_cli("index")


@router.post("/organize")
def organize():
    """把 swap/ 暂存区的书籍整理进 library/（自动分类）。"""
    return services.run_cli("organize", confirm=True)


@router.post("/upload")
async def upload(file: UploadFile):
    """上传新书到 swap/ 目录，之后通过 reindex/organize 纳入书库。"""
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in UPLOAD_EXTS:
        raise HTTPException(422, f"不支持的格式 {suffix}，支持: {sorted(UPLOAD_EXTS)}")
    dest_dir = services.BASE_DIR / "swap"
    dest_dir.mkdir(exist_ok=True)
    dest = dest_dir / Path(file.filename).name
    content = await file.read()
    if len(content) > 500 * 1024 * 1024:
        raise HTTPException(413, "文件超过 500MB 限制")
    dest.write_bytes(content)
    return {"ok": True, "path": str(dest.relative_to(services.BASE_DIR)), "size": len(content)}
