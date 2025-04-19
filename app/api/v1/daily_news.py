# app/api/endpoints/dailynews.py
import json
from datetime import datetime

import pytz
from fastapi import APIRouter

from app.core import cache
from app.services import crawler_factory
from app.utils.logger import log

router = APIRouter()


@router.get("/")
def get_hot_news(date: str = None, platform: str = None):
    if platform not in crawler_factory.keys():
        return {
            "status": "404",
            "data": [],
            "msg": "`platform` is required, valid platform: " + ", ".join(crawler_factory.keys())
        }

    if not date:
        date = datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d")

    cacheKey = f"crawler:{platform}:{date}"
    result = cache._get(cacheKey)
    if result:
        return {
            "status": "200",
            "data": json.loads(result),
            "msg": "success"
        }

    return {
        "status": "200",
        "data": [],
        "msg": "success"
    }

