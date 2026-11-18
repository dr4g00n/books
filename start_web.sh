#!/usr/bin/env bash
# Books Web 启动脚本
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${1:-8321}"

cd "$SCRIPT_DIR"
echo "📚 Books Web 启动中: http://127.0.0.1:${PORT}"
echo "   API 文档:          http://127.0.0.1:${PORT}/docs"
exec "$SCRIPT_DIR/venv/bin/python3" -m uvicorn web.app:app \
    --host 127.0.0.1 --port "$PORT" "$@"
