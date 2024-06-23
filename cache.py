import redis
from pydantic import BaseModel
from datetime import datetime

redis_client = redis.StrictRedis(host='localhost', port=6379, db=0, password="")


def _get(key):
    return redis_client.get(key).decode("utf-8")


def _set(key, value, ex=None):
    return redis_client.set(key, value, ex=ex)


def _del(key):
    return redis_client.delete(key)


def _hset(name, key, value):
    return redis_client.hset(name, key, value)


def _hget(name, key):
    return redis_client.hget(name, key)


class CacheNews(BaseModel):
    title: str
    url: str
    score: int
    desc: str
