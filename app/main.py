# app/main.py
import threading

from fastapi import FastAPI

import app.services.crawler as crawler
import tg_bot as tg_bot
from app.api.v1 import daily_news, web_tools
from app.utils.logger import log

app = FastAPI()

# 注册路由
app.include_router(daily_news.router, prefix="/dailynews", tags=["Daily News"])
app.include_router(web_tools.router, prefix="/tools/website-meta", tags=["Website Meta"])


@app.on_event("startup")
async def startup_event():
    crawler.crawlers_logic()
    log.info("start app")


@app.on_event("shutdown")
async def shutdown_event():
    log.info("close app")
