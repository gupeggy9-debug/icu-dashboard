"""ICU餐厅会员看板 — 生产环境启动脚本."""
import os
from waitress import serve
from app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"ICU餐厅会员看板 生产环境启动 → 0.0.0.0:{port}")
    serve(app, host="0.0.0.0", port=port, threads=12)
