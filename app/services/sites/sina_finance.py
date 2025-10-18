import json
import datetime
import requests
import urllib3
from ...core import cache
from .crawler import Crawler

urllib3.disable_warnings()


class SinaFinanceCrawler(Crawler):
    def fetch(self, date_str):
        current_time = datetime.datetime.now()
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Referer': 'https://finance.sina.com.cn/',
                'Origin': 'https://finance.sina.com.cn'
            }
            
            response = requests.get(
                "https://zhibo.sina.com.cn/api/zhibo/feed?page=1&page_size=20&zhibo_id=152&tag_id=0&dire=f&dpc=1&pagesize=20",
                headers=headers,
                timeout=self.timeout,
                verify=False
            )
            response.raise_for_status()
            
            data = response.json()
            if data.get('result', {}).get('status', {}).get('code') != 0:
                return []
            
            feed_list = data.get('result', {}).get('data', {}).get('feed', {}).get('list', [])
            result = []
            cache_list = []
            
            for item in feed_list:
                try:
                    title = item.get('rich_text', '').strip()
                    if not title:
                        continue
                    
                    ext_str = item.get('ext', '{}')
                    try:
                        ext_data = json.loads(ext_str)
                        doc_url = ext_data.get('docurl', '')
                    except:
                        doc_url = item.get('docurl', '').strip(' "')
                    
                    news = {
                        'title': title,
                        'url': doc_url,
                        'content': title,
                        'source': 'sina_finance',
                        'publish_time': current_time.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    result.append(news)
                    cache_list.append(news)
                    
                except Exception:
                    continue
            
            if cache_list:
                cache._hset(date_str, self.crawler_name(), json.dumps(cache_list, ensure_ascii=False))
            return result
        except Exception as e:
            return []
    
    def crawler_name(self):
        return "sina_finance"