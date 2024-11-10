# app/api/endpoints/dailynews.py
import json
from datetime import datetime

import pytz
from fastapi import APIRouter

from app.core import cache
from app.services import factory

router = APIRouter()


@router.get("/")
def get_hot_news(date: str = None, platform: str = None):
    if platform not in factory.keys():
        return {
            "status": "404",
            "data": [],
            "msg": "`platform` is required, valid platform: " + ", ".join(factory.keys())
        }

    if not date:
        date = datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d")

    result = cache._hget(date, platform)
    if result:
        return {
            "status": "200",
            "data": json.loads(result.decode("utf-8")),
            "msg": "success"
        }

    return {
        "status": "200",
        "data": [],
        "msg": "success"
    }

