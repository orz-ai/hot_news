import redis
from pydantic import BaseModel

from app.core import cache


def _get(key):
    return cache._get(key)


def _set(key, value, ex=None):
    return cache._set(key, value, ex)


def _del(key):
    return cache._del(key)


def _hset(name, key, value):
    return cache._hset(name, key, value)


def _hget(name, key):
    return cache._hget(name, key)


class CacheNews(BaseModel):
    title: str
    url: str
    score: int
    desc: str