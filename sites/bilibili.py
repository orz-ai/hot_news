import json

import requests
from sqlalchemy.sql.functions import now

import cache
from db import News
from .crawler import Crawler


class BilibiliCrawler(Crawler):

    def fetch(self, date_str):
        url = "http://api.bilibili.com/x/web-interface/ranking/v2"
        header = self.header.copy()
        header["host"] = "api.bilibili.com"

        resp = requests.get(url=url, headers=header, verify=False, timeout=self.timeout)
        if resp.status_code != 200:
            print(f"请求失败，状态码：{resp.status_code}")
            return []

        json_data = resp.json()
        hot_ranks = json_data.get("data")["list"]
        result = []
        cache_list = []
        for hot in hot_ranks:
            title = hot.get("title").strip()
            desc = hot.get("desc").strip().replace("\n", "")
            score = hot.get("stat")["view"]

            bvid = hot.get("bvid")
            link = "https://www.bilibili.com/video/" + bvid

            news = News(title=title, url=link, score=score, desc=desc, source=self.crawler_name(),create_time=now(), update_time=now())
            result.append(news)
            cache_list.append(news.to_cache_json())

        cache._hset(date_str, self.crawler_name(), json.dumps(cache_list, ensure_ascii=False))
        return result

    def crawler_name(self):
        return "bilibili"




