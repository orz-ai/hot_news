import time
import traceback
import threading
from datetime import datetime
from functools import wraps
import pytz
import signal
from typing import List, Dict, Any, Optional, Callable

from app.services import factory, _scheduler
from app.utils.logger import log
from app.core import db, cache
from app.core.config import get_crawler_config

# 获取爬虫配置
crawler_config = get_crawler_config()

# 配置常量
CRAWLER_INTERVAL = crawler_config.interval
CRAWLER_TIMEOUT = crawler_config.timeout
MAX_RETRY_COUNT = crawler_config.max_retry_count
SHANGHAI_TZ = pytz.timezone('Asia/Shanghai')

class CrawlerTimeoutError(Exception):
    """爬虫超时异常"""
    pass

def timeout_handler(func: Callable, timeout: int = CRAWLER_TIMEOUT) -> Callable:
    """超时处理装饰器，支持Unix信号和线程两种实现"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # 线程实现的超时机制
        result = [None]
        exception = [None]
        completed = [False]
        
        def target():
            try:
                result[0] = func(*args, **kwargs)
            except Exception as e:
                exception[0] = e
            finally:
                completed[0] = True
        
        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        thread.join(timeout)
        
        if not completed[0]:
            error_msg = f"Function {func.__name__} timed out after {timeout} seconds"
            log.error(error_msg)
            raise CrawlerTimeoutError(error_msg)
        
        if exception[0]:
            log.error(f"Function {func.__name__} raised an exception: {exception[0]}")
            raise exception[0]
                
        return result[0]
    return wrapper

def safe_fetch(crawler_name: str, crawler, date_str: str, is_retry: bool = False) -> List[Dict[str, Any]]:
    """安全地执行爬虫抓取，处理异常并返回结果"""
    try:
        news_list = crawler.fetch(date_str)
        if news_list and len(news_list) > 0:
            # 缓存成功的结果
            cache_key = f"crawler:{crawler_name}:{date_str}"
            cache.set_cache(cache_key, news_list, expire=86400)  # 缓存一天
            
            # 保存到数据库
            db.insert_news(news_list)
            
            log.info(f"{crawler_name} fetch success, {len(news_list)} news fetched")
            return news_list
        else:
            log.info(f"{'Second time ' if is_retry else ''}crawler {crawler_name} failed. 0 news fetched")
            return []
    except Exception as e:
        log.error(f"{'Second time ' if is_retry else ''}crawler {crawler_name} error: {traceback.format_exc()}")
        return []

@_scheduler.scheduled_job('interval', id='crawlers_logic', seconds=CRAWLER_INTERVAL, 
                         max_instances=crawler_config.max_instances, 
                         misfire_grace_time=crawler_config.misfire_grace_time)
def crawlers_logic():
    """爬虫主逻辑，包含超时保护和错误处理"""
    
    @timeout_handler
    def crawler_work():
        # 获取当前上海时间
        now_time = datetime.now(SHANGHAI_TZ)
        date_str = now_time.strftime("%Y-%m-%d")
        log.info(f"Starting crawler job at {now_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 检查是否已经运行过今天的爬虫
        cache_key = f"crawler:run_date:{date_str}"
        if cache.get_cache(cache_key):
            log.info(f"Crawler already ran today ({date_str}), checking for missing data only")
        
        # 第一轮爬取
        retry_crawler = []
        success_count = 0
        
        for crawler_name, crawler in factory.items():
            # 检查缓存，避免重复爬取
            cache_key = f"crawler:{crawler_name}:{date_str}"
            cached_result = cache.get_cache(cache_key)
            
            if cached_result:
                log.info(f"Using cached result for {crawler_name}")
                success_count += 1
                continue
                
            news_list = safe_fetch(crawler_name, crawler, date_str)
            if news_list:
                success_count += 1
            else:
                retry_crawler.append(crawler_name)
        
        # 第二轮爬取（重试失败的爬虫）
        if retry_crawler:
            log.info(f"Retrying {len(retry_crawler)} failed crawlers")
            for crawler_name in retry_crawler:
                safe_fetch(crawler_name, factory[crawler_name], date_str, is_retry=True)
        
        # 记录今天已运行爬虫
        cache.set_cache(f"crawler:run_date:{date_str}", "1", expire=86400)
        
        # 记录完成时间
        end_time = datetime.now(SHANGHAI_TZ)
        duration = (end_time - now_time).total_seconds()
        log.info(f"Crawler job finished at {end_time.strftime('%Y-%m-%d %H:%M:%S')}, "
                 f"duration: {duration:.2f}s, success: {success_count}/{len(factory)}")
        
        return success_count
    
    try:
        return crawler_work()
    except CrawlerTimeoutError:
        log.error("Crawler job timed out and was terminated")
    except Exception as e:
        log.error(f"Crawler job failed with error: {str(e)}")
        log.error(traceback.format_exc())
