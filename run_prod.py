"""ICU餐厅会员看板 — 生产环境启动脚本."""
import os
import sys
from waitress import serve
from app import app

# 生产环境从环境变量读取 secret key
app.secret_key = os.environ.get("SECRET_KEY", app.secret_key)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"ICU餐厅会员看板 生产环境启动 → http://0.0.0.0:{port}")
    # waitress 生产级服务器，支持多并发
    serve(app, host="0.0.0.0", port=port, threads=12)
