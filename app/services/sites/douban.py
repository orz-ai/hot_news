import json
import re
import datetime  # 添加datetime导入

import requests
import urllib3
from bs4 import BeautifulSoup
# 移除 SQLAlchemy 导入
# from sqlalchemy.sql.functions import now

from ...core import cache
from ...db.mysql import News
from .crawler import Crawler

urllib3.disable_warnings()


class DouBanCrawler(Crawler):

    def fetch(self, date_str):
        # 获取当前时间
        current_time = datetime.datetime.now()
        
        url = "https://www.douban.com/group/explore"

        header = self.header.copy()
        header.update({
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-encoding": "",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
            "host": "www.douban.com",
            "referer": "https://www.douban.com/group/explore",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
        })

        resp = requests.get(url=url, headers=header, verify=False, timeout=self.timeout)
        if resp.status_code != 200:
            print(f"request failed, status: {resp.status_code}")
            return []
            
        html_text = resp.text
        soup = BeautifulSoup(html_text, "html.parser")
        
        # 找到热门话题列表
        topic_list = soup.find_all('div', class_='channel-item')
        
        result = []
        cache_list = []
        
        for topic in topic_list:
            title_elem = topic.find('h3')
            if not title_elem:
                continue
                
            link_elem = title_elem.find('a')
            if not link_elem:
                continue
                
            title = link_elem.text.strip()
            url = link_elem.get('href')
            
            # 获取话题描述
            desc_elem = topic.find('div', class_='content')
            desc = desc_elem.text.strip() if desc_elem else ""
            
            news = {
                'title': title,
                'url': url,
                'content': desc,
                'source': 'douban',
                'publish_time': current_time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            result.append(news)
            cache_list.append(news)
            
        cache._hset(date_str, self.crawler_name(), json.dumps(cache_list, ensure_ascii=False))
        return result

    def crawler_name(self):
        return "douban"
