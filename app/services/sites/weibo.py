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

    def fetch(self, date_str):
        # 获取当前时间
        current_time = datetime.datetime.now()
        
        url = "https://weibo.com/ajax/side/hotSearch"
        
        resp = requests.get(url=url, headers=self.header, verify=False, timeout=self.timeout)
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
                hot = item.get('num', 0)
                
                news = {
                    'title': title,
                    'url': url,
                    'content': f"热度: {hot}",
                    'source': 'weibo',
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
        return "weibo"
