# Books Web 管理系统 — 任务计划

## 目标

在现有 Books CLI 基础上建立网页版管理系统，复用同一 SQLite 数据库，REST API 优先设计，支持未来扩展。

## 架构决策

- **后端**：FastAPI + Uvicorn（装入现有 venv），自动 OpenAPI 文档（/docs）
- **前端**：服务端渲染（Jinja2）+ 原生 JS fetch，纯 CSS 无外部 CDN（本机离线可用）
- **数据**：直接读写 `.metadata/library.db`（同一 schema，不动 CLI 数据）
- **重操作复用**：reindex / organize 通过 subprocess 调 CLI，不重写索引逻辑
- **扩展点**：版本化 API（/api/v1/）、模块化 router、配置集中

## 任务清单

- [x] 1. 安装依赖（fastapi/uvicorn/jinja2/python-multipart/markdown）
- [x] 2. web/services.py — 数据访问层（书籍 CRUD、统计、标签、笔记）
- [x] 3. web/api.py — REST API v1 路由
- [x] 4. web/app.py — FastAPI 入口 + 页面路由
- [x] 5. 模板：base / index（仪表盘）/ library（书库）/ detail（详情编辑）
- [x] 6. 静态资源：style.css / app.js
- [x] 7. start_web.sh 启动脚本
- [x] 8. 验证：启动服务，测试 API 与页面，确认数据一致
- [x] 9. 更新 README 说明

## 功能范围（v1）

仪表盘统计、书库搜索/筛选（关键词/分类/状态/评分/标签）、详情页元数据编辑、
伴生 .md 笔记渲染、浏览器内打开/下载 PDF、上传到 swap、一键重建索引。

非目标（留给未来）：在线 EPUB 阅读器、多用户/鉴权、远程访问部署、移动端 App。

## 验证

- API：curl 各端点检查响应
- 页面：确认渲染与交互
- 一致性：Web 端编辑后 CLI query 能看到同样结果

## 回顾

**完成时间**：2026-11-17

**验证结果**（全部通过）：
- 页面：`/`（仪表盘）、`/library`（书库）、`/books/{id}`（详情）、404 页均正常渲染
- API：stats / books 列表与筛选 / PATCH 编辑 / DELETE / notes / file（PDF inline 预览）/ upload / tags / categories / reindex 全部实测通过
- 一致性：Web 端 PATCH 修改评分/状态/标签后，CLI `query` 立即读到相同结果（共用 SQLite）
- 测试数据已还原

**踩过的坑**：
1. venv 是项目搬迁前的旧路径 shebang，`pip` 直接执行报 bad interpreter —— 用 `venv/bin/python3 -m pip` 绕过
2. 新版 Starlette 移除了 `TemplateResponse(name, context)` 旧签名，必须 `TemplateResponse(request, name, context)` —— 导致三个页面 500，改签名后恢复

**后续扩展方向**（架构已预留）：
- 新页面/能力 = 在 `web/api.py` 加路由 + `templates/` 加模板
- 移动端/其他前端直接消费 `/api/v1`，无需改后端
- 远程访问：uvicorn 绑定 0.0.0.0 + 前置反向代理加鉴权即可
