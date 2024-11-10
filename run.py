# run.py
import uvicorn

from app.main import app

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=18080,
        log_level="info",
        reload=False  # 开发时开启自动重载，生产环境下关闭
    )
