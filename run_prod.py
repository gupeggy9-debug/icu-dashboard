"""ICU\u9910\u5385\u4f1a\u5458\u770b\u677f \u2014 \u751f\u4ea7\u73af\u5883\u542f\u52a8\u811a\u672c."""
import os
from app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
