import json
import datetime
import requests
import urllib3

from .crawler import Crawler
from ...core import cache

urllib3.disable_warnings()


class CLSCrawler(Crawler):
    """财联社"""
    
    def fetch(self, date_str) -> list:
        current_time = datetime.datetime.now()
        
        try:
            params = {
                'app': 'CailianpressWeb',
                'os': 'web',
                'sv': '8.4.6',
                'sign': '9f8797a1f4de66c2370f7a03990d2737'
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Referer': 'https://www.cls.cn/',
                'Origin': 'https://www.cls.cn'
            }
            
            response = requests.get(
                "https://www.cls.cn/featured/v1/column/list",
                params=params,
                headers=headers,
                timeout=self.timeout,
                verify=False
            )
            response.raise_for_status()
            
            data = response.json()
            if data.get('errno') != 0:
                return []
            
            column_list = data.get('data', {}).get('column_list', [])
            
            result = []
            cache_list = []
            
            for idx, column in enumerate(column_list[:20]):
                try:
                    title = column.get('title', '').strip()
                    if not title or len(title) < 2:
                        continue
                    
                    article_list = column.get('article_list', {})
                    if article_list:
                        article_title = article_list.get('title', '').strip()
                        jump_url = article_list.get('jump_url', '').strip()
                        brief = article_list.get('brief', '').strip()
                        
                        if article_title:
                            display_title = f"[{title}] {article_title}"
                            content = brief if brief else article_title
                            url = jump_url if jump_url else f"https://www.cls.cn/featured"
                        else:
                            display_title = title
                            content = column.get('brief', '').strip()
                            url = f"https://www.cls.cn/featured"
                    else:
                        display_title = title
                        content = column.get('brief', '').strip()
                        url = f"https://www.cls.cn/featured"
                    
                    news = {
                        'title': display_title,
                        'url': url,
                        'content': content,
                        'source': 'cls',
                        'publish_time': current_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'score': 1000 - idx,
                        'rank': idx + 1
                    }
                    
                    result.append(news)
                    cache_list.append(news)
                    
                except Exception:
                    continue
            
            if cache_list:
                cache.hset(date_str, self.crawler_name(), json.dumps(cache_list, ensure_ascii=False))
            return result
        except Exception as e:
            return []

    def crawler_name(self):
        return "cls"