import json
import datetime
import requests
import urllib3

from .crawler import Crawler
from ...core import cache

urllib3.disable_warnings()


class EastMoneyCrawler(Crawler):
    """东方财富网"""

    def fetch(self, date_str) -> list:
        current_time = datetime.datetime.now()

        try:
            params = {
                'client': 'web',
                'biz': 'web_724',
                'fastColumn': '102',
                'sortEnd': '',
                'pageSize': '50',
                'req_trace': str(int(current_time.timestamp() * 1000))  # 使用当前时间戳
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Referer': 'https://kuaixun.eastmoney.com/',
                'Origin': 'https://kuaixun.eastmoney.com'
            }
            
            response = requests.get(
                "https://np-weblist.eastmoney.com/comm/web/getFastNewsList",
                params=params,
                headers=headers,
                timeout=self.timeout,
                verify=False
            )
            response.raise_for_status()
            
            data = response.json()
            if data.get('code') != '1':
                return []
            fast_news_list = data.get('data', {}).get('fastNewsList', [])
            
            result = []
            cache_list = []
            
            for idx, news_item in enumerate(fast_news_list[:20]):  # 取前20条
                try:
                    title = news_item.get('title', '').strip()
                    if not title:
                        continue
                    
                    summary = news_item.get('summary', '').strip()
                    show_time = news_item.get('showTime', '').strip()
                    code = news_item.get('code', '').strip()
                    url = f"https://finance.eastmoney.com/a/{code}" if code else "https://kuaixun.eastmoney.com/"
                    
                    news = {
                        'title': title,
                        'url': url,
                        'content': summary,
                        'source': 'eastmoney',
                        'publish_time': show_time if show_time else current_time.strftime('%Y-%m-%d %H:%M:%S'),
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
        return "eastmoney"