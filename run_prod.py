"""ICU餐厅会员看板 — 生产环境启动脚本."""
import os
from app import app

# 生产环境从环境变量读取 secret key
app.secret_key = os.environ.get("SECRET_KEY", app.secret_key)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"ICU餐厅会员看板 生产环境启动 → http://0.0.0.0:{port}")

    # 优先用 gunicorn (Linux/Render)，否则用 waitress
    try:
        from waitress import serve
        serve(app, host="0.0.0.0", port=port, threads=12)
    except ImportError:
        app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
