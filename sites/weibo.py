import json

import requests
from bs4 import BeautifulSoup
from sqlalchemy.sql.functions import now

import cache
from db import News
from .crawler import Crawler


class WeiboCrawler(Crawler):

    def fetch(self):
        url = "https://weibo.com/ajax/side/hotSearch"

        resp = requests.get(url=url, params=self.header, verify=False, timeout=self.timeout)
        if resp.status_code != 200:
            print(f"请求失败，状态码：{resp.status_code}")
            return []

        json_data = resp.json()
        hot_searches = json_data.get("data")["realtime"]
        result = []
        cache_list = []
        for hot_search in hot_searches:
            title = hot_search.get("word")
            hot_index = hot_search.get("num")
            hot_url = f"https://s.weibo.com/weibo?q={title}"

            news = News(title=title, url=hot_url, score=hot_index, source=self.crawler_name(), create_time=now(), update_time=now())
            result.append(news)
            cache_list.append(news.to_cache_json())

        cache._hset(self.date_str, self.crawler_name(), json.dumps(cache_list, ensure_ascii=False))
        return result


    def crawler_name(self):
        return "weibo"
