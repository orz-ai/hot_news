import redis
from redis import Redis
from typing import Optional
from pydantic import BaseModel

from app.core import cache
from app.core.config import get_redis_config

# Redis连接配置
REDIS_CONFIG = {
    "host": "localhost",
    "port": 6379,
    "db": 0,
    "decode_responses": False,  # 保持原始字节，由缓存层处理解码
    "socket_timeout": 5,        # 连接超时时间
    "socket_connect_timeout": 5,  # 连接建立超时
    "health_check_interval": 30,  # 定期检查连接健康
}

# 全局Redis连接池
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
    """获取Redis客户端"""
    pool = get_redis_pool()
    return redis.Redis(connection_pool=pool)

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