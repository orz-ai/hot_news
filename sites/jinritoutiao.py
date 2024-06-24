# -- coding: utf-8 --

import json

import requests
import urllib3
from sqlalchemy.sql.functions import now

import cache
from db import News
from .crawler import Crawler

urllib3.disable_warnings()


class JinRiTouTiaoCrawler(Crawler):
    """
    今日头条
    """

    def fetch(self, date_str):
        url = "https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc"
        header = self.header.copy()
        header.update({
            "host": "www.toutiao.com",
            "accept-encoding": "",
        })

        resp = requests.get(url=url, headers=header, verify=False, timeout=self.timeout)
        if resp.status_code != 200:
            print(f"请求失败，状态码：{resp.status_code}")
            return []

        json_data = resp.json()
        hot_ranks = json_data.get("data")

        result = []
        cache_list = []
        fix_top_news = json_data.get("fixed_top_data")
        if fix_top_news:
            hot_ranks.extend(fix_top_news)

        for hot in hot_ranks:
            title = hot.get("Title", "").strip()
            desc = hot.get("QueryWord", "").strip().replace("\n", "")
            score = hot.get("HotValue", "0")
            link = hot.get("Url", "")

            news = News(title=title, url=link, score=score, desc=desc, source=self.crawler_name(), create_time=now(),
                        update_time=now())
            result.append(news)
            cache_list.append(news.to_cache_json())

        cache._hset(date_str, self.crawler_name(), json.dumps(cache_list, ensure_ascii=False))
        return result

    def crawler_name(self):
        return "jinritoutiao"
