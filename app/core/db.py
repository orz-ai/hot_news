import time
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
import traceback

import pymysql
from pymysql.cursors import DictCursor

from app.utils.logger import log
from app.core.config import get_db_config

# 连接池
_connection = None

def init_db():
    """初始化数据库连接"""
    global _connection
    try:
        db_config = get_db_config()
        _connection = pymysql.connect(
            host=db_config.host,
            user=db_config.user,
            password=db_config.password,
            db=db_config.db,
            charset=db_config.charset,
            cursorclass=DictCursor,
            autocommit=db_config.autocommit
        )
        log.info("Database connection established")
    except Exception as e:
        log.error(f"Failed to connect to database: {e}")
        raise

def close_db():
    """关闭数据库连接"""
    global _connection
    if _connection:
        _connection.close()
        _connection = None
        log.info("Database connection closed")

@contextmanager
def get_cursor():
    """获取数据库游标的上下文管理器"""
    global _connection
    
    # 如果连接不存在或已关闭，重新连接
    if _connection is None or not _connection.open:
        init_db()
    
    cursor = None
    try:
        cursor = _connection.cursor()
        yield cursor
    except pymysql.OperationalError as e:
        # 处理连接断开的情况
        if e.args[0] in (2006, 2013):  # MySQL server has gone away, Lost connection
            log.warning("Database connection lost, reconnecting...")
            init_db()
            cursor = _connection.cursor()
            yield cursor
        else:
            raise
    except Exception as e:
        log.error(f"Database error: {e}")
        raise
    finally:
        if cursor:
            cursor.close()

def insert_news(news_list: List[Dict[str, Any]]) -> int:
    """插入新闻数据，返回成功插入的数量"""
    if not news_list:
        return 0
    
    inserted_count = 0
    start_time = time.time()
    
    try:
        with get_cursor() as cursor:
            for news in news_list:
                # 检查是否已存在
                cursor.execute(
                    "SELECT id FROM news WHERE url = %s LIMIT 1",
                    (news.get('url', ''),)
                )
                if cursor.fetchone():
                    continue
                
                # 插入新数据
                cursor.execute(
                    """
                    INSERT INTO news (title, content, url, source, publish_time, created_at)
                    VALUES (%s, %s, %s, %s, %s, NOW())
                    """,
                    (
                        news.get('title', ''),
                        news.get('content', ''),
                        news.get('url', ''),
                        news.get('source', ''),
                        news.get('publish_time', None),
                    )
                )
                inserted_count += 1
        
        duration = time.time() - start_time
        log.info(f"Inserted {inserted_count}/{len(news_list)} news items in {duration:.2f}s")
        return inserted_count
    
    except Exception as e:
        log.error(f"Error inserting news: {e}")
        log.error(traceback.format_exc())
        return 0

def get_news_by_date(date_str: str, limit: int = 100) -> List[Dict[str, Any]]:
    """获取指定日期的新闻"""
    try:
        with get_cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM news 
                WHERE DATE(publish_time) = %s
                ORDER BY publish_time DESC
                LIMIT %s
                """,
                (date_str, limit)
            )
            return cursor.fetchall()
    except Exception as e:
        log.error(f"Error getting news by date: {e}")
        return []
