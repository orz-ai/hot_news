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


class ZhiHuCrawler(Crawler):
    """知乎"""

    def fetch(self, date_str):
        # 获取当前时间
        current_time = datetime.datetime.now()
        
        url = "https://www.zhihu.com/api/v3/explore/guest/feeds?limit=30&ws_qiangzhisafe=0"
        
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
                target = item.get('target', {})
                question = target.get('question', {})
                title = question.get('title', '')
                url = f"https://www.zhihu.com/question/{question.get('id')}"
                excerpt = target.get('excerpt', '')
                
                news = {
                    'title': title,
                    'url': url,
                    'content': excerpt,
                    'source': 'zhihu',
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
        return "zhihu"
