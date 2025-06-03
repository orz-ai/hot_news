from fastapi import APIRouter, Query
from typing import Optional
from datetime import datetime

import pytz

from app.analysis.trend_analyzer import TrendAnalyzer
from app.analysis.predictor import TrendPredictor
from app.utils.logger import log
from app.core import cache

router = APIRouter()

@router.get("/trend")
async def get_trend_analysis(date: Optional[str] = None, type: str = "main"):
    """
    获取热点聚合分析
    
    分析各平台热点数据的共性和差异，提取共同关键词、跨平台热点话题等
    
    - **date**: 可选，指定日期，格式为YYYY-MM-DD，默认为当天
    - **type**: 分析类型，可选值为 main(主题分析), platform(平台对比), cross(跨平台热点), advanced(高级分析)，默认为main
    """
    try:
        if not date:
            date = datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d")
        
        # 从缓存中获取数据
        cache_key = f"analysis:trend:{date}:{type}"
        cached_data = cache.get_cache(cache_key)
        
        if cached_data:
            log.info(f"Retrieved trend analysis from cache for {date}, type: {type}")
            return cached_data
        
        # 如果缓存中没有，则生成新的分析数据
        analyzer = TrendAnalyzer()
        result = analyzer.get_analysis(date, type)
        return result
    except Exception as e:
        log.error(f"Error in trend analysis: {e}")
        return {
            "status": "error",
            "message": str(e),
            "date": date or datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d")
        }

@router.get("/platform-comparison")
async def get_platform_comparison(date: Optional[str] = None):
    """
    获取平台对比分析
    
    分析各平台热点数据的特点、热度排行、更新频率等，比较不同平台间的异同
    
    - **date**: 可选，指定日期，格式为YYYY-MM-DD，默认为当天
    """
    try:
        if not date:
            date = datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d")
        
        # 从缓存中获取数据
        cache_key = f"analysis:trend:{date}:platform_comparison"
        cached_data = cache.get_cache(cache_key)
        
        if cached_data:
            log.info(f"Retrieved platform comparison from cache for {date}")
            return cached_data
        
        # 如果缓存中没有，则生成新的分析数据
        analyzer = TrendAnalyzer()
        result = analyzer.get_platform_comparison(date)
        return result
    except Exception as e:
        log.error(f"Error in platform comparison: {e}")
        return {
            "status": "error",
            "message": str(e),
            "date": date or datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d")
        }

@router.get("/cross-platform")
async def get_cross_platform_analysis(date: Optional[str] = None, refresh: bool = False):
    """
    获取跨平台热点分析
    
    分析在多个平台上出现的热点话题，以及热点的传播路径
    
    - **date**: 可选，指定日期，格式为YYYY-MM-DD，默认为当天
    - **refresh**: 可选，是否强制刷新缓存，默认为False
    """
    try:
        if not date:
            date = datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d")
        
        # 从缓存中获取数据
        cache_key = f"analysis:trend:{date}:cross_platform"
        
        # 如果不是强制刷新，尝试从缓存获取
        if not refresh:
            cached_data = cache.get_cache(cache_key)
            if cached_data:
                log.info(f"Retrieved cross platform analysis from cache for {date}")
                return cached_data
        
        # 如果缓存中没有或需要刷新，则生成新的分析数据
        analyzer = TrendAnalyzer()
        result = analyzer.get_cross_platform_analysis(date, refresh)
        return result
    except Exception as e:
        log.error(f"Error in cross platform analysis: {e}")
        return {
            "status": "error",
            "message": str(e),
            "date": date or datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d")
        }

@router.get("/advanced")
async def get_advanced_analysis(date: Optional[str] = None, refresh: bool = False):
    """
    获取高级分析
    
    提供更深入的热点分析，包括关键词云图、情感分析、热点演变趋势等
    
    - **date**: 可选，指定日期，格式为YYYY-MM-DD，默认为当天
    - **refresh**: 可选，是否强制刷新缓存，默认为False
    """
    try:
        if not date:
            date = datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d")
        
        # 从缓存中获取数据
        cache_key = f"analysis:trend:{date}:advanced_analysis"
        
        # 如果不是强制刷新，尝试从缓存获取
        if not refresh:
            cached_data = cache.get_cache(cache_key)
            if cached_data:
                log.info(f"Retrieved advanced analysis from cache for {date}")
                return cached_data
        
        # 如果缓存中没有或需要刷新，则生成新的分析数据
        analyzer = TrendAnalyzer()
        result = analyzer.get_advanced_analysis(date, refresh)
        return result
    except Exception as e:
        log.error(f"Error in advanced analysis: {e}")
        return {
            "status": "error",
            "message": str(e),
            "date": date or datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d")
        }

@router.get("/prediction")
async def get_trend_prediction(date: Optional[str] = None):
    """
    获取热点趋势预测
    
    基于历史数据预测热点话题的发展趋势，包括上升趋势、下降趋势、持续热门话题等
    
    - **date**: 可选，指定日期，格式为YYYY-MM-DD，默认为当天
    """
    try:
        if not date:
            date = datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d")
        
        # 从缓存中获取数据
        cache_key = f"analysis:prediction:{date}"
        cached_data = cache.get_cache(cache_key)
        
        if cached_data:
            log.info(f"Retrieved trend prediction from cache for {date}")
            return cached_data
        
        # 如果缓存中没有，则生成新的预测数据
        predictor = TrendPredictor()
        result = predictor.get_prediction(date)
        return result
    except Exception as e:
        log.error(f"Error in trend prediction: {e}")
        return {
            "status": "error",
            "message": str(e),
            "date": date or datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d")
        }

