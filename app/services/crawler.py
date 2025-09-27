import time
import traceback
import threading
from datetime import datetime
from functools import wraps
import pytz
import signal
from typing import List, Dict, Any, Optional, Callable

from app.services import crawler_factory, _scheduler
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
            cache_key = f"crawler:{crawler_name}:{date_str}"
            cache.set_cache(key=cache_key, value=news_list, expire=0)
            
            log.info(f"{crawler_name} fetch success, {len(news_list)} news fetched")
            return news_list
        else:
            log.info(f"{'Second time ' if is_retry else ''}crawler {crawler_name} failed. 0 news fetched")
            return []
    except Exception as e:
        log.error(f"{'Second time ' if is_retry else ''}crawler {crawler_name} error: {traceback.format_exc()}")
        return []

def run_data_analysis(date_str: str):
    """执行数据分析并缓存结果"""
    log.info(f"Starting data analysis for date {date_str}")
    try:
        # 导入分析模块（在这里导入避免循环依赖）
        from app.analysis.trend_analyzer import TrendAnalyzer
        from app.analysis.predictor import TrendPredictor
        
        # 创建分析器实例
        analyzer = TrendAnalyzer()
        predictor = TrendPredictor()
        
        # 1. 生成关键词云图数据并缓存
        log.info("Generating keyword cloud data...")
        analyzer.get_keyword_cloud(date_str, refresh=True)
        
        # 2. 生成热点聚合分析数据并缓存
        log.info("Generating trend analysis data...")
        analyzer.get_analysis(date_str, analysis_type="main")
        
        # 3. 生成跨平台热点分析数据并缓存
        log.info("Generating cross-platform analysis data...")
        analyzer.get_cross_platform_analysis(date_str, refresh=True)
        
        # 4. 生成热点趋势预测数据并缓存
        log.info("Generating trend prediction data...")
        predictor.get_prediction(date_str)
        
        # 5. 生成平台对比分析数据并缓存
        log.info("Generating platform comparison data...")
        analyzer.get_platform_comparison(date_str)
        
        # 6. 生成高级分析数据并缓存
        log.info("Generating advanced analysis data...")
        analyzer.get_advanced_analysis(date_str, refresh=True)
        
        # 7. 生成数据可视化分析数据并缓存
        log.info("Generating data visualization analysis...")
        analyzer.get_data_visualization(date_str, refresh=True)
        
        # 8. 生成趋势预测分析数据并缓存
        log.info("Generating trend forecast data...")
        analyzer.get_trend_forecast(date_str, refresh=True)
        
        log.info(f"All data analysis completed for date {date_str}")
    except Exception as e:
        log.error(f"Error during data analysis: {str(e)}")
        log.error(traceback.format_exc())

@_scheduler.scheduled_job('interval', id='crawlers_logic', seconds=CRAWLER_INTERVAL, 
                         max_instances=crawler_config.max_instances, 
                         misfire_grace_time=crawler_config.misfire_grace_time)
def crawlers_logic():
    """爬虫主逻辑，包含超时保护和错误处理"""
    
    @timeout_handler
    def crawler_work():
        now_time = datetime.now(SHANGHAI_TZ)
        date_str = now_time.strftime("%Y-%m-%d")
        log.info(f"Starting crawler job at {now_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        retry_crawler = []
        success_count = 0
        
        for crawler_name, crawler in crawler_factory.items():
            news_list = safe_fetch(crawler_name, crawler, date_str)
            if news_list:
                success_count += 1
            else:
                retry_crawler.append(crawler_name)
        
        # 第二轮爬取（重试失败的爬虫）
        if retry_crawler:
            log.info(f"Retrying {len(retry_crawler)} failed crawlers")
            for crawler_name in retry_crawler:
                safe_fetch(crawler_name, crawler_factory[crawler_name], date_str, is_retry=True)
        
        # 记录完成时间
        end_time = datetime.now(SHANGHAI_TZ)
        duration = (end_time - now_time).total_seconds()
        log.info(f"Crawler job finished at {end_time.strftime('%Y-%m-%d %H:%M:%S')}, "
                 f"duration: {duration:.2f}s, success: {success_count}/{len(crawler_factory)}")
        
        # 爬取完成后执行数据分析
        log.info("Crawler job completed, starting data analysis...")
        # 使用新线程执行分析，避免阻塞主线程
        threading.Thread(target=run_data_analysis, args=(date_str,), daemon=True).start()
        
        return success_count
    
    try:
        return crawler_work()
    except CrawlerTimeoutError:
        log.error("Crawler job timed out and was terminated")
    except Exception as e:
        log.error(f"Crawler job failed with error: {str(e)}")
        log.error(traceback.format_exc())
