import json
import datetime

import requests
import urllib3

from .crawler import Crawler
from ...core import cache
from ...db.mysql import News

urllib3.disable_warnings()


class BilibiliCrawler(Crawler):

    def fetch(self, date_str):
        current_time = datetime.datetime.now()

        url = "https://api.bilibili.com/x/web-interface/popular"

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "Chrome/122.0.0.0 Safari/537.36"
                "AppleWebKit/537.36 (KHTML, like Gecko) "
            ),
            "Referer": "https://www.bilibili.com/",
        }

        resp = requests.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        if resp.status_code != 200:
            print(f"request failed, status: {resp.status_code}")
            return []

        data = resp.json()
        if data["code"] != 0:
            print(f"API error: {data['message']}")
            return []

        result = []
        cache_list = []

        for item in data["data"].get("list", []):
            title = item.get("title", "")
            bvid = item.get("bvid", "")
            desc = item.get("desc", "")
            video_url = f"https://www.bilibili.com/video/{bvid}"

            news = {
                'title': title,
                'url': video_url,
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
