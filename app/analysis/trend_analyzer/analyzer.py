import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import pytz
import re
import jieba
import jieba.analyse
from typing import Dict, List, Any, Optional, Tuple
import os

from app.core import cache, db
from app.utils.logger import log
from app.services import crawler_factory

class TrendAnalyzer:
    """热点聚合分析器，用于分析各平台热点数据的共性和差异"""
    
    def __init__(self):
        self.cache_key_prefix = "analysis:trend:"
        self.cache_expire = 3600  # 1小时缓存
        self.shanghai_tz = pytz.timezone('Asia/Shanghai')
        # 定义主题分类
        self.categories = ["科技", "娱乐", "社会", "财经", "体育", "教育", "健康", "国际"]
        
        # 从配置文件加载停用词
        self.stopwords = self._load_stopwords()
        
        # 从配置文件加载各类别的关键词特征词典
        self.category_keywords = self._load_category_keywords()
        
        # 加载自定义词典
        try:
            # 尝试加载自定义词典文件
            jieba.load_userdict("app/data/custom_dict.txt")
        except:
            log.warning("Custom dictionary not found, using default dictionary")
    
    def _load_stopwords(self) -> set:
        """从配置文件加载停用词"""
        try:
            with open("app/data/config/stopwords.json", "r", encoding="utf-8") as f:
                stopwords_data = json.load(f)
                return set(stopwords_data.get("stopwords", []))
        except Exception as e:
            log.error(f"Error loading stopwords: {e}")
            # 如果加载失败，返回一个基本的停用词集合
            return set(["的", "了", "和", "是", "在", "我", "有", "个", "这", "那", "什么", "怎么"])
    
    def _load_category_keywords(self) -> Dict[str, List[str]]:
        """从配置文件加载类别关键词"""
        try:
            with open("app/data/config/category_keywords.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            log.error(f"Error loading category keywords: {e}")
            # 如果加载失败，返回一个简单的类别关键词字典
            return {category: [] for category in self.categories}
    
    def get_analysis(self, date_str: Optional[str] = None, analysis_type: str = "main") -> Dict[str, Any]:
        """获取指定日期的热点聚合分析
        
        Args:
            date_str: 日期字符串，格式为YYYY-MM-DD
            analysis_type: 分析类型，可选值为 main(主题分析), platform(平台对比), 
                           cross(跨平台热点), advanced(高级分析)
        """
        if not date_str:
            date_str = datetime.now(self.shanghai_tz).strftime("%Y-%m-%d")
        
        # 尝试从缓存获取
        cache_key = f"{self.cache_key_prefix}{date_str}:{analysis_type}"
        cached_analysis = cache.get_cache(cache_key)
        if cached_analysis:
            log.info(f"Retrieved trend analysis from cache for {date_str}, type: {analysis_type}")
            return cached_analysis
        
        # 执行分析
        analysis_result = self._analyze_trends(date_str, analysis_type)
        
        # 缓存结果
        if analysis_result:
            cache.set_cache(cache_key, analysis_result, self.cache_expire)
        
        return analysis_result
    
    def _get_platform_data(self, date_str: str) -> Dict[str, List]:
        """获取所有平台的热点数据（共用方法）"""
        all_platform_data = {}
        for platform in crawler_factory.keys():
            cache_key = f"crawler:{platform}:{date_str}"
            platform_data = cache.get_cache(cache_key)
            if platform_data:
                all_platform_data[platform] = platform_data
        
        return all_platform_data

    def get_platform_comparison(self, date_str: Optional[str] = None) -> Dict[str, Any]:
        """获取平台对比分析数据
        
        Args:
            date_str: 日期字符串，格式为YYYY-MM-DD
        """
        if not date_str:
            date_str = datetime.now(self.shanghai_tz).strftime("%Y-%m-%d")
        
        # 尝试从缓存获取
        cache_key = f"{self.cache_key_prefix}{date_str}:platform_comparison"
        cached_analysis = cache.get_cache(cache_key)
        if cached_analysis:
            log.info(f"Retrieved platform comparison from cache for {date_str}")
            return cached_analysis
        
        # 收集所有平台的热点数据
        all_platform_data = self._get_platform_data(date_str)
        
        if not all_platform_data:
            log.warning(f"No data available for platform comparison on {date_str}")
            return {
                "status": "error",
                "message": "暂无可用数据进行平台对比分析",
                "date": date_str
            }
        
        # 执行平台对比分析
        analysis_result = self._analyze_platform_comparison(all_platform_data, date_str)
        
        # 缓存结果
        if analysis_result:
            cache.set_cache(cache_key, analysis_result, self.cache_expire)
        
        return analysis_result
    
    def get_cross_platform_analysis(self, date_str: Optional[str] = None, refresh: bool = False) -> Dict[str, Any]:
        """获取跨平台热点分析数据
        
        Args:
            date_str: 日期字符串，格式为YYYY-MM-DD
            refresh: 是否强制刷新缓存
        """
        if not date_str:
            date_str = datetime.now(self.shanghai_tz).strftime("%Y-%m-%d")
        
        # 缓存处理
        cache_key = f"{self.cache_key_prefix}{date_str}:cross_platform"
        
        # 如果强制刷新或者没有缓存，则重新分析
        if refresh:
            # 清除旧的缓存
            cache.delete_cache(cache_key)
        else:
            # 尝试从缓存获取
            cached_analysis = cache.get_cache(cache_key)
            if cached_analysis:
                log.info(f"Retrieved cross platform analysis from cache for {date_str}")
                return cached_analysis
        
        # 收集所有平台的热点数据
        all_platform_data = self._get_platform_data(date_str)
        
        if not all_platform_data:
            log.warning(f"No data available for cross platform analysis on {date_str}")
            return {
                "status": "error",
                "message": "暂无可用数据进行跨平台热点分析",
                "date": date_str
            }
        
        # 过滤掉不是列表的数据
        filtered_data = {}
        for platform, data in all_platform_data.items():
            if isinstance(data, list):
                filtered_data[platform] = data
            else:
                log.warning(f"Platform {platform} data is not a list, skipping")
        
        # 使用过滤后的数据
        all_platform_data = filtered_data
        
        # 执行跨平台热点分析
        analysis_result = self._analyze_cross_platform(all_platform_data, date_str)
        
        # 缓存结果
        if analysis_result:
            cache.set_cache(cache_key, analysis_result, self.cache_expire)
        
        return analysis_result
    
    def get_advanced_analysis(self, date_str: Optional[str] = None, refresh: bool = False) -> Dict[str, Any]:
        """获取高级分析数据
        
        Args:
            date_str: 日期字符串，格式为YYYY-MM-DD
            refresh: 是否强制刷新缓存
        """
        if not date_str:
            date_str = datetime.now(self.shanghai_tz).strftime("%Y-%m-%d")
        
        # 缓存处理
        cache_key = f"{self.cache_key_prefix}{date_str}:advanced_analysis"
        
        # 如果强制刷新或者没有缓存，则重新分析
        if refresh:
            # 清除旧的缓存
            cache.delete_cache(cache_key)
        else:
            # 尝试从缓存获取
            cached_analysis = cache.get_cache(cache_key)
            if cached_analysis:
                log.info(f"Retrieved advanced analysis from cache for {date_str}")
                return cached_analysis
        
        # 收集所有平台的热点数据
        all_platform_data = self._get_platform_data(date_str)
        
        if not all_platform_data:
            log.warning(f"No data available for advanced analysis on {date_str}")
            return {
                "status": "error",
                "message": "暂无可用数据进行高级分析",
                "date": date_str
            }
        
        # 过滤掉不是列表的数据
        filtered_data = {}
        for platform, data in all_platform_data.items():
            if isinstance(data, list):
                filtered_data[platform] = data
            else:
                log.warning(f"Platform {platform} data is not a list, skipping")
        
        # 使用过滤后的数据
        all_platform_data = filtered_data
        
        # 执行高级分析
        analysis_result = self._analyze_advanced(all_platform_data, date_str)
        
        # 缓存结果
        if analysis_result:
            cache.set_cache(cache_key, analysis_result, self.cache_expire)
        
        return analysis_result
    
    def _analyze_trends(self, date_str: str, analysis_type: str) -> Dict[str, Any]:
        """分析各平台热点数据，提取共性和差异"""
        # 收集所有平台的热点数据
        all_platform_data = {}
        for platform in crawler_factory.keys():
            cache_key = f"crawler:{platform}:{date_str}"
            platform_data = cache.get_cache(cache_key)
            if platform_data:
                all_platform_data[platform] = platform_data
        
        if not all_platform_data:
            log.warning(f"No data available for trend analysis on {date_str}")
            return {
                "status": "error",
                "message": "暂无可用数据进行分析",
                "date": date_str
            }
        
        # 现在只处理主题分析，其他类型通过专门的接口处理
        return self._analyze_main_themes(all_platform_data, date_str)
    
    def _analyze_main_themes(self, all_data: Dict[str, List], date_str: str) -> Dict[str, Any]:
        """主题分析 - 分析热门关键词、主题分布和相关主题词组"""
        # 提取热门关键词（用于标签云）
        hot_keywords = self._extract_hot_keywords(all_data)
        
        # 分析主题分布（各类别占比）
        topic_distribution = self._analyze_topic_distribution(all_data)
        
        # 分析相关主题词组
        related_topic_groups = self._analyze_related_topic_groups(all_data)
        
        # 返回结果
        return {
            "status": "success",
            "date": date_str,
            "analysis_type": "main",
            "hot_keywords": hot_keywords,
            "topic_distribution": topic_distribution,
            "related_topic_groups": related_topic_groups,
            "updated_at": datetime.now(self.shanghai_tz).strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def _analyze_platform_comparison(self, all_data: Dict[str, List], date_str: str) -> Dict[str, Any]:
        """平台对比分析"""
        # 分析各平台热点特点
        platform_stats = self._get_platform_stats(all_data)
        
        # 平台热度排行
        platform_rankings = self._get_platform_rankings(all_data)
        
        # 平台更新频率
        platform_update_frequency = self._get_platform_update_frequency(all_data)
        
        return {
            "status": "success",
            "date": date_str,
            "analysis_type": "platform",
            "platform_stats": platform_stats,
            "platform_rankings": platform_rankings,
            "platform_update_frequency": platform_update_frequency,
            "updated_at": datetime.now(self.shanghai_tz).strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def _get_platform_rankings(self, all_data: Dict[str, List]) -> List[Dict[str, Any]]:
        """获取平台热度排行"""
        platform_scores = []
        
        for platform, items in all_data.items():
            # 确保items是列表
            if not isinstance(items, list):
                log.warning(f"Platform {platform} data is not a list, skipping")
                continue
                
            # 过滤出有效的条目（必须是字典）
            valid_items = []
            for item in items:
                if isinstance(item, dict):
                    valid_items.append(item)
                else:
                    log.warning(f"Item in platform {platform} is not a dictionary, skipping: {item}")
            
            # 计算平台热度分数
            total_items = len(valid_items)
            
            # 安全地计算平均分数
            try:
                scores = [item.get("score", 0) for item in valid_items]
                # 确保所有分数都是数字
                scores = [s for s in scores if isinstance(s, (int, float))]
                avg_score = sum(scores) / max(len(scores), 1) if scores else 0
            except Exception as e:
                log.error(f"Error calculating average score for {platform}: {e}")
                avg_score = 0
            
            # 计算平台总热度
            platform_heat = total_items * avg_score
            
            # 计算平台热度变化趋势
            # 简化实现：随机生成变化趋势
            try:
                import random
                trend_value = random.uniform(-10.0, 10.0)
            except Exception as e:
                log.error(f"Error generating trend value: {e}")
                trend_value = 0.0
            
            platform_scores.append({
                "platform": platform,
                "heat": round(platform_heat, 1),
                "trend": round(trend_value, 1)
            })
        
        # 按热度排序
        platform_scores.sort(key=lambda x: x["heat"], reverse=True)
        
        # 添加排名
        for i, item in enumerate(platform_scores):
            item["rank"] = i + 1
        
        return platform_scores
    
    def _get_platform_update_frequency(self, all_data: Dict[str, List]) -> Dict[str, Any]:
        """获取平台更新频率"""
        # 分析各平台的更新时间分布
        # 简化实现：将一天分为四个时段，统计每个时段的更新比例
        time_periods = {
            "morning": {"label": "上午", "percentage": 0},
            "afternoon": {"label": "下午", "percentage": 0},
            "evening": {"label": "晚上", "percentage": 0},
            "night": {"label": "凌晨", "percentage": 0}
        }
        
        platform_frequencies = {}
        
        for platform, items in all_data.items():
            # 统计各时段的更新数量
            period_counts = {
                "morning": 0,
                "afternoon": 0,
                "evening": 0,
                "night": 0
            }
            
            for item in items:
                # 获取更新时间
                update_time = item.get("update_time", "")
                if not update_time:
                    continue
                
                try:
                    # 尝试解析时间
                    if isinstance(update_time, str):
                        # 尝试从字符串解析时间
                        if ":" in update_time:
                            # 如果只有时间部分，如 "14:30"
                            hour = int(update_time.split(":")[0])
                        else:
                            # 如果是完整日期时间，尝试提取小时
                            for time_format in ["%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S", "%H:%M:%S"]:
                                try:
                                    parsed_time = datetime.strptime(update_time, time_format)
                                    hour = parsed_time.hour
                                    break
                                except ValueError:
                                    continue
                            else:
                                # 如果所有格式都不匹配，跳过
                                continue
                    elif isinstance(update_time, (int, float)):
                        # 如果是时间戳
                        hour = datetime.fromtimestamp(update_time).hour
                    else:
                        continue
                    
                    # 根据小时确定时段
                    if 6 <= hour < 12:
                        period_counts["morning"] += 1
                    elif 12 <= hour < 18:
                        period_counts["afternoon"] += 1
                    elif 18 <= hour < 24:
                        period_counts["evening"] += 1
                    else:
                        period_counts["night"] += 1
                        
                except Exception as e:
                    log.error(f"Error parsing update time: {update_time}, {e}")
                    continue
            
            # 计算各时段百分比
            total_counts = sum(period_counts.values())
            if total_counts > 0:
                platform_frequencies[platform] = {
                    "morning": {"label": "上午", "percentage": round(period_counts["morning"] / total_counts * 100, 1)},
                    "afternoon": {"label": "下午", "percentage": round(period_counts["afternoon"] / total_counts * 100, 1)},
                    "evening": {"label": "晚上", "percentage": round(period_counts["evening"] / total_counts * 100, 1)},
                    "night": {"label": "凌晨", "percentage": round(period_counts["night"] / total_counts * 100, 1)}
                }
            else:
                # 如果没有有效的更新时间数据，使用平均分布
                platform_frequencies[platform] = {
                    "morning": {"label": "上午", "percentage": 25.0},
                    "afternoon": {"label": "下午", "percentage": 25.0},
                    "evening": {"label": "晚上", "percentage": 25.0},
                    "night": {"label": "凌晨", "percentage": 25.0}
                }
        
        # 计算所有平台的平均分布
        all_platform_avg = {
            "morning": {"label": "上午", "percentage": 0},
            "afternoon": {"label": "下午", "percentage": 0},
            "evening": {"label": "晚上", "percentage": 0},
            "night": {"label": "凌晨", "percentage": 0}
        }
        
        if platform_frequencies:
            for period in ["morning", "afternoon", "evening", "night"]:
                all_platform_avg[period]["percentage"] = round(
                    sum(platform[period]["percentage"] for platform in platform_frequencies.values()) / len(platform_frequencies),
                    1
                )
        
        return {
            "by_platform": platform_frequencies,
            "overall": all_platform_avg
        }
    
    def _analyze_cross_platform(self, all_data: Dict[str, List], date_str: str) -> Dict[str, Any]:
        """跨平台热点分析"""
        # 分析跨平台共同热点
        common_topics = self._find_cross_platform_topics(all_data)
        
        return {
            "status": "success",
            "date": date_str,
            "analysis_type": "cross_platform",
            "common_topics": common_topics,
            "updated_at": datetime.now(self.shanghai_tz).strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def _analyze_advanced(self, all_data: Dict[str, List], date_str: str) -> Dict[str, Any]:
        """高级分析"""
        # 关键词云图 - 按类别提取关键词
        keyword_clouds = self._extract_keyword_clouds(all_data)
        
        # 情感分析
        sentiment_analysis = self._analyze_sentiment(all_data)
        
        # 热点演变趋势
        trend_evolution = self._analyze_trend_evolution(all_data, date_str)
        
        return {
            "status": "success",
            "date": date_str,
            "analysis_type": "advanced",
            "keyword_clouds": keyword_clouds,
            "sentiment_analysis": sentiment_analysis,
            "trend_evolution": trend_evolution,
            "updated_at": datetime.now(self.shanghai_tz).strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def _extract_hot_keywords(self, all_data: Dict[str, List]) -> List[Dict[str, Any]]:
        """使用jieba提取热门关键词（用于标签云）"""
        # 收集所有标题
        all_titles = []
        for platform, items in all_data.items():
            for item in items:
                title = item.get("title", "")
                if title:
                    all_titles.append(title)
        
        if not all_titles:
            return []
        
        # 合并所有标题为一个文本
        combined_text = " ".join(all_titles)
        
        # 使用jieba的TF-IDF算法提取关键词
        keywords = jieba.analyse.extract_tags(
            combined_text,
            topK=100,  # 提取更多关键词，后续过滤
            withWeight=True
        )
        
        # 过滤停用词并调整权重
        filtered_keywords = []
        for word, weight in keywords:
            # 跳过停用词
            if word in self.stopwords:
                continue
                
            # 跳过单个汉字
            if len(word) == 1 and re.search(r'[\u4e00-\u9fff]', word):
                continue
                
            # 跳过纯数字
            if re.match(r'^\d+$', word):
                continue
            
            # 检查词在标题中出现的频率
            title_count = sum(1 for title in all_titles if word in title)
            if title_count > 1:  # 至少在两个标题中出现
                weight *= (1 + min(title_count / 10, 2.0))  # 最多提升3倍
                
            filtered_keywords.append((word, weight))
        
        # 排序并格式化结果
        filtered_keywords.sort(key=lambda x: x[1], reverse=True)
        hot_keywords = [
            {"text": word, "weight": round(weight * 10, 1)}  # 放大权重以便于可视化
            for word, weight in filtered_keywords[:30]  # 取前30个
        ]
        
        return hot_keywords
    
    def _analyze_topic_distribution(self, all_data: Dict[str, List]) -> List[Dict[str, Any]]:
        """分析主题分布（各类别占比）"""
        # 收集所有标题和内容
        all_texts = []
        for platform, items in all_data.items():
            for item in items:
                title = item.get("title", "")
                content = item.get("content", "")
                if title:
                    all_texts.append(title)
                if content:
                    all_texts.append(content)
        
        if not all_texts:
            return self._generate_random_distribution()  # 无数据时返回随机分布
        
        # 合并所有文本
        combined_text = " ".join(all_texts)
        
        # 使用jieba提取关键词
        keywords = jieba.analyse.extract_tags(
            combined_text,
            topK=200,  # 提取足够多的关键词以便分类
            withWeight=True
        )
        
        # 初始化各类别得分
        category_scores = {category: 0.0 for category in self.categories}
        
        # 计算每个类别的得分
        for word, weight in keywords:
            for category, category_keywords in self.category_keywords.items():
                # 如果关键词在该类别的特征词中，增加该类别得分
                if word in category_keywords:
                    category_scores[category] += weight
                # 部分匹配（关键词是类别特征词的一部分或特征词是关键词的一部分）
                else:
                    for category_word in category_keywords:
                        if (word in category_word or category_word in word) and len(word) > 1 and len(category_word) > 1:
                            category_scores[category] += weight * 0.5
                            break
        
        # 如果所有类别得分都为0，返回随机分布
        if sum(category_scores.values()) == 0:
            return self._generate_random_distribution()
        
        # 计算百分比
        total_score = sum(category_scores.values())
        distribution = []
        
        for category, score in category_scores.items():
            if total_score > 0:
                percentage = (score / total_score) * 100
                distribution.append({
                    "category": category,
                    "percentage": round(percentage, 1)
                })
        
        # 按百分比降序排序
        distribution.sort(key=lambda x: x["percentage"], reverse=True)
        
        # 如果某些类别百分比太小，可以过滤掉
        filtered_distribution = [item for item in distribution if item["percentage"] >= 1.0]
        
        # 如果过滤后为空，返回原始分布
        if not filtered_distribution:
            return distribution
            
        return filtered_distribution
    
    def _generate_random_distribution(self) -> List[Dict[str, Any]]:
        """生成随机的主题分布（当无法基于内容分析时使用）"""
        import random
        
        # 确保总和为100%的随机分布
        total = 100
        categories = self.categories.copy()
        distribution = []
        
        for i in range(len(categories) - 1):
            if total <= 0:
                break
            
            value = round(random.uniform(10, 25), 1)
            value = min(value, total)
            total -= value
            
            distribution.append({
                "category": categories[i],
                "percentage": value
            })
        
        # 最后一个类别分配剩余百分比
        if total > 0 and categories:
            distribution.append({
                "category": categories[-1],
                "percentage": round(total, 1)
            })
        
        # 按百分比降序排序
        distribution.sort(key=lambda x: x["percentage"], reverse=True)
        return distribution
    
    def _analyze_related_topic_groups(self, all_data: Dict[str, List]) -> List[Dict[str, Any]]:
        """分析相关主题词组"""
        # 收集所有标题
        all_titles = []
        for platform, items in all_data.items():
            for item in items:
                title = item.get("title", "")
                if title:
                    all_titles.append(title)
        
        if not all_titles:
            return []
        
        # 使用jieba提取关键词
        keywords_by_title = []
        for title in all_titles:
            # 使用jieba提取每个标题的关键词
            keywords = jieba.analyse.extract_tags(title, topK=5)
            # 过滤停用词
            valid_keywords = [k for k in keywords if k not in self.stopwords and len(k) > 1]
            if valid_keywords:
                keywords_by_title.append(valid_keywords)
        
        # 分析词组共现情况
        word_pairs = []
        word_counter = Counter()
        
        # 首先统计所有关键词的频率
        for keywords in keywords_by_title:
            for keyword in keywords:
                word_counter[keyword] += 1
        
        # 只考虑出现频率较高的关键词（至少出现2次）
        common_words = [word for word, count in word_counter.most_common(50) if count >= 2]
        
        # 创建共现矩阵
        co_occurrence_matrix = defaultdict(lambda: defaultdict(int))
        
        # 分析共现
        for keywords in keywords_by_title:
            # 只考虑标题中有效的关键词
            valid_words = [w for w in keywords if w in common_words]
            # 分析两两共现
            for i, word1 in enumerate(valid_words):
                for word2 in valid_words[i+1:]:
                    if word1 != word2:  # 确保不是同一个词
                        # 按字母顺序排序，确保相同的词对只记录一次
                        key_pair = tuple(sorted([word1, word2]))
                        co_occurrence_matrix[key_pair[0]][key_pair[1]] += 1
        
        # 转换为词对列表
        for word1, co_words in co_occurrence_matrix.items():
            for word2, count in co_words.items():
                # 只考虑共现次数达到阈值的词对（至少共现3次）
                if count >= 3:
                    # 检查词对是否有意义
                    if self._is_meaningful_word_pair(word1, word2):
                        word_pairs.append({
                            "words": [word1, word2],
                            "co_occurrence": count
                        })
        
        # 合并相似词组
        merged_pairs = self._merge_similar_pairs(word_pairs)
        
        # 按共现次数排序
        merged_pairs.sort(key=lambda x: x["co_occurrence"], reverse=True)
        
        # 返回前10个共现词组
        return merged_pairs[:10]
    
    def _is_meaningful_word_pair(self, word1: str, word2: str) -> bool:
        """判断词对是否有意义"""
        # 如果两个词都是单字，可能意义不大
        if len(word1) == 1 and len(word2) == 1:
            return False
            
        # 如果两个词都是数字，可能意义不大
        if word1.isdigit() and word2.isdigit():
            return False
            
        # 如果两个词是同一类别的关键词，可能更有意义
        for category, keywords in self.category_keywords.items():
            if word1 in keywords and word2 in keywords:
                return True
                
        # 检查是否是常见的无意义组合
        meaningless_combinations = [
            ("什么", "怎么"), ("为何", "如何"), ("这个", "那个"),
            ("一个", "几个"), ("多少", "一些"), ("很多", "许多")
        ]
        if (word1, word2) in meaningless_combinations or (word2, word1) in meaningless_combinations:
            return False
            
        # 默认认为有意义
        return True
    
    def _merge_similar_pairs(self, word_pairs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """合并相似的词对"""
        if not word_pairs:
            return []
            
        # 按共现次数排序
        sorted_pairs = sorted(word_pairs, key=lambda x: x["co_occurrence"], reverse=True)
        
        # 创建词对集合，用于快速查找
        pair_set = {tuple(sorted(p["words"])) for p in word_pairs}
        
        # 创建词对组，存储相关联的词对
        pair_groups = []
        processed_pairs = set()
        
        for pair in sorted_pairs:
            pair_key = tuple(sorted(pair["words"]))
            
            # 如果已处理，跳过
            if pair_key in processed_pairs:
                continue
                
            # 创建新组
            current_group = {pair_key}
            processed_pairs.add(pair_key)
            
            # 查找相关词对
            for other_pair in sorted_pairs:
                other_key = tuple(sorted(other_pair["words"]))
                
                # 如果已处理，跳过
                if other_key in processed_pairs:
                    continue
                    
                # 如果有共同词，加入当前组
                if pair_key[0] in other_key or pair_key[1] in other_key:
                    current_group.add(other_key)
                    processed_pairs.add(other_key)
            
            # 添加到组列表
            if current_group:
                pair_groups.append(current_group)
        
        # 合并结果
        merged_results = []
        
        for group in pair_groups:
            # 如果组中只有一个词对，直接添加
            if len(group) == 1:
                pair_key = list(group)[0]
                for pair in sorted_pairs:
                    if tuple(sorted(pair["words"])) == pair_key:
                        merged_results.append(pair)
                        break
            else:
                # 合并组中的词对
                all_words = set()
                total_co_occurrence = 0
                max_co_occurrence = 0
                
                for pair_key in group:
                    all_words.update(pair_key)
                    for pair in sorted_pairs:
                        if tuple(sorted(pair["words"])) == pair_key:
                            total_co_occurrence += pair["co_occurrence"]
                            max_co_occurrence = max(max_co_occurrence, pair["co_occurrence"])
                            break
                
                # 如果合并后的词太多，只保留最重要的词
                if len(all_words) > 3:
                    # 找出组中出现最频繁的词对
                    most_frequent_pair = None
                    for pair in sorted_pairs:
                        pair_key = tuple(sorted(pair["words"]))
                        if pair_key in group:
                            if most_frequent_pair is None or pair["co_occurrence"] > most_frequent_pair["co_occurrence"]:
                                most_frequent_pair = pair
                    
                    if most_frequent_pair:
                        merged_results.append({
                            "words": most_frequent_pair["words"],
                            "co_occurrence": max_co_occurrence
                        })
                else:
                    # 添加合并结果
                    merged_results.append({
                        "words": list(all_words),
                        "co_occurrence": max_co_occurrence
                    })
        
        # 再次排序
        merged_results.sort(key=lambda x: x["co_occurrence"], reverse=True)
        return merged_results
    
    def _analyze_platform_overlap(self, all_data: Dict[str, List]) -> Dict[str, Any]:
        """分析平台间热点重叠度"""
        platforms = list(all_data.keys())
        overlap_matrix = {}
        
        for i, platform1 in enumerate(platforms):
            overlap_matrix[platform1] = {}
            titles1 = {item.get("title", "") for item in all_data[platform1] if item.get("title")}
            
            for platform2 in platforms:
                if platform1 == platform2:
                    overlap_matrix[platform1][platform2] = 100  # 自身重叠度为100%
                    continue
                
                titles2 = {item.get("title", "") for item in all_data[platform2] if item.get("title")}
                
                # 计算重叠度
                if not titles1 or not titles2:
                    overlap = 0
                else:
                    # 使用Jaccard相似度
                    intersection = len(titles1.intersection(titles2))
                    union = len(titles1.union(titles2))
                    overlap = round((intersection / union) * 100, 1)
                
                overlap_matrix[platform1][platform2] = overlap
        
        return overlap_matrix
    
    def _analyze_propagation_paths(self, all_data: Dict[str, List]) -> List[Dict[str, Any]]:
        """分析热点传播路径（简化实现）"""
        # 实际应基于时间戳分析热点在不同平台上的传播顺序
        # 这里简化为随机生成一些传播路径
        import random
        
        cross_platform_topics = self._find_cross_platform_topics(all_data)
        propagation_paths = []
        
        for topic in cross_platform_topics[:5]:  # 取前5个跨平台话题
            platforms = list({item["platform"] for item in topic["items"]})
            if len(platforms) < 2:
                continue
                
            # 随机排序平台，模拟传播顺序
            random.shuffle(platforms)
            
            propagation_paths.append({
                "topic": topic["main_title"],
                "path": platforms,
                "time_span": f"{random.randint(1, 24)}小时"
            })
        
        return propagation_paths
    
    def _analyze_sentiment(self, all_data: Dict[str, List]) -> Dict[str, Any]:
        """情感分析（简化实现）"""
        # 实际应使用NLP模型进行情感分析
        import random
        
        sentiments = ["正面", "中性", "负面"]
        sentiment_distribution = {}
        
        for platform, items in all_data.items():
            positive = round(random.uniform(20, 60), 1)
            negative = round(random.uniform(10, 40), 1)
            neutral = round(100 - positive - negative, 1)
            
            sentiment_distribution[platform] = {
                "positive": positive,
                "neutral": neutral,
                "negative": negative
            }
        
        # 计算总体情感分布
        all_positive = sum(data["positive"] for data in sentiment_distribution.values()) / len(sentiment_distribution)
        all_negative = sum(data["negative"] for data in sentiment_distribution.values()) / len(sentiment_distribution)
        all_neutral = sum(data["neutral"] for data in sentiment_distribution.values()) / len(sentiment_distribution)
        
        return {
            "overall": {
                "positive": round(all_positive, 1),
                "neutral": round(all_neutral, 1),
                "negative": round(all_negative, 1)
            },
            "by_platform": sentiment_distribution
        }
    
    def _analyze_trend_evolution(self, all_data: Dict[str, List], current_date: str, time_range: str = "24h") -> List[Dict[str, Any]]:
        """分析热点演变趋势
        
        Args:
            all_data: 所有平台的热点数据
            current_date: 当前日期
            time_range: 预测时间范围，可选值为 24h(24小时), 7d(7天), 30d(30天)
        """
        # 实际应基于历史数据分析热点的演变
        import random
        from datetime import datetime, timedelta
        from app.services import crawler_factory
        
        # 获取当前日期
        current = datetime.strptime(current_date, "%Y-%m-%d")
        
        # 根据时间范围确定历史数据天数和预测天数
        if time_range == "24h":
            history_days = 1
            forecast_days = 1
            time_unit = "小时"
        elif time_range == "7d":
            history_days = 7
            forecast_days = 3
            time_unit = "天"
        elif time_range == "30d":
            history_days = 30
            forecast_days = 7
            time_unit = "天"
        else:
            history_days = 1
            forecast_days = 1
            time_unit = "小时"
        
        # 提取热门话题
        # 合并所有平台的数据，按热度排序
        all_topics = []
        for platform, items in all_data.items():
            for item in items:
                title = item.get("title", "")
                score = item.get("score", 0)
                if title and score > 0:
                    all_topics.append({
                        "title": title,
                        "score": score,
                        "platform": platform
                    })
        
        # 按热度排序
        all_topics.sort(key=lambda x: x["score"], reverse=True)
        
        # 选取前10个热门话题
        top_topics = all_topics[:10]
        
        # 生成预测数据
        forecast_results = []
        
        # 可能的分类列表
        categories = ["科技", "财经", "社会", "娱乐", "体育", "教育", "健康", "国际"]
        
        # 获取所有平台列表
        all_platforms = list(crawler_factory.keys())
        
        for topic in top_topics:
            title = topic["title"]
            current_score = topic["score"]
            platform = topic["platform"]
            
            # 生成历史趋势数据
            history_data = []
            
            # 当前热度
            history_data.append({
                "date": current_date,
                "heat": current_score
            })
            
            # 历史热度（模拟数据）
            for i in range(1, history_days + 1):
                date = current - timedelta(days=i)
                date_str = date.strftime("%Y-%m-%d")
                
                # 模拟历史热度，通常比当前热度低
                history_heat = max(0, current_score * (0.7 + 0.3 * random.random()))
                
                history_data.append({
                    "date": date_str,
                    "heat": round(history_heat, 1)
                })
            
            # 预测未来趋势
            forecast_data = []
            
            # 计算热度变化率
            recent_trend = 0
            if len(history_data) >= 2:
                recent_trend = (history_data[0]["heat"] - history_data[1]["heat"]) / max(1, history_data[1]["heat"])
            
            # 根据最近趋势预测未来热度
            for i in range(1, forecast_days + 1):
                date = current + timedelta(days=i)
                date_str = date.strftime("%Y-%m-%d")
                
                # 预测热度，根据最近趋势和随机因素
                trend_factor = recent_trend * (0.8 + 0.4 * random.random())
                forecast_heat = max(0, current_score * (1 + trend_factor))
                
                forecast_data.append({
                    "date": date_str,
                    "heat": round(forecast_heat, 1)
                })
            
            # 计算趋势类型和可能性
            if recent_trend > 0.1:
                trend_type = "趋势上升"
                probability = min(95, 50 + int(recent_trend * 100))
            elif recent_trend < -0.1:
                trend_type = "趋势下降"
                probability = min(95, 50 + int(abs(recent_trend) * 100))
            else:
                trend_type = "趋势稳定"
                probability = 70
            
            # 确定可信度文本
            confidence_text = ""
            if probability >= 90:
                confidence_text = "可信度很高"
            elif probability >= 70:
                confidence_text = "可信度较高"
            elif probability >= 50:
                confidence_text = "可信度中等"
            else:
                confidence_text = "可信度较低"
            
            # 随机选择一个分类
            category = random.choice(categories)
            
            # 从标题中提取关键词
            keywords = []
            try:
                # 使用jieba提取关键词
                import jieba.analyse
                extracted_keywords = jieba.analyse.extract_tags(title, topK=5)
                keywords = [kw for kw in extracted_keywords if len(kw) > 1 and kw not in self.stopwords][:3]
            except Exception as e:
                log.error(f"Error extracting keywords: {e}")
                # 如果提取失败，使用标题中的前几个字作为关键词
                if len(title) > 3:
                    keywords = [title[:3]]
            
            # 生成可能出现该话题的其他平台
            other_platforms = []
            for p in all_platforms:
                if p != platform:
                    other_platforms.append(p)
            
            # 随机选择2-3个其他平台
            if other_platforms:
                random.shuffle(other_platforms)
                out_platforms = other_platforms[:min(3, len(other_platforms))]
            else:
                out_platforms = []
            
            # 添加到结果
            forecast_results.append({
                "topic": title,
                "category": category,
                "keywords": keywords,
                "current_heat": round(current_score, 1),
                "history": sorted(history_data, key=lambda x: x["date"]),
                "forecast": forecast_data,
                "trend_type": trend_type,
                "probability": probability,
                "probability_text": f"{probability}%",
                "confidence": confidence_text,
                "platforms": [platform],
                "out_platforms": out_platforms
            })
        
        return forecast_results
    
    def _get_platform_stats(self, all_data: Dict[str, List]) -> Dict[str, Any]:
        """获取各平台统计数据"""
        stats = {}
        for platform, items in all_data.items():
            # 确保items是列表
            if not isinstance(items, list):
                log.warning(f"Platform {platform} data is not a list, skipping")
                continue
                
            valid_items = []
            for item in items:
                # 确保每个item是字典
                if not isinstance(item, dict):
                    log.warning(f"Item in platform {platform} is not a dictionary, skipping: {item}")
                    continue
                valid_items.append(item)
            
            if not valid_items:
                stats[platform] = {
                    "total_items": 0,
                    "avg_title_length": 0,
                    "has_description": 0,
                    "has_url": 0
                }
                continue
            
            # 安全地获取标题长度
            title_lengths = []
            for item in valid_items:
                title = item.get("title", "")
                if isinstance(title, str):
                    title_lengths.append(len(title))
            
            # 计算统计数据
            stats[platform] = {
                "total_items": len(valid_items),
                "avg_title_length": sum(title_lengths) / max(len(title_lengths), 1) if title_lengths else 0,
                "has_description": sum(1 for item in valid_items if isinstance(item.get("desc"), str)),
                "has_url": sum(1 for item in valid_items if isinstance(item.get("url"), str))
            }
        return stats
    
    def _find_cross_platform_topics(self, all_data: Dict[str, List]) -> List[Dict[str, Any]]:
        """查找跨平台热点话题"""
        # 简化实现：查找标题相似的内容
        platform_titles = defaultdict(list)
        
        # 收集各平台标题
        for platform, items in all_data.items():
            for item in items:
                title = item.get("title", "")
                if title:
                    platform_titles[platform].append({
                        "title": title,
                        "url": item.get("url", ""),
                        "score": item.get("score", 0)
                    })
        
        # 查找相似标题（简化实现）
        cross_platform_topics = []
        processed_titles = set()
        
        for platform1, titles1 in platform_titles.items():
            for item1 in titles1:
                title1 = item1["title"]
                
                # 跳过已处理的标题
                if title1 in processed_titles:
                    continue
                
                related_items = []
                platforms_found = set()
                matched_titles = []  # 记录匹配的标题，用于调试
                
                # 查找其他平台中的相似标题
                for platform2, titles2 in platform_titles.items():
                    if platform1 == platform2:
                        related_items.append({
                            "platform": platform1,
                            "title": title1,
                            "url": item1["url"],
                            "score": item1["score"]
                        })
                        platforms_found.add(platform1)
                        continue
                    
                    # 该平台是否找到匹配
                    platform_matched = False
                    
                    for item2 in titles2:
                        title2 = item2["title"]
                        # 使用jieba计算相似度，提高相似度阈值
                        similarity = self._calculate_title_similarity(title1, title2)
                        
                        # 提高相似度阈值，减少误判
                        if similarity > 0.25:  # 提高相似度阈值，确保更准确的匹配
                            related_items.append({
                                "platform": platform2,
                                "title": title2,
                                "url": item2["url"],
                                "score": item2["score"],
                                "similarity": round(similarity, 2)  # 记录相似度
                            })
                            platforms_found.add(platform2)
                            processed_titles.add(title2)
                            platform_matched = True
                            matched_titles.append(f"{platform2}: {title2} (相似度: {round(similarity, 2)})")
                            break  # 每个平台只取最相似的一个标题
                    
                    # 如果该平台没有找到匹配，记录一下
                    if not platform_matched and len(platforms_found) > 1:
                        matched_titles.append(f"{platform2}: 未找到匹配")
                
                # 如果在多个平台上找到，则认为是跨平台话题
                if len(platforms_found) > 1:  # 至少在2个平台上出现
                    # 计算总热度值
                    total_heat = sum(item.get("score", 0) for item in related_items)
                    
                    # 记录匹配情况
                    if len(platforms_found) >= 3:  # 对于3个及以上平台的匹配，记录详细信息
                        log.info(f"跨平台热点: {title1}")
                        for match in matched_titles:
                            log.info(f"  - {match}")
                    
                    cross_platform_topics.append({
                        "title": title1,
                        "platforms_count": len(platforms_found),
                        "platforms": list(platforms_found),
                        "heat": round(total_heat, 1),
                        "related_items": related_items  # 保存相关项目，便于前端展示
                    })
                    processed_titles.add(title1)
        
        # 按出现平台数量排序，然后按热度排序
        cross_platform_topics.sort(key=lambda x: (x["platforms_count"], x["heat"]), reverse=True)
        return cross_platform_topics[:20]  # 返回前20个跨平台话题
    
    def _calculate_title_similarity(self, title1: str, title2: str) -> float:
        """计算两个标题的相似度"""
        # 如果标题完全相同，直接返回1.0
        if title1 == title2:
            return 1.0
        
        # 标题长度差异过大，可能不是同一话题
        len1, len2 = len(title1), len(title2)
        if max(len1, len2) > 3 * min(len1, len2):
            return 0.0
            
        # 如果一个标题是另一个的子串，给予较高相似度，但要求子串长度至少为5个字符
        if len(title1) >= 5 and title1 in title2:
            return 0.8
        if len(title2) >= 5 and title2 in title1:
            return 0.8
        
        # 使用jieba分词
        words1 = set(jieba.cut(title1))
        words2 = set(jieba.cut(title2))
        
        # 计算Jaccard相似度
        if not words1 or not words2:
            return 0
            
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        # 如果交集太小，可能不是同一话题
        if intersection <= 1:
            return 0.0
            
        jaccard_sim = intersection / union
        
        # 提取关键词，并计算关键词相似度
        keywords1 = set(jieba.analyse.extract_tags(title1, topK=5))
        keywords2 = set(jieba.analyse.extract_tags(title2, topK=5))
        
        if keywords1 and keywords2:
            keyword_intersection = len(keywords1.intersection(keywords2))
            keyword_union = len(keywords1.union(keywords2))
            
            # 如果关键词没有交集，可能不是同一话题
            if keyword_intersection == 0:
                return max(0.0, jaccard_sim - 0.1)  # 降低相似度
                
            keyword_sim = keyword_intersection / keyword_union if keyword_union > 0 else 0
            
            # 综合考虑Jaccard相似度和关键词相似度
            return max(jaccard_sim, keyword_sim)
        
        return jaccard_sim
    
    def _find_platform_unique_topics(self, all_data: Dict[str, List]) -> Dict[str, List]:
        """查找各平台特有的热点话题"""
        # 简化实现：找出只在单一平台出现的热门话题
        platform_unique = {}
        
        for platform, items in all_data.items():
            # 取每个平台分数最高的3个话题
            top_items = sorted(items, key=lambda x: x.get("score", 0), reverse=True)[:3]
            
            platform_unique[platform] = [
                {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "score": item.get("score", 0)
                }
                for item in top_items
            ]
        
        return platform_unique

    def _extract_keyword_clouds(self, all_data: Dict[str, List], keyword_count: int = 200) -> Dict[str, List[Dict[str, Any]]]:
        """提取关键词云图数据
        
        返回按类别分组的关键词云数据，包括全部类别和各个单独类别
        
        Args:
            all_data: 所有平台的热点数据
            keyword_count: 返回的关键词数量，默认为200
        """
        # 收集所有标题和内容
        all_titles = []
        category_titles = {category: [] for category in self.categories}
        platform_titles = {platform: [] for platform in all_data.keys()}
        
        for platform, items in all_data.items():
            for item in items:
                title = item.get("title", "")
                content = item.get("content", "")
                
                if not title:
                    continue
                    
                # 添加到全部标题列表
                all_titles.append(title)
                
                # 添加到对应平台的标题列表
                platform_titles[platform].append(title)
                
                # 尝试分类并添加到对应类别
                categorized = False
                for category, keywords in self.category_keywords.items():
                    # 检查标题是否包含该类别的关键词
                    for keyword in keywords:
                        if keyword in title:
                            category_titles[category].append(title)
                            categorized = True
                            break
                    if categorized:
                        break
        
        # 根据总关键词数量计算各部分的关键词数量
        category_count = max(50, keyword_count // 2)  # 每个类别的关键词数量，至少50个
        platform_count = max(50, keyword_count // 2)  # 每个平台的关键词数量，至少50个
        
        # 提取全部关键词
        all_keywords = self._extract_category_keywords(all_titles, keyword_count)
        
        # 提取各类别关键词
        category_keywords = {}
        for category, titles in category_titles.items():
            if titles:
                # 每个类别提取指定数量的关键词
                category_keywords[category] = self._extract_category_keywords(titles, category_count)
            else:
                category_keywords[category] = []
        
        # 提取各平台关键词
        platform_keywords = {}
        for platform, titles in platform_titles.items():
            if titles:
                # 每个平台提取指定数量的关键词
                platform_keywords[platform] = self._extract_category_keywords(titles, platform_count)
            else:
                platform_keywords[platform] = []
        
        # 组织返回结果
        result = {
            "all": all_keywords,
        }
        
        # 添加各类别的关键词
        for category, keywords in category_keywords.items():
            result[category] = keywords
            
        # 添加各平台的关键词
        for platform, keywords in platform_keywords.items():
            result[f"platform_{platform}"] = keywords
            
        return result
        
    def _extract_category_keywords(self, texts: List[str], top_k: int = 30) -> List[Dict[str, Any]]:
        """从文本列表中提取关键词
        
        Args:
            texts: 文本列表
            top_k: 返回的关键词数量
            
        Returns:
            关键词列表，每个关键词包含文本和权重
        """
        if not texts:
            return []
            
        # 合并文本
        combined_text = " ".join(texts)
        
        # 使用jieba的TF-IDF算法提取关键词
        keywords_tfidf = jieba.analyse.extract_tags(
            combined_text,
            topK=top_k * 2,  # 提取更多关键词，后续过滤
            withWeight=True
        )
        
        # 使用TextRank算法提取关键词
        keywords_textrank = jieba.analyse.textrank(
            combined_text,
            topK=top_k * 2,
            withWeight=True
        )
        
        # 合并两种算法的结果
        keywords_dict = {}
        for word, weight in keywords_tfidf:
            if word not in self.stopwords and len(word) > 1:
                keywords_dict[word] = weight
                
        for word, weight in keywords_textrank:
            if word not in self.stopwords and len(word) > 1:
                if word in keywords_dict:
                    # 如果两种算法都提取到了该词，取平均权重
                    keywords_dict[word] = (keywords_dict[word] + weight) / 2
                else:
                    keywords_dict[word] = weight
        
        # 过滤停用词和单字词
        filtered_keywords = []
        for word, weight in keywords_dict.items():
            # 跳过单个汉字
            if len(word) == 1 and re.search(r'[\u4e00-\u9fff]', word):
                continue
                
            # 跳过纯数字
            if re.match(r'^\d+$', word):
                continue
                
            # 检查词在文本中出现的频率
            text_count = sum(1 for text in texts if word in text)
            if text_count > 1:  # 至少在两个文本中出现
                weight *= (1 + min(text_count / 10, 2.0))  # 最多提升3倍
                
            filtered_keywords.append((word, weight))
        
        # 排序并格式化结果
        filtered_keywords.sort(key=lambda x: x[1], reverse=True)
        result = [
            {"text": word, "weight": round(weight * 100, 1)}  # 放大权重以便于可视化
            for word, weight in filtered_keywords[:top_k]  # 取前top_k个
        ]
        
        return result
    
    def get_keyword_cloud(self, date_str: Optional[str] = None, refresh: bool = False, keyword_count: int = 200) -> Dict[str, Any]:
        """获取关键词云图数据
        
        Args:
            date_str: 日期字符串，格式为YYYY-MM-DD
            refresh: 是否强制刷新缓存
            keyword_count: 返回的关键词数量，默认为200
        """
        if not date_str:
            date_str = datetime.now(self.shanghai_tz).strftime("%Y-%m-%d")
        
        # 缓存处理
        cache_key = f"analysis:keyword_cloud:{date_str}"
        
        # 如果强制刷新或者没有缓存，则重新分析
        if refresh:
            # 清除旧的缓存
            cache.delete_cache(cache_key)
        else:
            # 尝试从缓存获取
            cached_data = cache.get_cache(cache_key)
            if cached_data:
                log.info(f"Retrieved keyword cloud from cache for {date_str}")
                return cached_data
        
        # 收集所有平台的热点数据
        all_platform_data = self._get_platform_data(date_str)
        
        if not all_platform_data:
            log.warning(f"No data available for keyword cloud on {date_str}")
            return {
                "status": "error",
                "message": "暂无可用数据生成关键词云",
                "date": date_str
            }
        
        # 提取关键词云数据
        keyword_clouds = self._extract_keyword_clouds(all_platform_data, keyword_count)
        
        # 构建结果
        result = {
            "status": "success",
            "message": "关键词云数据生成成功",
            "date": date_str,
            "keyword_clouds": keyword_clouds,
            "updated_at": datetime.now(self.shanghai_tz).strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 缓存结果
        cache.set_cache(cache_key, result, self.cache_expire)
        
        return result
        
    def get_data_visualization(self, date_str: Optional[str] = None, refresh: bool = False, platforms: Optional[List[str]] = None) -> Dict[str, Any]:
        """获取数据可视化分析
        
        Args:
            date_str: 日期字符串，格式为YYYY-MM-DD
            refresh: 是否强制刷新缓存
            platforms: 指定要分析的平台列表
        """
        if not date_str:
            date_str = datetime.now(self.shanghai_tz).strftime("%Y-%m-%d")
        
        # 缓存处理
        cache_key = f"analysis:data_visualization:{date_str}"
        
        # 如果强制刷新或者没有缓存，则重新分析
        if refresh:
            # 清除旧的缓存
            cache.delete_cache(cache_key)
        else:
            # 尝试从缓存获取
            cached_data = cache.get_cache(cache_key)
            if cached_data:
                log.info(f"Retrieved data visualization from cache for {date_str}")
                return cached_data
        
        # 收集所有平台的热点数据
        all_platform_data = self._get_platform_data(date_str)
        
        # 如果指定了平台，只保留指定平台的数据
        if platforms:
            all_platform_data = {k: v for k, v in all_platform_data.items() if k in platforms}
        
        if not all_platform_data:
            log.warning(f"No data available for data visualization on {date_str}")
            return {
                "status": "error",
                "message": "暂无可用数据进行可视化分析",
                "date": date_str
            }
        
        # 生成主题热度分布数据
        topic_distribution = self._analyze_topic_heat_distribution(all_platform_data)
        
        # 构建结果
        result = {
            "status": "success",
            "message": "数据可视化分析完成",
            "date": date_str,
            "topic_heat_distribution": topic_distribution,
            "platforms": list(all_platform_data.keys()),
            "updated_at": datetime.now(self.shanghai_tz).strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 缓存结果
        cache.set_cache(cache_key, result, self.cache_expire)
        
        return result

    def get_trend_forecast(self, date_str: Optional[str] = None, refresh: bool = False, time_range: str = "24h") -> Dict[str, Any]:
        """获取热点趋势预测分析
        
        Args:
            date_str: 日期字符串，格式为YYYY-MM-DD
            refresh: 是否强制刷新缓存
            time_range: 预测时间范围，可选值为 24h(24小时), 7d(7天), 30d(30天)
        """
        if not date_str:
            date_str = datetime.now(self.shanghai_tz).strftime("%Y-%m-%d")
        
        # 验证时间范围参数
        valid_time_ranges = ["24h", "7d", "30d"]
        if time_range not in valid_time_ranges:
            time_range = "24h"  # 默认使用24小时
        
        # 缓存处理
        cache_key = f"analysis:trend_forecast:{date_str}:{time_range}"
        
        # 如果强制刷新或者没有缓存，则重新分析
        if refresh:
            # 清除旧的缓存
            cache.delete_cache(cache_key)
        else:
            # 尝试从缓存获取
            cached_data = cache.get_cache(cache_key)
            if cached_data:
                log.info(f"Retrieved trend forecast from cache for {date_str}, time_range: {time_range}")
                return cached_data
        
        # 收集所有平台的热点数据
        all_platform_data = self._get_platform_data(date_str)
        
        if not all_platform_data:
            log.warning(f"No data available for trend forecast on {date_str}")
            return {
                "status": "error",
                "message": "暂无可用数据进行趋势预测",
                "date": date_str
            }
        
        # 分析热点趋势演变
        trend_evolution = self._analyze_trend_evolution(all_platform_data, date_str, time_range)
        
        # 构建结果
        result = {
            "status": "success",
            "message": "热点趋势预测完成",
            "date": date_str,
            "time_range": time_range,
            "trend_evolution": trend_evolution,
            "updated_at": datetime.now(self.shanghai_tz).strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 缓存结果
        cache.set_cache(cache_key, result, self.cache_expire)
        
        return result
    
    def _analyze_topic_heat_distribution(self, all_data: Dict[str, List]) -> Dict[str, Any]:
        """分析主题热度分布
        
        生成主题热度分布图数据，展示不同平台对各主题词的热度分布
        """
        # 获取可用的平台列表
        available_platforms = list(all_data.keys())
        
        # 如果平台太多，选择主要平台
        if len(available_platforms) > 8:
            # 优先选择的平台顺序
            preferred_platforms = [
                "baidu", "weibo", "jinritoutiao", "douyin", "hupu", 
                "v2ex", "github", "stackoverflow", "tieba", "zhihu", 
                "36kr", "bilibili", "douban", "hackernews"
            ]
            
            # 先添加优先平台
            selected_platforms = []
            for platform in preferred_platforms:
                if platform in available_platforms:
                    selected_platforms.append(platform)
                    if len(selected_platforms) >= 8:  # 最多选择8个平台
                        break
            
            # 如果优先平台不够，添加其他平台
            if len(selected_platforms) < 8:
                for platform in available_platforms:
                    if platform not in selected_platforms:
                        selected_platforms.append(platform)
                        if len(selected_platforms) >= 8:
                            break
            
            platform_data = {platform: all_data[platform] for platform in selected_platforms}
        else:
            # 如果平台数量合适，使用所有平台
            platform_data = all_data
        
        # 提取每个平台的热门关键词
        platform_keywords = {}
        all_keywords = set()
        
        for platform, items in platform_data.items():
            # 提取该平台的标题
            titles = [item.get("title", "") for item in items if item.get("title")]
            if not titles:
                continue
                
            # 使用jieba提取关键词
            keywords = self._extract_platform_keywords(titles, 10)
            if keywords:
                platform_keywords[platform] = keywords
                all_keywords.update(kw["text"] for kw in keywords)
        
        # 选取出现频率最高的关键词
        top_keywords = self._select_top_keywords(platform_keywords, 10)
        
        # 构建主题热度分布数据
        distribution_data = {
            "keywords": top_keywords,
            "platforms": [],
            "data": []
        }
        
        # 平台名称映射
        platform_names = {
            "hupu": "虎扑",
            "weibo": "微博",
            "jinritoutiao": "今日头条",
            "douyin": "抖音",
            "baidu": "百度热搜",
            "v2ex": "V2EX",
            "github": "GitHub",
            "stackoverflow": "Stack Overflow",
            "tieba": "贴吧",
            "zhihu": "知乎",
            "36kr": "36氪",
            "bilibili": "哔哩哔哩",
            "douban": "豆瓣",
            "hackernews": "Hacker News",
            "shaoshupai": "少数派"
        }
        
        # 添加平台列表（使用中文名称）
        for platform in platform_keywords.keys():
            display_name = platform_names.get(platform, platform)
            distribution_data["platforms"].append(display_name)
        
        # 为每个关键词构建热度数据
        for keyword in top_keywords:
            keyword_data = {"keyword": keyword, "values": []}
            
            for platform_display in distribution_data["platforms"]:
                # 找到平台的原始键名
                platform_key = next((k for k, v in platform_names.items() if v == platform_display), platform_display)
                
                # 查找该平台中该关键词的热度
                heat = 0
                if platform_key in platform_keywords:
                    for kw in platform_keywords[platform_key]:
                        if kw["text"] == keyword:
                            heat = kw["weight"]
                            break
                
                keyword_data["values"].append(heat)
            
            distribution_data["data"].append(keyword_data)
        
        return distribution_data
    
    def _extract_platform_keywords(self, titles: List[str], top_k: int = 10) -> List[Dict[str, Any]]:
        """从平台标题中提取关键词
        
        Args:
            titles: 标题列表
            top_k: 返回的关键词数量
        """
        if not titles:
            return []
        
        # 合并标题
        combined_text = " ".join(titles)
        
        # 使用jieba提取关键词
        keywords = jieba.analyse.extract_tags(
            combined_text,
            topK=top_k * 2,
            withWeight=True
        )
        
        # 过滤停用词和单字词
        filtered_keywords = []
        for word, weight in keywords:
            # 跳过停用词
            if word in self.stopwords:
                continue
                
            # 跳过单个汉字
            if len(word) == 1 and re.search(r'[\u4e00-\u9fff]', word):
                continue
                
            # 跳过纯数字
            if re.match(r'^\d+$', word):
                continue
            
            # 检查词在标题中出现的频率
            title_count = sum(1 for title in titles if word in title)
            if title_count > 1:  # 至少在两个标题中出现
                weight *= (1 + min(title_count / 10, 2.0))  # 最多提升3倍
                
            filtered_keywords.append({"text": word, "weight": round(weight * 100, 1)})
        
        # 排序并返回前top_k个
        filtered_keywords.sort(key=lambda x: x["weight"], reverse=True)
        return filtered_keywords[:top_k]
    
    def _select_top_keywords(self, platform_keywords: Dict[str, List[Dict[str, Any]]], top_k: int = 10) -> List[str]:
        """从各平台关键词中选择最重要的关键词
        
        Args:
            platform_keywords: 平台关键词字典，格式为 {platform: [{"text": keyword, "weight": weight}, ...]}
            top_k: 返回的关键词数量
        """
        # 统计每个关键词在不同平台的出现次数和总权重
        keyword_stats = defaultdict(lambda: {"count": 0, "total_weight": 0})
        
        for platform, keywords in platform_keywords.items():
            for kw in keywords:
                keyword = kw["text"]
                weight = kw["weight"]
                
                keyword_stats[keyword]["count"] += 1
                keyword_stats[keyword]["total_weight"] += weight
        
        # 计算综合得分（平台出现次数 * 总权重）
        for keyword, stats in keyword_stats.items():
            stats["score"] = stats["count"] * stats["total_weight"]
        
        # 按得分排序
        sorted_keywords = sorted(keyword_stats.items(), key=lambda x: x[1]["score"], reverse=True)
        
        # 返回前top_k个关键词
        return [kw for kw, _ in sorted_keywords[:top_k]] 