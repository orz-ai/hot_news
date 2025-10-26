import json
import datetime  # 添加datetime导入

import requests
import urllib3
from bs4 import BeautifulSoup
# 移除 SQLAlchemy 导入
# from sqlalchemy.sql.functions import now

from ...core import cache
from .crawler import Crawler

urllib3.disable_warnings()


class ShaoShuPaiCrawler(Crawler):
    """少数派"""
    def fetch(self, date_str):
        current_time = datetime.datetime.now()
        
        url = "https://sspai.com/api/v1/article/index/page/get?limit=20&offset=0&created_at=0"
        
        resp = requests.get(url=url, headers=self.header, verify=False, timeout=self.timeout)
        if resp.status_code != 200:
            print(f"request failed, status: {resp.status_code}")
            return []
            
        try:
            json_data = resp.json()
            data = json_data.get('data', [])
            
            result = []
            cache_list = []
            
            for item in data:
                title = item.get('title', '')
                article_id = item.get('id', '')
                url = f"https://sspai.com/post/{article_id}"
                summary = item.get('summary', '')
                
                news = {
                    'title': title,
                    'url': url,
                    'content': summary,
                    'source': 'sspai',
                    'publish_time': current_time.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                result.append(news)
                cache_list.append(news)
                
            cache.hset(date_str, self.crawler_name(), json.dumps(cache_list, ensure_ascii=False))
            return result
            
        except Exception as e:
            print(f"Error parsing JSON: {e}")
            return []
        
    def crawler_name(self):
        return "shaoshupai"
