import json
import datetime
import time

import requests
import urllib3

from .crawler import Crawler
from ...core import cache

urllib3.disable_warnings()


class TsKrCrawler(Crawler):
    """36氪"""
    
    def fetch(self, date_str):
        """
        获取36氪热榜数据
        """
        current_time = datetime.datetime.now()
        url = f"https://gateway.36kr.com/api/mis/nav/home/nav/rank/hot"
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
        }

        body = {
            "partner_id": "wap",
            "param": {
                "siteId": 1,
                "platformId": 2,
            },
            "timestamp": int(time.time() * 1000),
        }
        
        try:
            resp = requests.post(
                url=url,
                headers=headers,
                json=body,
                verify=False,
                timeout=self.timeout
            )
            
            if resp.status_code != 200:
                print(f"request failed, status: {resp.status_code}")
                return []
            
            json_data = resp.json()
            data_key = "hotRankList"
            data_list = json_data.get("data", {}).get(data_key, [])
            
            result = []
            cache_list = []
            
            for item in data_list:
                template_material = item.get("templateMaterial", {})
                item_id = item.get("itemId", "")
                
                title = template_material.get("widgetTitle", "")
                article_url = f"https://www.36kr.com/p/{item_id}"

                news = {
                    'title': title,
                    'url': article_url,
                    'content': title,
                    'source': '36kr',
                    'publish_time': current_time.strftime('%Y-%m-%d %H:%M:%S'),
                }

                result.append(news)
                cache_list.append(news)
            
            cache.hset(date_str, self.crawler_name(), json.dumps(cache_list, ensure_ascii=False))
            return result
            
        except Exception as e:
            print(f"Error fetching 36kr data: {e}")
            return []
        
    def crawler_name(self):
        return "36kr"
