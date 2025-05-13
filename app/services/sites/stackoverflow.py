import json
import datetime

import requests
import urllib3

from .crawler import Crawler
from ...core import cache
from ...db.mysql import News

urllib3.disable_warnings()


class TenXunWangCrawler(Crawler):

    def fetch(self, date_str):
        current_time = datetime.datetime.now()

        url = "https://i.news.qq.com/gw/event/pc_hot_ranking_list?ids_hash=&offset=0&page_size=51&appver=15.5_qqnews_7.1.60&rank_id=hot"

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "Chrome/122.0.0.0 Safari/537.36"
                "AppleWebKit/537.36 (KHTML, like Gecko) "
            ),
            "Referer": "https://news.qq.com/",
        }

        resp = requests.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        if resp.status_code != 200:
            print(f"request failed, status: {resp.status_code}")
            return []

        data = resp.json()
        result = []
        cache_list = []


        for i, item in enumerate(data["idlist"][0].get("newslist", [])):
            if i == 0:
                # 腾讯新闻用户最关注的热点，每10分钟更新一次
                continue

            title = item.get("title", "")
            url = item.get("url", "")
            desc = item.get("abstract", "")

            news = {
                'title': title,
                'url': url,
                'content': desc,
                'source': 'tenxunwang',
                'publish_time': current_time.strftime('%Y-%m-%d %H:%M:%S')
            }

            result.append(news)
            cache_list.append(news)

        cache._hset(date_str, self.crawler_name(), json.dumps(cache_list, ensure_ascii=False))
        return result

    def crawler_name(self):
        return "bilibili"
