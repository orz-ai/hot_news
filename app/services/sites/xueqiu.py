import json
import datetime
import requests
import urllib3
import re
from requests.sessions import Session

from .crawler import Crawler
from ...core import cache

urllib3.disable_warnings()


class XueqiuCrawler(Crawler):
    """雪球"""
    def __init__(self):
        super().__init__()
        self.session = Session()
        self._init_session()
    
    def _init_session(self):
        try:
            # 第一步：访问主页获取基础cookies
            main_url = "https://xueqiu.com"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1'
            }
            
            resp = self.session.get(main_url, headers=headers, verify=False, timeout=self.timeout)
            if resp.status_code == 200:
                html_content = resp.text
                
                # 尝试提取token
                token_match = re.search(r'window\.SNB\s*=\s*\{[^}]*token["\']?\s*:\s*["\']([^"\']+)["\']', html_content)
                if token_match:
                    token = token_match.group(1)
                    self.session.headers.update({'X-Requested-With': 'XMLHttpRequest'})
                
                hot_page_url = "https://xueqiu.com/hot_event"
                hot_headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                    'Referer': 'https://xueqiu.com/',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'same-origin',
                    'Sec-Fetch-User': '?1',
                    'Upgrade-Insecure-Requests': '1'
                }
                
                hot_resp = self.session.get(hot_page_url, headers=hot_headers, verify=False, timeout=self.timeout)
                if hot_resp.status_code == 200:
                    print("雪球热门页面访问成功，已获取完整认证信息")
                else:
                    print(f"雪球热门页面访问失败: {hot_resp.status_code}")
                    
            else:
                print(f"雪球主页访问失败: {resp.status_code}")
                
        except Exception as e:
            print(f"初始化雪球会话失败: {e}")

    def fetch(self, date_str) -> list:
        current_time = datetime.datetime.now()
        
        url = "https://xueqiu.com/hot_event/list.json?count=10"
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Referer': 'https://xueqiu.com/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        try:
            resp = self.session.get(url=url, headers=headers, verify=False, timeout=self.timeout)
            
            if resp.status_code != 200:
                print(f"雪球请求失败, status: {resp.status_code}")
                self._init_session()
                resp = self.session.get(url=url, headers=headers, verify=False, timeout=self.timeout)
                if resp.status_code != 200:
                    print(f"雪球重试后仍失败, status: {resp.status_code}")
                    return []

            json_data = resp.json()
            if 'list' not in json_data:
                print("雪球响应格式异常")
                return []
                
            result = []
            cache_list = []
            
            for idx, item in enumerate(json_data['list'][:10]):  # 取前10条
                try:
                    tag = item.get('tag', '').strip()
                    if tag.startswith('#') and tag.endswith('#'):
                        title = tag[1:-1]
                    else:
                        title = tag
                    
                    if not title:
                        continue
                    
                    item_id = item.get('id')
                    url_link = f"https://xueqiu.com/"
                    
                    content = item.get('content', '').strip()
                    if len(content) > 200:
                        content = content[:200] + '...'
                    
                    status_count = item.get('status_count', 0)
                    hot_value = item.get('hot', 0)
                    
                    news = {
                        'title': title,
                        'url': url_link,
                        'content': content,
                        'source': 'xueqiu',
                        'publish_time': current_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'score': status_count if status_count > 0 else 1000 - idx,
                        'rank': idx + 1
                    }
                    result.append(news)
                    cache_list.append(news)
                    
                except Exception as e:
                    print(f"解析雪球新闻项失败: {e}")
                    continue

            cache.hset(date_str, self.crawler_name(), json.dumps(cache_list, ensure_ascii=False))
            return result
            
        except Exception as e:
            print(f"获取雪球数据失败: {e}")
            return []

    def crawler_name(self):
        return "xueqiu"