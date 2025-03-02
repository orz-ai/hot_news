import json
import datetime

import requests
import urllib3
from bs4 import BeautifulSoup

from .crawler import Crawler
from ...core import cache
from ...db.mysql import News

urllib3.disable_warnings()


class BilibiliCrawler(Crawler):

    def fetch(self, date_str):
        current_time = datetime.datetime.now()
        
        url = "https://www.bilibili.com/v/popular/rank/all"
        
        resp = requests.get(url=url, headers=self.header, verify=False, timeout=self.timeout)
        if resp.status_code != 200:
            print(f"request failed, status: {resp.status_code}")
            return []
            
        html_text = resp.text
        soup = BeautifulSoup(html_text, "html.parser")
        
        rank_list = soup.find('ul', class_='rank-list')
        if not rank_list:
            return []
            
        items = rank_list.find_all('li', class_='rank-item')
        
        result = []
        cache_list = []
        
        for item in items:
            title_elem = item.find('a', class_='title')
            if not title_elem:
                continue
                
            title = title_elem.text.strip()
            url = "https:" + title_elem.get('href') if title_elem.get('href').startswith('//') else title_elem.get('href')
            
            desc_elem = item.find('div', class_='detail')
            desc = desc_elem.text.strip() if desc_elem else ""
            
            news = {
                'title': title,
                'url': url,
                'content': desc,
                'source': 'bilibili',
                'publish_time': current_time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            result.append(news)
            cache_list.append(news)
            
        cache._hset(date_str, self.crawler_name(), json.dumps(cache_list, ensure_ascii=False))
        return result

    def crawler_name(self):
        return "bilibili"
