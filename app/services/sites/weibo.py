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


class WeiboCrawler(Crawler):
    """微博"""

    def fetch(self, date_str):
        # 获取当前时间
        current_time = datetime.datetime.now()

        header = self.header.copy()
        header.update({
            "accept": "application/json, text/javascript, */*; q=0.01",
            "host": "weibo.com",
            "Referer": "https://weibo.com",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        })
        
        url = "https://weibo.com/ajax/side/hotSearch"
        
        resp = requests.get(url=url, headers=header, verify=False, timeout=self.timeout)
        if resp.status_code != 200:
            print(f"request failed, status: {resp.status_code}")
            return []
            
        try:
            json_data = resp.json()
            data = json_data.get('data', {}).get('realtime', [])
            
            result = []
            cache_list = []
            
            for item in data:
                title = item.get('word', '')
                url = f"https://s.weibo.com/weibo?q=%23{title}%23"

                news = {
                    'title': title,
                    'url': url,
                    'content': title,
                    'source': 'weibo',
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
        return "weibo"
