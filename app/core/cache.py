import redis
from pydantic import BaseModel
import json
from typing import Any, Optional, Dict, List, Union
import time

from app.db.redis import get_redis_client
from app.utils.logger import log

# 默认缓存过期时间（1小时）
DEFAULT_EXPIRE = 3600

def init_cache():
    """初始化缓存连接"""
    try:
        redis = get_redis_client()
        redis.ping()
        log.info("Cache connection established")
    except Exception as e:
        log.error(f"Failed to connect to cache: {e}")

def close_cache():
    """关闭缓存连接"""
    try:
        redis = get_redis_client()
        redis.connection_pool.disconnect()
        log.info("Cache connection closed")
    except Exception as e:
        log.error(f"Error closing cache connection: {e}")

def set_cache(key: str, value: Any, expire: int = DEFAULT_EXPIRE) -> bool:
    """设置缓存，支持自动序列化复杂对象"""
    try:
        redis = get_redis_client()
        if isinstance(value, (dict, list, tuple)):
            value = json.dumps(value)
        elif isinstance(value, bool):
            value = "1" if value else "0"

        if expire > 0:
            redis.setex(key, expire, value)
        else:
            redis.set(key, value)
        return True
    except Exception as e:
        log.error(f"Error setting cache for key111111 {key}: {e}")
        return False

def get_cache(key: str) -> Optional[Any]:
    try:
        redis = get_redis_client()
        value = redis.get(key)
        
        if value is None:
            return None
        
        if isinstance(value, bytes):
            value = value.decode('utf-8')
            
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value
    except Exception as e:
        log.error(f"Error getting cache for key {key}: {e}")
        return None

def delete_cache(key: str) -> bool:
    try:
        redis = get_redis_client()
        redis.delete(key)
        return True
    except Exception as e:
        log.error(f"Error deleting cache for key {key}: {e}")
        return False

def clear_cache_pattern(pattern: str) -> int:
    try:
        redis = get_redis_client()
        keys = redis.keys(pattern)
        if keys:
            return redis.delete(*keys)
        return 0
    except Exception as e:
        log.error(f"Error clearing cache pattern {pattern}: {e}")
        return 0


def _get(key):
    try:
        redis_client = get_redis_client()
    except Exception as e:
        log.error(f"Error getting redis client: {e}")
        return None

    value = redis_client.get(key)
    if value is None:
        return None

    return value.decode("utf-8")


def _set(key, value, ex=None):
    try:
        redis_client = get_redis_client()
    except Exception as e:
        log.error(f"Error getting redis client: {e}")
        return None

    return redis_client.set(key, value, ex=ex)


def _del(key):

    try:
        redis_client = get_redis_client()
    except Exception as e:
        log.error(f"Error getting redis client: {e}")
        return None

    return redis_client.delete(key)


def _hset(name, key, value):

    try:
        redis_client = get_redis_client()
    except Exception as e:
        log.error(f"Error getting redis client: {e}")
        return None

    return redis_client.hset(name, key, value)


def _hget(name, key):

    try:
        redis_client = get_redis_client()
    except Exception as e:
        log.error(f"Error getting redis client: {e}")
        return None

    return redis_client.hget(name, key)


class CacheNews(BaseModel):
    title: str
    url: str
    score: int
    desc: str
