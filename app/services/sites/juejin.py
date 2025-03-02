import json
import datetime  # 添加datetime导入

import requests
import urllib3
from bs4 import BeautifulSoup
# 移除 SQLAlchemy 导入
# from sqlalchemy.sql.functions import now

from .crawler import Crawler
from ...core import cache
from ...db.mysql import News

urllib3.disable_warnings()


class JueJinCrawler(Crawler):

    def fetch(self, date_str):
        # 获取当前时间
        current_time = datetime.datetime.now()
        
        url = "https://api.juejin.cn/recommend_api/v1/article/recommend_all_feed"
        
        payload = {
            "id_type": 2,
            "client_type": 2608,
            "sort_type": 3,
            "cursor": "0",
            "limit": 20
        }
        
        resp = requests.post(url=url, json=payload, headers=self.header, verify=False, timeout=self.timeout)
        if resp.status_code != 200:
            print(f"request failed, status: {resp.status_code}")
            return []
            
        try:
            json_data = resp.json()
            data = json_data.get('data', [])
            
            result = []
            cache_list = []
            
            for item in data:
                article_info = item.get('article_info', {})
                title = article_info.get('title', '')
                article_id = article_info.get('article_id', '')
                url = f"https://juejin.cn/post/{article_id}"
                brief = article_info.get('brief_content', '')
                
                news = {
                    'title': title,
                    'url': url,
                    'content': brief,
                    'source': 'juejin',
                    'publish_time': current_time.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                result.append(news)
                cache_list.append(news)
                
            cache._hset(date_str, self.crawler_name(), json.dumps(cache_list, ensure_ascii=False))
            return result
            
        except Exception as e:
            print(f"Error parsing JSON: {e}")
            return []

    def crawler_name(self):
        return "juejin"
