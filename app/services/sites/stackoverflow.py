import json
import datetime

import requests
import urllib3

from .crawler import Crawler
from ...core import cache
from ...db.mysql import News

urllib3.disable_warnings()


class StackOverflowCrawler(Crawler):
    def fetch(self, date_str):
        current_time = datetime.datetime.now()

        url = "https://api.stackexchange.com/2.3/questions?order=desc&sort=hot&site=stackoverflow"

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "Chrome/122.0.0.0 Safari/537.36"
                "AppleWebKit/537.36 (KHTML, like Gecko) "
            ),
            "Referer": "https://stackoverflow.com/",
        }

        resp = requests.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        if resp.status_code != 200:
            print(f"request failed, status: {resp.status_code}")
            return []

        data = resp.json()
        result = []
        cache_list = []

        for i, item in enumerate(data["items"]):
            title = item.get("title", "")
            url = item.get("link", "")
            desc = item.get("title", "")

            news = {
                'title': title,
                'url': url,
                'content': desc,
                'source': 'stackoverflow',
                'publish_time': current_time.strftime('%Y-%m-%d %H:%M:%S')
            }

            result.append(news)
            cache_list.append(news)

        cache.hset(date_str, self.crawler_name(), json.dumps(cache_list, ensure_ascii=False))
        return result

    def crawler_name(self):
        return "stackoverflow"
