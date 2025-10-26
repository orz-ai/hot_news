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


class VtexCrawler(Crawler):
    """v2ex"""

    def fetch(self, date_str):
        # 获取当前时间
        current_time = datetime.datetime.now()
        
        url = "https://www.v2ex.com/?tab=hot"
        
        resp = requests.get(url=url, headers=self.header, verify=False, timeout=self.timeout)
        if resp.status_code != 200:
            print(f"request failed, status: {resp.status_code}")
            return []
            
        html_text = resp.text
        soup = BeautifulSoup(html_text, "html.parser")
        
        # 找到热门话题列表
        topic_list = soup.find_all('div', class_='cell item')
        
        result = []
        cache_list = []
        
        for topic in topic_list:
            title_elem = topic.find('span', class_='item_title')
            if not title_elem:
                continue
                
            link_elem = title_elem.find('a')
            if not link_elem:
                continue
                
            title = link_elem.text.strip()
            url = "https://www.v2ex.com" + link_elem.get('href')
            
            # 获取话题信息
            info_elem = topic.find('span', class_='topic_info')
            info = info_elem.text.strip() if info_elem else ""
            
            news = {
                'title': title,
                'url': url,
                'content': info,
                'source': 'v2ex',
                'publish_time': current_time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            result.append(news)
            cache_list.append(news)
            
        cache.hset(date_str, self.crawler_name(), json.dumps(cache_list, ensure_ascii=False))
        return result

    def crawler_name(self):
        return "v2ex"
