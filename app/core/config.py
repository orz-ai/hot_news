import os
import yaml
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

# 配置文件路径
CONFIG_PATH = os.environ.get("CONFIG_PATH", "config/config.yaml")

# 配置模型
class AppConfig(BaseModel):
    title: str
    description: str
    version: str
    host: str
    port: int
    debug: bool = True
    cors: Dict[str, Any]

class DatabaseConfig(BaseModel):
    host: str
    user: str
    password: str
    db: str
    charset: str
    autocommit: bool = True

class RedisConfig(BaseModel):
    host: str
    port: int
    db: int
    password: str = ""
    decode_responses: bool = False
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    health_check_interval: int = 30

class CrawlerConfig(BaseModel):
    interval: int
    timeout: int
    max_retry_count: int
    max_instances: int
    misfire_grace_time: int

class LoggingConfig(BaseModel):
    level: str
    format: str
    dir: str
    file: str
    max_size: int
    backup_count: int
    daily_backup_count: int
    timezone: str

class SchedulerConfig(BaseModel):
    thread_pool_size: int
    process_pool_size: int
    coalesce: bool
    max_instances: int
    misfire_grace_time: int
    timezone: str

class Config(BaseModel):
    app: AppConfig
    database: DatabaseConfig
    redis: RedisConfig
    crawler: CrawlerConfig
    logging: LoggingConfig
    scheduler: SchedulerConfig

# 全局配置对象
_config: Optional[Config] = None

def load_config() -> Config:
    """加载配置文件"""
    global _config
    if _config is None:
        try:
            with open(CONFIG_PATH, 'r') as f:
                config_data = yaml.safe_load(f)
                _config = Config(**config_data)
        except Exception as e:
            raise RuntimeError(f"Failed to load configuration: {e}")
    return _config

def get_config() -> Config:
    """获取配置对象"""
    if _config is None:
        return load_config()
    return _config

# 便捷访问函数
def get_app_config() -> AppConfig:
    return get_config().app

def get_db_config() -> DatabaseConfig:
    return get_config().database

def get_redis_config() -> RedisConfig:
    return get_config().redis

def get_crawler_config() -> CrawlerConfig:
    return get_config().crawler

def get_logging_config() -> LoggingConfig:
    return get_config().logging

def get_scheduler_config() -> SchedulerConfig:
    return get_config().scheduler
