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


class FtPoJieCrawler(Crawler):

    def fetch(self, date_str):
        # 获取当前时间
        current_time = datetime.datetime.now()
        
        url = "https://www.52pojie.cn/forum.php?mod=guide&view=hot"
        
        resp = requests.get(url=url, headers=self.header, verify=False, timeout=self.timeout)
        if resp.status_code != 200:
            print(f"request failed, status: {resp.status_code}")
            return []
            
        resp.encoding = 'gbk'  # 52pojie使用GBK编码
        html_text = resp.text
        soup = BeautifulSoup(html_text, "html.parser")
        
        # 找到热门帖子列表
        hot_threads = soup.find_all('tbody', id=lambda x: x and x.startswith('normalthread_'))
        
        result = []
        cache_list = []
        
        for thread in hot_threads:
            title_elem = thread.find('a', class_='xst')
            if not title_elem:
                continue
                
            title = title_elem.text.strip()
            url = "https://www.52pojie.cn/" + title_elem.get('href')
            
            # 获取帖子信息
            info_elem = thread.find('td', class_='by')
            info = info_elem.text.strip() if info_elem else ""
            
            news = {
                'title': title,
                'url': url,
                'content': info,
                'source': '52pojie',
                'publish_time': current_time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            result.append(news)
            cache_list.append(news)
            
        cache._hset(date_str, self.crawler_name(), json.dumps(cache_list, ensure_ascii=False))
        return result

    def crawler_name(self):
        return "52pojie"
