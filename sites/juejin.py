import json

import requests
import urllib3
from sqlalchemy.sql.functions import now

import cache
from db import News
from .crawler import Crawler

urllib3.disable_warnings()


class JueJinCrawler(Crawler):

    def fetch(self, date_str):
        url = "https://api.juejin.cn/content_api/v1/content/article_rank?category_id=1&type=hot"

        resp = requests.get(url=url, params=self.header, verify=False, timeout=self.timeout)
        if resp.status_code != 200:
            print(f"请求失败，状态码：{resp.status_code}")
            return []

        json_data = resp.json()
        contents = json_data.get("data")
        result = []
        cache_list = []
        for i, discus in enumerate(contents):
            title = discus.get("content")["title"]
            score = discus.get("content_counter")["view"]
            content_id = discus.get("content")["content_id"]
            link = f"https://juejin.cn/post/{content_id}"

            news = News(title=title, url=link, score=score, desc="", source=self.crawler_name(), create_time=now(),
                        update_time=now())
            result.append(news)
            cache_list.append(news.to_cache_json())

        cache._hset(date_str, self.crawler_name(), json.dumps(cache_list, ensure_ascii=False))
        return result

    def crawler_name(self):
        return "juejin"
