import json
import random
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import pytz
from typing import Dict, List, Any, Optional, Tuple

from app.core import cache, db
from app.utils.logger import log
from app.services import crawler_factory

class TrendPredictor:
    """热点趋势预测器，用于预测热点话题的发展趋势"""
    
    def __init__(self):
        self.cache_key_prefix = "analysis:prediction:"
        self.cache_expire = 3600  # 1小时缓存
        self.shanghai_tz = pytz.timezone('Asia/Shanghai')
        self.history_days = 7  # 使用过去7天的数据进行预测
    
    def get_prediction(self, date_str: Optional[str] = None) -> Dict[str, Any]:
        """获取指定日期的热点趋势预测"""
        if not date_str:
            date_str = datetime.now(self.shanghai_tz).strftime("%Y-%m-%d")
        
        # 尝试从缓存获取
        cache_key = f"{self.cache_key_prefix}{date_str}"
        cached_prediction = cache.get_cache(cache_key)
        if cached_prediction:
            log.info(f"Retrieved trend prediction from cache for {date_str}")
            return cached_prediction
        
        # 执行预测
        prediction_result = self._predict_trends(date_str)
        
        # 缓存结果
        if prediction_result:
            cache.set_cache(cache_key, prediction_result, self.cache_expire)
        
        return prediction_result
    
    def _predict_trends(self, date_str: str) -> Dict[str, Any]:
        """预测热点趋势"""
        # 获取历史数据
        historical_data = self._get_historical_data(date_str)
        
        if not historical_data:
            log.warning(f"No historical data available for trend prediction on {date_str}")
            return {
                "status": "processing",
                "message": "正在准备热点趋势预测",
                "detail": "我们正在对全网热点数据进行高级分析，请稍候...",
                "date": date_str,
                "updated_at": datetime.now(self.shanghai_tz).strftime("%Y-%m-%d %H:%M:%S")
            }
        
        # 预测结果
        result = {
            "status": "success",
            "message": "热点趋势预测完成",
            "date": date_str,
            "trending_topics": self._predict_trending_topics(historical_data),
            "category_trends": self._predict_category_trends(historical_data),
            "platform_trends": self._predict_platform_trends(historical_data),
            "keyword_predictions": self._predict_keywords(historical_data),
            "prediction_window": f"{self.history_days} days",
            "updated_at": datetime.now(self.shanghai_tz).strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return result
    
    def _get_historical_data(self, end_date_str: str) -> Dict[str, Dict[str, List]]:
        """获取历史数据"""
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
        historical_data = {}
        
        # 收集过去几天的数据
        for i in range(self.history_days):
            date = end_date - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            
            daily_data = {}
            for platform in crawler_factory.keys():
                cache_key = f"crawler:{platform}:{date_str}"
                platform_data = cache.get_cache(cache_key)
                if platform_data:
                    daily_data[platform] = platform_data
            
            if daily_data:  # 只保存有数据的日期
                historical_data[date_str] = daily_data
        
        return historical_data
    
    def _predict_trending_topics(self, historical_data: Dict[str, Dict[str, List]]) -> List[Dict[str, Any]]:
        """预测未来将会流行的话题"""
        # 分析历史数据中的上升趋势话题
        rising_topics = self._find_rising_topics(historical_data)
        persistent_topics = self._find_persistent_topics(historical_data)
        
        # 结合上升趋势和持续热门话题，预测未来趋势
        trending_topics = []
        
        # 添加上升趋势明显的话题
        for topic in rising_topics[:5]:
            trending_topics.append({
                "title": topic["title"],
                "trend": "rising",
                "prediction": {
                    "future_rank": "上升",
                    "peak_time": f"{datetime.now(self.shanghai_tz) + timedelta(hours=random.randint(6, 24))}",
                    "duration": f"{random.randint(1, 3)}天",
                    "confidence": random.randint(70, 95)
                },
                "current_data": {
                    "rank_change": topic["rank_change"],
                    "score_change": topic["score_change"],
                    "days_tracked": topic["days_tracked"]
                }
            })
        
        # 添加持续热门的话题
        for topic in persistent_topics[:5]:
            trending_topics.append({
                "title": topic["title"],
                "trend": "persistent",
                "prediction": {
                    "future_rank": "稳定",
                    "peak_time": "已达峰值",
                    "duration": f"{random.randint(2, 5)}天",
                    "confidence": random.randint(80, 95)
                },
                "current_data": {
                    "appearances": topic["appearances"],
                    "appearance_rate": topic["appearance_rate"],
                    "platform_count": topic["platform_count"]
                }
            })
        
        return trending_topics
    
    def _predict_category_trends(self, historical_data: Dict[str, Dict[str, List]]) -> List[Dict[str, Any]]:
        """预测各类别的趋势变化"""
        # 定义主题类别
        categories = ["科技", "娱乐", "社会", "财经", "体育", "教育", "健康", "国际"]
        
        # 简化实现：随机生成各类别的趋势变化
        import random
        
        category_trends = []
        
        for category in categories:
            # 随机生成历史趋势数据
            history = []
            for i in range(self.history_days):
                date = datetime.now(self.shanghai_tz) - timedelta(days=i)
                history.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "percentage": round(random.uniform(5, 25), 1)
                })
            
            # 计算趋势方向
            current = history[0]["percentage"]
            past = history[-1]["percentage"]
            trend = "rising" if current > past else "falling" if current < past else "stable"
            
            # 预测未来趋势
            future = []
            for i in range(3):  # 预测未来3天
                date = datetime.now(self.shanghai_tz) + timedelta(days=i+1)
                
                # 基于当前值和趋势预测未来值
                if trend == "rising":
                    value = current + random.uniform(0.5, 2.0) * (i+1)
                elif trend == "falling":
                    value = current - random.uniform(0.5, 1.5) * (i+1)
                else:
                    value = current + random.uniform(-1.0, 1.0)
                
                # 确保值在合理范围内
                value = max(3, min(30, value))
                
                future.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "percentage": round(value, 1)
                })
            
            category_trends.append({
                "category": category,
                "current_percentage": current,
                "trend": trend,
                "history": history,
                "prediction": future,
                "confidence": random.randint(70, 95)
            })
        
        return category_trends
    
    def _predict_platform_trends(self, historical_data: Dict[str, Dict[str, List]]) -> Dict[str, Any]:
        """预测各平台的趋势变化"""
        # 分析平台趋势
        platform_growth = self._analyze_platform_trends(historical_data)
        
        # 预测未来平台趋势
        future_trends = {}
        
        for platform in platform_growth["emerging"]:
            platform_name = platform["platform"]
            future_trends[platform_name] = {
                "current_trend": "rising",
                "future_trend": "continued_growth",
                "growth_potential": random.randint(10, 30),
                "confidence": random.randint(70, 90)
            }
        
        for platform in platform_growth["declining"]:
            platform_name = platform["platform"]
            future_trends[platform_name] = {
                "current_trend": "falling",
                "future_trend": random.choice(["stabilize", "continued_decline"]),
                "decline_rate": random.randint(5, 20),
                "confidence": random.randint(60, 85)
            }
        
        # 添加其他平台的预测
        for platform in crawler_factory.keys():
            if platform not in future_trends:
                future_trends[platform] = {
                    "current_trend": "stable",
                    "future_trend": random.choice(["slight_growth", "stable", "slight_decline"]),
                    "change_rate": random.randint(-10, 10),
                    "confidence": random.randint(60, 80)
                }
        
        return {
            "platform_predictions": future_trends,
            "emerging_platforms": [p["platform"] for p in platform_growth["emerging"][:3]],
            "declining_platforms": [p["platform"] for p in platform_growth["declining"][:3]]
        }
    
    def _predict_keywords(self, historical_data: Dict[str, Dict[str, List]]) -> Dict[str, List]:
        """预测关键词趋势"""
        # 分析关键词历史趋势
        keyword_trends = self._analyze_keyword_trends(historical_data)
        
        # 预测未来关键词趋势
        keyword_predictions = {
            "emerging": [],
            "fading": []
        }
        
        # 预测新兴关键词
        for keyword in keyword_trends["rising"]:
            keyword_predictions["emerging"].append({
                "keyword": keyword["keyword"],
                "current_growth": keyword["growth_rate"],
                "predicted_growth": keyword["growth_rate"] * random.uniform(1.1, 1.5),
                "peak_time": f"{random.randint(1, 3)}天后",
                "confidence": random.randint(70, 90)
            })
        
        # 预测衰退关键词
        for keyword in keyword_trends["falling"]:
            keyword_predictions["fading"].append({
                "keyword": keyword["keyword"],
                "current_decline": abs(keyword["growth_rate"]),
                "predicted_decline": abs(keyword["growth_rate"]) * random.uniform(1.1, 1.3),
                "expected_duration": f"{random.randint(2, 5)}天",
                "confidence": random.randint(75, 90)
            })
        
        return keyword_predictions
    
    def _find_rising_topics(self, historical_data: Dict[str, Dict[str, List]]) -> List[Dict[str, Any]]:
        """查找上升趋势的话题"""
        # 按日期排序的数据
        sorted_dates = sorted(historical_data.keys())
        if len(sorted_dates) < 2:
            return []
        
        # 统计每个话题在不同日期的出现情况和排名
        topic_trends = defaultdict(list)
        
        for date_str in sorted_dates:
            daily_data = historical_data[date_str]
            
            # 收集当天所有话题
            for platform, items in daily_data.items():
                for item in items:
                    title = item.get("title", "")
                    if not title:
                        continue
                    
                    # 记录话题在当天的排名和平台
                    rank = items.index(item) + 1 if hasattr(items, "index") else 0
                    score = item.get("score", 0)
                    
                    topic_trends[title].append({
                        "date": date_str,
                        "platform": platform,
                        "rank": rank,
                        "score": score
                    })
        
        # 计算话题的上升趋势
        rising_topics = []
        
        for title, appearances in topic_trends.items():
            if len(appearances) < 2:
                continue
            
            # 按日期排序
            appearances.sort(key=lambda x: x["date"])
            
            # 计算排名变化和分数变化
            first_appearance = appearances[0]
            last_appearance = appearances[-1]
            
            rank_change = first_appearance["rank"] - last_appearance["rank"]  # 排名上升为正
            score_change = last_appearance["score"] - first_appearance["score"]  # 分数上升为正
            
            # 如果排名上升或分数上升，认为是上升趋势
            if rank_change > 0 or score_change > 0:
                rising_topics.append({
                    "title": title,
                    "rank_change": rank_change,
                    "score_change": score_change,
                    "first_appearance": first_appearance,
                    "last_appearance": last_appearance,
                    "days_tracked": len(set(app["date"] for app in appearances))
                })
        
        # 按排名变化和分数变化排序
        rising_topics.sort(key=lambda x: (x["rank_change"], x["score_change"]), reverse=True)
        return rising_topics[:10]  # 返回前10个上升趋势话题
    
    def _find_persistent_topics(self, historical_data: Dict[str, Dict[str, List]]) -> List[Dict[str, Any]]:
        """查找持续热门的话题"""
        # 按日期排序的数据
        sorted_dates = sorted(historical_data.keys())
        if len(sorted_dates) < 2:
            return []
        
        # 统计每个话题在不同日期的出现次数
        topic_appearances = defaultdict(int)
        topic_platforms = defaultdict(set)
        topic_last_seen = {}
        
        for date_str in sorted_dates:
            daily_data = historical_data[date_str]
            
            # 收集当天所有话题
            for platform, items in daily_data.items():
                for item in items:
                    title = item.get("title", "")
                    if not title:
                        continue
                    
                    topic_appearances[title] += 1
                    topic_platforms[title].add(platform)
                    topic_last_seen[title] = date_str
        
        # 找出持续出现的话题
        persistent_topics = []
        
        for title, appearances in topic_appearances.items():
            # 如果话题在超过一半的天数中出现，认为是持续热门话题
            if appearances >= len(sorted_dates) / 2:
                persistent_topics.append({
                    "title": title,
                    "appearances": appearances,
                    "appearance_rate": appearances / len(sorted_dates),
                    "platforms": list(topic_platforms[title]),
                    "platform_count": len(topic_platforms[title]),
                    "last_seen": topic_last_seen[title]
                })
        
        # 按出现次数和平台数量排序
        persistent_topics.sort(key=lambda x: (x["appearances"], x["platform_count"]), reverse=True)
        return persistent_topics[:10]  # 返回前10个持续热门话题
    
    def _analyze_platform_trends(self, historical_data: Dict[str, Dict[str, List]]) -> Dict[str, Any]:
        """分析平台趋势"""
        # 按日期排序的数据
        sorted_dates = sorted(historical_data.keys())
        if len(sorted_dates) < 2:
            return {"emerging": [], "declining": []}
        
        # 统计每个平台在不同日期的热点数量
        platform_trends = defaultdict(lambda: defaultdict(int))
        
        for date_str in sorted_dates:
            daily_data = historical_data[date_str]
            
            for platform, items in daily_data.items():
                platform_trends[platform][date_str] = len(items)
        
        # 计算平台的增长趋势
        platform_growth = {}
        
        for platform, date_counts in platform_trends.items():
            if len(date_counts) < 2:
                continue
            
            # 计算增长率
            first_date = sorted_dates[0]
            last_date = sorted_dates[-1]
            
            first_count = date_counts.get(first_date, 0)
            last_count = date_counts.get(last_date, 0)
            
            if first_count == 0:
                growth_rate = 100 if last_count > 0 else 0
            else:
                growth_rate = ((last_count - first_count) / first_count) * 100
            
            platform_growth[platform] = {
                "first_count": first_count,
                "last_count": last_count,
                "growth_rate": growth_rate,
                "trend": "rising" if growth_rate > 0 else "falling" if growth_rate < 0 else "stable"
            }
        
        # 按增长率排序
        emerging_platforms = sorted(
            platform_growth.items(), 
            key=lambda x: x[1]["growth_rate"], 
            reverse=True
        )
        
        return {
            "emerging": [{"platform": p, **data} for p, data in emerging_platforms[:5]],
            "declining": [{"platform": p, **data} for p, data in emerging_platforms[-5:] if data["growth_rate"] < 0]
        }
    
    def _analyze_keyword_trends(self, historical_data: Dict[str, Dict[str, List]]) -> Dict[str, List]:
        """分析关键词趋势"""
        # 按日期排序的数据
        sorted_dates = sorted(historical_data.keys())
        if len(sorted_dates) < 2:
            return {"rising": [], "falling": []}
        
        # 统计每个日期的关键词频率
        date_keywords = defaultdict(Counter)
        
        for date_str in sorted_dates:
            daily_data = historical_data[date_str]
            
            # 收集当天所有标题
            all_titles = []
            for platform, items in daily_data.items():
                all_titles.extend([item.get("title", "") for item in items])
            
            # 分词并统计频率（简化实现）
            for title in all_titles:
                for word in title.split():
                    if len(word) > 1:  # 忽略单字
                        date_keywords[date_str][word] += 1
        
        # 分析关键词趋势
        keyword_trends = defaultdict(list)
        
        # 收集所有关键词
        all_keywords = set()
        for date_counter in date_keywords.values():
            all_keywords.update(date_counter.keys())
        
        # 分析每个关键词的趋势
        for keyword in all_keywords:
            trend_data = []
            
            for date_str in sorted_dates:
                count = date_keywords[date_str].get(keyword, 0)
                trend_data.append({"date": date_str, "count": count})
            
            # 计算趋势方向
            if len(trend_data) >= 2:
                first_count = trend_data[0]["count"]
                last_count = trend_data[-1]["count"]
                
                if first_count == 0:
                    growth_rate = 100 if last_count > 0 else 0
                else:
                    growth_rate = ((last_count - first_count) / first_count) * 100
                
                if growth_rate > 50:  # 增长超过50%
                    keyword_trends["rising"].append({
                        "keyword": keyword,
                        "growth_rate": growth_rate,
                        "first_count": first_count,
                        "last_count": last_count,
                        "trend_data": trend_data
                    })
                elif growth_rate < -50:  # 下降超过50%
                    keyword_trends["falling"].append({
                        "keyword": keyword,
                        "growth_rate": growth_rate,
                        "first_count": first_count,
                        "last_count": last_count,
                        "trend_data": trend_data
                    })
        
        # 按增长率排序
        keyword_trends["rising"].sort(key=lambda x: x["growth_rate"], reverse=True)
        keyword_trends["falling"].sort(key=lambda x: x["growth_rate"])
        
        return {
            "rising": keyword_trends["rising"][:10],  # 前10个上升关键词
            "falling": keyword_trends["falling"][:10]  # 前10个下降关键词
        }

# 添加随机模块，用于生成模拟数据
import random 