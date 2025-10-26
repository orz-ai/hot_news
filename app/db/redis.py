import redis
from redis import Redis
from typing import Optional
from pydantic import BaseModel

from app.core import cache
from app.core.config import get_redis_config

REDIS_CONFIG = {
    "host": "localhost",
    "port": 6379,
    "db": 0,
    "decode_responses": False,
    "socket_timeout": 5,
    "socket_connect_timeout": 5,
    "health_check_interval": 30,
}

_redis_pool = None

def get_redis_pool() -> redis.ConnectionPool:
    global _redis_pool
    if _redis_pool is None:
        redis_config = get_redis_config()
        _redis_pool = redis.ConnectionPool(
            host=redis_config.host,
            port=redis_config.port,
            db=redis_config.db,
            password=redis_config.password,
            decode_responses=redis_config.decode_responses,
            socket_timeout=redis_config.socket_timeout,
            socket_connect_timeout=redis_config.socket_connect_timeout,
            health_check_interval=redis_config.health_check_interval
        )
    return _redis_pool

def get_redis_client() -> Redis:
    pool = get_redis_pool()
    return redis.Redis(connection_pool=pool)

class CacheNews(BaseModel):
    title: str
    url: str
    score: int
    desc: str