import json
import datetime  # 添加datetime导入
import re

import requests
from bs4 import BeautifulSoup
# 移除 SQLAlchemy 导入
# from sqlalchemy.sql.functions import now

from ...core import cache
from ...db.mysql import News
from .crawler import Crawler
import urllib3
urllib3.disable_warnings()


class DouYinCrawler(Crawler):

    def fetch(self, date_str):
        # 获取当前时间
        current_time = datetime.datetime.now()
        
        # 抖音热榜API
        url = "https://www.douyin.com/hot"
        
        resp = requests.get(url=url, headers=self.header, verify=False, timeout=self.timeout)
        if resp.status_code != 200:
            print(f"request failed, status: {resp.status_code}")
            return []
            
        html_text = resp.text
        soup = BeautifulSoup(html_text, "html.parser")
        
        # 找到热榜列表
        hot_items = soup.find_all('div', class_='recommend-item')
        
        result = []
        cache_list = []
        
        for item in hot_items:
            title_elem = item.find('p', class_='title')
            if not title_elem:
                continue
                
            title = title_elem.text.strip()
            
            # 获取链接
            link_elem = item.find('a')
            url = "https://www.douyin.com" + link_elem.get('href') if link_elem else "https://www.douyin.com/hot"
            
            # 获取热度
            hot_elem = item.find('span', class_='hot-count')
            hot = hot_elem.text.strip() if hot_elem else ""
            
            news = {
                'title': title,
                'url': url,
                'content': f"热度: {hot}",
                'source': 'douyin',
                'publish_time': current_time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            result.append(news)
            cache_list.append(news)
            
        cache._hset(date_str, self.crawler_name(), json.dumps(cache_list, ensure_ascii=False))
        return result

    def crawler_name(self):
        return "douyin"


