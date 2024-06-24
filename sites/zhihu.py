import json

import requests
from sqlalchemy.sql.functions import now

import cache
from db import News
from .crawler import Crawler
import urllib3
urllib3.disable_warnings()


class ZhiHuCrawler(Crawler):

    def fetch(self, date_str):
        url = "https://api.zhihu.com/topstory/hot-list?limit=20&reverse_order=0"

        resp = requests.get(url=url, params=self.header, verify=False, timeout=self.timeout)
        if resp.status_code != 200:
            print(f"请求失败，状态码：{resp.status_code}")
            return []

        json_data = resp.json()
        hot_searches = json_data.get("data")
        result = []
        cache_list = []
        for hot_search in hot_searches:
            target = hot_search.get("target")
            title = target.get("title")
            answer_count = target.get("answer_count")
            follower_count = target.get("follower_count")
            score = answer_count + follower_count
            link = "https://www.zhihu.com/question/" + str(target.get("id"))
            desc = target.get("excerpt")

            news = News(
                title=title,
                url=link,
                score=score,
                desc=desc,
                source=self.crawler_name(),
                create_time=now(),
                update_time=now()
            )
            result.append(news)
            cache_list.append(news.to_cache_json())

        cache._hset(date_str, self.crawler_name(), json.dumps(cache_list, ensure_ascii=False))
        return result

    def crawler_name(self):
        return "zhihu"