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


class TieBaCrawler(Crawler):

    def fetch(self, date_str):
        # 获取当前时间
        current_time = datetime.datetime.now()
        
        url = "http://tieba.baidu.com/hottopic/browse/topicList"
        
        resp = requests.get(url=url, headers=self.header, verify=False, timeout=self.timeout)
        if resp.status_code != 200:
            print(f"request failed, status: {resp.status_code}")
            return []
            
        try:
            json_data = resp.json()
            data = json_data.get('data', {}).get('bang_topic', {}).get('topic_list', [])
            
            result = []
            cache_list = []
            
            for item in data:
                title = item.get('topic_name', '')
                url = item.get('topic_url', '')
                if url and not url.startswith('http'):
                    url = f"http://tieba.baidu.com{url}"
                
                desc = item.get('topic_desc', '')
                
                news = {
                    'title': title,
                    'url': url,
                    'content': desc,
                    'source': 'tieba',
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
        return "tieba"
