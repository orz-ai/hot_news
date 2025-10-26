import json
import datetime  # 添加datetime导入
import re

import requests
import urllib3
from bs4 import BeautifulSoup
# 移除 SQLAlchemy 导入
# from sqlalchemy.sql.functions import now

from ...core import cache
from ...db.mysql import News
from .crawler import Crawler

urllib3.disable_warnings()


class HuPuCrawler(Crawler):
    """虎扑"""

    def fetch(self, date_str):
        # 获取当前时间
        current_time = datetime.datetime.now()
        
        url = "https://bbs.hupu.com/all-gambia"
        
        resp = requests.get(url=url, headers=self.header, verify=False, timeout=self.timeout)
        if resp.status_code != 200:
            print(f"request failed, status: {resp.status_code}")
            return []
            
        html_text = resp.text
        soup = BeautifulSoup(html_text, "html.parser")
        
        # 找到热门帖子列表
        post_list = soup.find_all('div', class_='t-info')
        
        result = []
        cache_list = []
        
        for post in post_list:
            title_elem = post.find('span', class_='t-title')
            if not title_elem:
                continue
                
            link_elem = post.find('a')
            if not link_elem:
                continue

            title = title_elem.text.strip()
            url = "https://bbs.hupu.com" + link_elem.get('href') if link_elem.get('href').startswith('/') else link_elem.get('href')
            
            # 获取帖子信息
            info_elem = post.find('span', class_='t-replies')
            info = info_elem.text.strip() if info_elem else ""
            
            news = {
                'title': title,
                'url': url,
                'content': info,
                'source': 'hupu',
                'publish_time': current_time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            result.append(news)
            cache_list.append(news)
            
        cache.hset(date_str, self.crawler_name(), json.dumps(cache_list, ensure_ascii=False))
        return result

    def crawler_name(self):
        return "hupu"
