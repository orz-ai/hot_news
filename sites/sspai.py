import json

import requests
from sqlalchemy.sql.functions import now

import cache
from db import News
from .crawler import Crawler


class ShaoShuPaiCrawler(Crawler):
    def fetch(self):
        url = "https://sspai.com/api/v1/article/tag/page/get?limit=50&offset=0&tag=%E7%83%AD%E9%97%A8%E6%96%87%E7%AB%A0&released=false"
        resp = requests.get(url=url, params=self.header, verify=False, timeout=self.timeout)
        if resp.status_code != 200:
            print(f"请求失败，状态码：{resp.status_code}")
            return []

        json_data = resp.json()
        article_list = json_data.get("data")
        result = []
        cache_list = []
        for article in article_list:
            title = article.get("title")
            article_id = article.get("id")
            article_url = f"https://sspai.com/post/{article_id}"
            comments_count = article.get("comment_count")
            likes_count = article.get("like_count")
            score = comments_count + likes_count
            desc = article.get("summary")

            news = News(title=title, url=article_url, score=score, source=self.crawler_name(), desc=desc, create_time=now(), update_time=now())
            result.append(news)
            cache_list.append(news.to_cache_json())

        cache._hset(self.date_str, self.crawler_name(), json.dumps(cache_list, ensure_ascii=False))
        return result

    def crawler_name(self):
        return "shaoshupai"