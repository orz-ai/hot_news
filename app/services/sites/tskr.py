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

class TsKrCrawler(Crawler):
    def fetch(self, date_str):
        # 获取当前时间
        current_time = datetime.datetime.now()
        
        url = "https://36kr.com/hot-list/catalog"
        
        resp = requests.get(url=url, headers=self.header, verify=False, timeout=self.timeout)
        if resp.status_code != 200:
            print(f"request failed, status: {resp.status_code}")
            return []
            
        html_text = resp.text
        soup = BeautifulSoup(html_text, "html.parser")
        
        # 找到热门文章列表
        article_list = soup.find_all('div', class_='article-wrapper')
        if not article_list:
            return []
        
        result = []
        cache_list = []
        
        for article in article_list:
            title_elem = article.find('a', class_='article-item-title')
            if not title_elem:
                continue
                
            title = title_elem.text.strip()
            url = "https://36kr.com" + title_elem.get('href') if title_elem.get('href').startswith('/') else title_elem.get('href')
            
            # 获取文章摘要
            desc_elem = article.find('a', class_='article-item-description')
            desc = desc_elem.text.strip() if desc_elem else ""
            
            news = {
                'title': title,
                'url': url,
                'content': desc,
                'source': '36kr',
                'publish_time': current_time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            result.append(news)
            cache_list.append(news)
            
        cache._hset(date_str, self.crawler_name(), json.dumps(cache_list, ensure_ascii=False))
        return result
        
    def crawler_name(self):
        return "36kr"
