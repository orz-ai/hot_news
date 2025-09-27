# app/main.py
import threading
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

import app.services.crawler as crawler
import tg_bot as tg_bot
from app.api.v1 import daily_news, web_tools, analysis
from app.utils.logger import log
from app.core import db, cache
from app.core.config import get_app_config, get_config
from app.services.browser_manager import BrowserManager

# 获取应用配置
app_config = get_app_config()

# 应用启动和关闭的生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    log.info("Application startup")
    
    # 初始化数据库连接
    db.init_db()
    
    # 初始化缓存
    cache.init_cache()
    
    # 异步启动爬虫，避免阻塞应用启动
    threading.Thread(target=crawler.crawlers_logic, daemon=True).start()
    
    yield
    
    # 关闭时执行
    log.info("Application shutdown")
    
    # 关闭浏览器管理器
    try:
        BrowserManager().shutdown()
        log.info("Browser manager shutdown")
    except Exception as e:
        log.error(f"Error shutting down browser manager: {e}")
    
    # 关闭数据库连接
    db.close_db()
    
    # 关闭缓存连接
    cache.close_cache()

# 创建应用实例
app = FastAPI(
    title=app_config.title,
    description=app_config.description,
    version=app_config.version,
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=app_config.cors["allow_origins"],
    allow_credentials=app_config.cors["allow_credentials"],
    allow_methods=app_config.cors["allow_methods"],
    allow_headers=app_config.cors["allow_headers"],
)

# 请求计时中间件
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# 注册路由
app.include_router(daily_news.router, prefix="/api/v1/dailynews", tags=["Daily News"])
app.include_router(web_tools.router, prefix="/api/v1/tools/website-meta", tags=["Website Meta"])
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["Analysis"])

# 健康检查端点
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "version": app_config.version}

# 如果直接运行此文件
if __name__ == "__main__":
    uvicorn.run("app.main:app", host=app_config.host, port=app_config.port, reload=app_config.debug)
