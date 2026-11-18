"""
Books Web 管理入口。

启动方式:
    ./start_web.sh            # 或
    venv/bin/python3 -m uvicorn web.app:app --port 8321

页面路由渲染 HTML，数据全部走 /api/v1 REST 接口。
"""
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .api import router as api_router
from . import services

WEB_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="Books Web",
    description="个人书库网页管理系统（与 Books CLI 共用数据库）",
    version="1.0.0",
)

app.mount("/static", StaticFiles(directory=WEB_DIR / "static"), name="static")
app.include_router(api_router)

templates = Jinja2Templates(directory=WEB_DIR / "templates")
templates.env.globals["status_labels"] = services.STATUS_LABELS


def _static_version() -> int:
    """静态资源版本号：取 CSS/JS 最新 mtime，文件变更后浏览器自动弃用旧缓存。"""
    return int(max(
        (WEB_DIR / "static" / f).stat().st_mtime
        for f in ("style.css", "app.js")
    ))


templates.env.globals["v"] = _static_version()


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html",
        {"stats": services.get_stats(), "page": "dashboard"},
    )


@app.get("/library", response_class=HTMLResponse)
def library(request: Request):
    return templates.TemplateResponse(
        request,
        "library.html",
        {
            "page": "library",
            "categories": services.list_categories(),
            "tags": services.list_tags(),
        },
    )


@app.get("/books/{book_id}", response_class=HTMLResponse)
def book_detail(request: Request, book_id: int):
    book = services.get_book(book_id)
    if not book:
        return templates.TemplateResponse(
            request, "404.html", {"book_id": book_id}, status_code=404
        )
    return templates.TemplateResponse(
        request,
        "detail.html",
        {
            "page": "library",
            "book": book,
            "categories": services.list_categories(),
            "status_labels": services.STATUS_LABELS,
        },
    )
