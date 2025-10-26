# app/api/endpoints/dailynews.py
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

import pytz
from fastapi import APIRouter

from app.core import cache
from app.services import crawler_factory
from app.utils.logger import log

router = APIRouter()


@router.get("/")
def get_hot_news(date: str = None, platform: str = None):
    if platform not in crawler_factory.keys():
        return {
            "status": "404",
            "data": [],
            "msg": "`platform` is required, valid platform: " + ", ".join(crawler_factory.keys())
        }

    if not date:
        date = datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d")

    cacheKey = f"crawler:{platform}:{date}"
    result = cache.get(cacheKey)
    if result:
        return {
            "status": "200",
            "data": json.loads(result),
            "msg": "success"
        }

    return {
        "status": "200",
        "data": [],
        "msg": "success"
    }


@router.get("/all")
def get_all_platforms_news(date: str = None):
    """
    获取所有平台的热门新闻
    
    Args:
        date: 日期，格式为YYYY-MM-DD，默认为当天
    
    Returns:
        包含所有平台新闻的字典，键为平台名称，值为新闻列表
    """
    if not date:
        date = datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d")
    
    all_news = {}
    
    for platform in crawler_factory.keys():
        cacheKey = f"crawler:{platform}:{date}"
        result = cache.get(cacheKey)
        if result:
            try:
                all_news[platform] = json.loads(result)
            except Exception as e:
                log.error(f"Error parsing cached data for {platform}: {e}")
                all_news[platform] = []
        else:
            all_news[platform] = []
    
    return {
        "status": "200",
        "data": all_news,
        "msg": "success"
    }


@router.get("/multi")
def get_multi_platforms_news(date: str = None, platforms: str = None):
    """
    获取多个平台的热门新闻
    
    Args:
        date: 日期，格式为YYYY-MM-DD，默认为当天
        platforms: 平台列表，以逗号分隔，例如 "weibo,baidu,zhihu"
    
    Returns:
        包含指定平台新闻的字典，键为平台名称，值为新闻列表
    """
    if not date:
        date = datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d")
    
    if not platforms:
        return {
            "status": "404",
            "data": {},
            "msg": "`platforms` parameter is required, format: comma-separated platform names"
        }
    
    platform_list = [p.strip() for p in platforms.split(",")]
    valid_platforms = crawler_factory.keys()
    
    # 验证平台是否有效
    invalid_platforms = [p for p in platform_list if p not in valid_platforms]
    if invalid_platforms:
        return {
            "status": "404",
            "data": {},
            "msg": f"Invalid platforms: {', '.join(invalid_platforms)}. Valid platforms: {', '.join(valid_platforms)}"
        }
    
    multi_news = {}
    
    for platform in platform_list:
        cacheKey = f"crawler:{platform}:{date}"
        result = cache.get(cacheKey)
        if result:
            try:
                multi_news[platform] = json.loads(result)
            except Exception as e:
                log.error(f"Error parsing cached data for {platform}: {e}")
                multi_news[platform] = []
        else:
            multi_news[platform] = []
    
    return {
        "status": "200",
        "data": multi_news,
        "msg": "success"
    }


@router.get("/search")
def search_news(keyword: str, date: str = None, platforms: str = None, limit: int = 20):
    """
    搜索新闻
    
    Args:
        keyword: 搜索关键词
        date: 日期，格式为YYYY-MM-DD，默认为当天
        platforms: 平台列表，以逗号分隔，例如 "weibo,baidu,zhihu"，默认搜索所有平台
        limit: 返回结果数量限制，默认为20
    
    Returns:
        包含搜索结果的字典，键为状态码、数据、消息、总结果数量和搜索结果数量
    """
    if not date:
        date = datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d")
    
    # 确定要搜索的平台
    if platforms:
        platform_list = [p.strip() for p in platforms.split(",")]
        valid_platforms = crawler_factory.keys()
        platform_list = [p for p in platform_list if p in valid_platforms]
    else:
        platform_list = list(crawler_factory.keys())
    
    if not platform_list:
        return {
            "status": "404",
            "data": [],
            "msg": "No valid platforms specified",
            "total": 0,
            "search_results": 0
        }
    
    # 从各平台获取新闻数据
    all_news = []
    
    for platform in platform_list:
        cacheKey = f"crawler:{platform}:{date}"
        result = cache.get(cacheKey)
        if not result:
            continue
        
        try:
            platform_news = json.loads(result)
            if not isinstance(platform_news, list):
                continue
            
            # 为每条新闻添加平台信息
            for idx, item in enumerate(platform_news):
                if not isinstance(item, dict):
                    continue
                
                # 处理rank字段
                rank_value = ""
                if "rank" in item and item["rank"]:
                    rank_value = str(item["rank"]).replace("#", "")
                elif "index" in item and item["index"]:
                    rank_value = str(item["index"]).replace("#", "")
                else:
                    rank_value = str(idx + 1)
                
                # 获取分类信息
                category = _get_category_for_platform(platform)
                sub_category = _get_subcategory_for_platform(platform)
                
                # 构建标准化的新闻条目
                item_with_source = {
                    "id": item.get("id"),
                    "title": item.get("title", ""),
                    "source": platform,
                    "rank": rank_value,
                    "category": category,
                    "sub_category": sub_category,
                    "url": item.get("url", "")
                }
                all_news.append(item_with_source)
                
        except Exception as e:
            log.error(f"Error processing news from {platform}: {e}")
    
    # 搜索关键词
    search_results = []
    for item in all_news:
        if keyword.lower() in item["title"].lower():
            search_results.append(item)
    
    # 按站点分组，每个站点内按排名排序
    grouped_results = {}
    for item in search_results:
        source = item["source"]
        if source not in grouped_results:
            grouped_results[source] = []
        grouped_results[source].append(item)
    
    # 对每个站点内的结果按排名排序
    for source, items in grouped_results.items():
        # 按排名排序（直接比较数字）
        items.sort(key=lambda x: int(x["rank"]) if x["rank"].isdigit() else 999)
    
    # 重新组合排序后的结果
    sorted_results = []
    for source, items in grouped_results.items():
        sorted_results.extend(items)
    
    # 限制返回结果数量
    limited_results = sorted_results[:limit]
    
    return {
        "status": "200",
        "data": limited_results,
        "msg": "success",
        "total": len(search_results),
        "search_results": len(limited_results)
    }


def _get_category_for_platform(platform: str) -> str:
    """根据平台返回对应的分类"""
    categories = {
        "36kr": "科技创业",
        "hupu": "体育",
        "sspai": "科技",
        "weibo": "社交",
        "zhihu": "知识",
        "baidu": "综合",
        "tieba": "社区",
        "douban": "文化",
        "bilibili": "视频",
        "v2ex": "科技",
        "github": "开发者",
        "hackernews": "科技",
        "stackoverflow": "开发者",
        "jinritoutiao": "资讯",
        "douyin": "娱乐",
        "shaoshupai": "科技"
    }
    return categories.get(platform, "其他")


def _get_subcategory_for_platform(platform: str) -> str:
    """根据平台返回对应的子分类"""
    subcategories = {
        "36kr": "商业资讯",
        "hupu": "娱乐",
        "sspai": "数码",
        "weibo": "热门",
        "zhihu": "问答",
        "baidu": "热搜",
        "tieba": "讨论",
        "douban": "影视",
        "bilibili": "热门",
        "v2ex": "技术",
        "github": "开源",
        "hackernews": "国际",
        "stackoverflow": "问答",
        "jinritoutiao": "热点",
        "douyin": "娱乐",
        "shaoshupai": "数码"
    }
    return subcategories.get(platform, "其他")