@router.get("/keyword-cloud")
async def get_keyword_cloud(date: Optional[str] = None, refresh: bool = False, platforms: Optional[str] = None, category: Optional[str] = None, keyword_count: int = 200):
    """
    获取关键词云图数据
    
    提取热点数据中的关键词，按不同类别（科技、娱乐、社会等）进行分类，用于生成词云
    
    - **date**: 可选，指定日期，格式为YYYY-MM-DD，默认为当天
    - **refresh**: 可选，是否强制刷新缓存，默认为False
    - **platforms**: 可选，指定平台，多个平台用逗号分隔，如"baidu,weibo"
    - **category**: 可选，指定分类，如"科技"、"娱乐"等
    - **keyword_count**: 可选，返回的关键词数量，默认为200
    """
    try:
        if not date:
            date = datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d")
        
        # 从缓存中获取数据
        cache_key = f"analysis:keyword_cloud:{date}"
        
        # 如果不是强制刷新，尝试从缓存获取
        if not refresh:
            cached_data = cache.get_cache(cache_key)
            if cached_data:
                log.info(f"Retrieved keyword cloud from cache for {date}")
                # 如果指定了分类，过滤结果
                if category and cached_data.get("status") == "success" and "keyword_clouds" in cached_data:
                    if category in cached_data["keyword_clouds"]:
                        filtered_data = cached_data.copy()
                        filtered_data["keyword_clouds"] = {category: cached_data["keyword_clouds"][category]}
                        return filtered_data
                return cached_data
        
        # 如果缓存中没有或需要刷新，则生成新的关键词云数据
        analyzer = TrendAnalyzer()
        result = analyzer.get_keyword_cloud(date, refresh, keyword_count)
        return result
    except Exception as e:
        log.error(f"Error in keyword cloud analysis: {e}")
        return {
            "status": "error",
            "message": str(e),
            "date": date or datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d")
        }

@router.get("/data-visualization")
async def get_data_visualization(date: Optional[str] = None, refresh: bool = False, platforms: str = None):
    """
    获取数据可视化分析
    
    提供热点数据的可视化分析，包括主题热度分布图
    
    - **date**: 可选，指定日期，格式为YYYY-MM-DD，默认为当天
    - **refresh**: 可选，是否强制刷新缓存，默认为False
    - **platforms**: 可选，指定要分析的平台，多个平台用逗号分隔，例如：baidu,weibo,douyin
    """
    try:
        if not date:
            date = datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d")
        
        # 从缓存中获取数据
        cache_key = f"analysis:data_visualization:{date}"
        
        # 如果不是强制刷新，尝试从缓存获取
        if not refresh:
            cached_data = cache.get_cache(cache_key)
            if cached_data:
                log.info(f"Retrieved data visualization from cache for {date}")
                return cached_data
        
        # 解析平台参数
        platform_list = None
        if platforms:
            platform_list = [p.strip() for p in platforms.split(",") if p.strip()]
            
        # 如果缓存中没有或需要刷新，则生成新的可视化数据
        analyzer = TrendAnalyzer()
        result = analyzer.get_data_visualization(date, refresh, platform_list)
        return result
    except Exception as e:
        log.error(f"Error in data visualization: {e}")
        return {
            "status": "error",
            "message": str(e),
            "date": date or datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d")
        }

@router.get("/trend-forecast")
async def get_trend_forecast(date: Optional[str] = None, refresh: bool = False, time_range: str = "24h"):
    """
    获取热点趋势预测分析
    
    分析热点话题的演变趋势，预测热点的发展方向
    
    - **date**: 可选，指定日期，格式为YYYY-MM-DD，默认为当天
    - **refresh**: 可选，是否强制刷新缓存，默认为False
    - **time_range**: 可选，预测时间范围，可选值为 24h(24小时), 7d(7天), 30d(30天)，默认为24h
    """
    try:
        if not date:
            date = datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d")
        
        # 验证时间范围参数
        valid_time_ranges = ["24h", "7d", "30d"]
        if time_range not in valid_time_ranges:
            time_range = "24h"  # 默认使用24小时
        
        # 从缓存中获取数据
        cache_key = f"analysis:trend_forecast:{date}:{time_range}"
        
        # 如果不是强制刷新，尝试从缓存获取
        if not refresh:
            cached_data = cache.get_cache(cache_key)
            if cached_data:
                log.info(f"Retrieved trend forecast from cache for {date}, time_range: {time_range}")
                return cached_data
            
        # 如果缓存中没有或需要刷新，则生成新的趋势预测数据
        analyzer = TrendAnalyzer()
        result = analyzer.get_trend_forecast(date, refresh, time_range)
        return result
    except Exception as e:
        log.error(f"Error in trend forecast: {e}")
        return {
            "status": "error",
            "message": str(e),
            "date": date or datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d"),
            "time_range": time_range
        } 