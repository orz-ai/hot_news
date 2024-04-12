import json

import requests
from bs4 import BeautifulSoup
from sqlalchemy.sql.functions import now

import cache
from db import News
from .crawler import Crawler


class TieBaCrawler(Crawler):

    def fetch(self):
        url = "https://tieba.baidu.com/hottopic/browse/topicList"

        resp = requests.get(url=url, params=self.header, verify=False, timeout=self.timeout)
        if resp.status_code != 200:
            print(f"请求失败，状态码：{resp.status_code}")
            return []

        json_data = resp.json()
        hot_discuses = json_data.get("data")["bang_topic"]["topic_list"]
        result = []
        cache_list = []
        for i, discus in enumerate(hot_discuses):
            title = discus.get("topic_name")
            score = discus.get("discuss_num")
            desc = discus.get("topic_desc")
            link = discus.get("topic_url")

            news = News(title=title, url=link, score=score, desc=desc, source=self.crawler_name(), create_time=now(), update_time=now())
            result.append(news)
            cache_list.append(news.to_cache_json())

        cache._hset(self.date_str, self.crawler_name(), json.dumps(cache_list, ensure_ascii=False))
        return result

    def crawler_name(self):
        return "tieba"

