/* Books Web 前端逻辑 —— 原生 JS，数据走 /api/v1 */

const API = "/api/v1";

/* ---------- 通用工具 ---------- */

function toast(msg, isError = false) {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.className = "toast" + (isError ? " error" : "");
  el.hidden = false;
  clearTimeout(el._timer);
  el._timer = setTimeout(() => (el.hidden = true), 3500);
}

async function api(path, options = {}) {
  const resp = await fetch(API + path, options);
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}));
    throw new Error(body.detail || `请求失败 (${resp.status})`);
  }
  return resp.json();
}

function esc(s) {
  const d = document.createElement("div");
  d.textContent = s == null ? "" : String(s);
  return d.innerHTML;
}

/* ---------- 全局：上传 / 重建索引 ---------- */

document.getElementById("btn-upload").addEventListener("click", () => {
  document.getElementById("upload-input").click();
});

document.getElementById("upload-input").addEventListener("change", async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  const fd = new FormData();
  fd.append("file", file);
  toast(`正在上传 ${file.name} …`);
  try {
    const resp = await fetch(API + "/upload", { method: "POST", body: fd });
    if (!resp.ok) throw new Error((await resp.json()).detail || "上传失败");
    toast(`已上传到 swap/，点「重建索引」纳入书库`);
  } catch (err) {
    toast(err.message, true);
  }
  e.target.value = "";
});

document.getElementById("btn-reindex").addEventListener("click", async () => {
  toast("正在重建索引…");
  try {
    const r = await api("/reindex", { method: "POST" });
    if (r.ok) {
      toast("索引完成");
      setTimeout(() => location.reload(), 800);
    } else {
      toast("索引失败：" + r.output, true);
    }
  } catch (err) {
    toast(err.message, true);
  }
});

/* ---------- 书库页 ---------- */

const PAGE_SIZE = 24;
let pageState = { offset: 0, total: 0 };

function readFilters() {
  return {
    keyword: document.getElementById("f-keyword").value.trim(),
    category: document.getElementById("f-category").value,
    status: document.getElementById("f-status").value,
    tag: document.getElementById("f-tag").value,
    min_rating: document.getElementById("f-rating").value,
    sort: document.getElementById("f-sort").value,
  };
}

function bookCard(b) {
  const stars = b.rating > 0 ? "★".repeat(b.rating) : "";
  const tags = (b.tags || [])
    .map((t) => `<span class="tag">${esc(t)}</span>`)
    .join("");
  return `
    <div class="book-card">
      <a class="title" href="/books/${b.id}">${esc(b.title)}</a>
      <div class="meta">${esc(b.author || "佚名")} · ${esc(b.category)} · ${b.size_mb} MB</div>
      <div class="tags">${tags}</div>
      <div class="foot">
        <span class="rating">${stars}</span>
        <span class="badge status-${b.status}">${esc(b.status_label)}</span>
      </div>
    </div>`;
}

async function loadBooks() {
  const f = readFilters();
  const qs = new URLSearchParams({
    ...f,
    limit: PAGE_SIZE,
    offset: pageState.offset,
  });
  const data = await api("/books?" + qs);
  pageState.total = data.total;

  const grid = document.getElementById("book-grid");
  grid.innerHTML =
    data.items.map(bookCard).join("") ||
    '<p class="muted">没有匹配的书籍</p>';

  document.getElementById("result-meta").textContent = `共 ${data.total} 本`;
  const page = Math.floor(pageState.offset / PAGE_SIZE) + 1;
  const pages = Math.max(1, Math.ceil(data.total / PAGE_SIZE));
  document.getElementById("page-info").textContent = `${page} / ${pages}`;
  document.getElementById("btn-prev").disabled = pageState.offset === 0;
  document.getElementById("btn-next").disabled =
    pageState.offset + PAGE_SIZE >= data.total;
}

function initLibrary() {
  // 从 URL 恢复筛选（如从仪表盘分类链接进来）
  const params = new URLSearchParams(location.search);
  if (params.get("category"))
    document.getElementById("f-category").value = params.get("category");
  if (params.get("status"))
    document.getElementById("f-status").value = params.get("status");
  if (params.get("keyword"))
    document.getElementById("f-keyword").value = params.get("keyword");

  let debounce;
  const reload = () => {
    pageState.offset = 0;
    clearTimeout(debounce);
    debounce = setTimeout(() => loadBooks().catch((e) => toast(e.message, true)), 200);
  };
  document.querySelectorAll(".filter-bar input, .filter-bar select")
    .forEach((el) => el.addEventListener("input", reload));

  document.getElementById("btn-prev").addEventListener("click", () => {
    pageState.offset = Math.max(0, pageState.offset - PAGE_SIZE);
    loadBooks();
  });
  document.getElementById("btn-next").addEventListener("click", () => {
    pageState.offset += PAGE_SIZE;
    loadBooks();
  });

  loadBooks().catch((e) => toast(e.message, true));
}

/* ---------- 详情页 ---------- */

function initDetail() {
  const form = document.getElementById("edit-form");
  const bookId = form.dataset.bookId;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(form);
    const payload = {
      title: fd.get("title"),
      author: fd.get("author"),
      isbn: fd.get("isbn"),
      category: fd.get("category"),
      status: fd.get("status"),
      rating: parseInt(fd.get("rating"), 10),
      tags: fd.get("tags")
        .split(/[,，]/)
        .map((t) => t.trim())
        .filter(Boolean),
      notes: fd.get("notes"),
    };
    try {
      await api(`/books/${bookId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      toast("已保存");
    } catch (err) {
      toast(err.message, true);
    }
  });

  document.getElementById("btn-delete").addEventListener("click", async () => {
    if (!confirm("确定删除这条记录？（不会删除磁盘文件）")) return;
    try {
      await api(`/books/${bookId}`, { method: "DELETE" });
      toast("已删除");
      setTimeout(() => (location.href = "/library"), 600);
    } catch (err) {
      toast(err.message, true);
    }
  });

  // 加载伴生笔记
  const notesEl = document.getElementById("notes-view");
  api(`/books/${bookId}/notes`)
    .then((r) => {
      notesEl.innerHTML = r.has_notes
        ? r.html
        : '<p class="muted">没有伴生笔记</p>';
    })
    .catch(() => {
      notesEl.innerHTML = '<p class="muted">笔记加载失败</p>';
    });
}
