import json
import time

import requests
import urllib3
from sqlalchemy.sql.functions import now

from ...core import cache
from ...db.mysql import News
from .crawler import Crawler

urllib3.disable_warnings()


class TsKrCrawler(Crawler):
    def fetch(self, date_str):
        url = "https://gateway.36kr.com/api/mis/nav/home/nav/rank/hot"

        header = self.header.copy()
        header.update({
            "host": "gateway.36kr.com",
            "origin": "https://m.36kr.com",
            "Referer": "https://m.36kr.com/",
            "User-agent": "Mozilla/5.0 (Linux; Android 10; Redmi K30 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Mobile Safari/537.36",
            "content-type": "application/json;charset=UTF-8",
        })

        # 当前时间戳
        now_timestamp = int(time.time() * 1000)

        data = {"partner_id": "wap", "timestamp": now_timestamp, "param": {"siteId": 1, "platformId": 2}}

        resp = requests.post(url=url, headers=header, json=data, verify=False, timeout=self.timeout)
        if resp.status_code != 200:
            print(f"请求失败，状态码：{resp.status_code}")
            return []

        json_data = resp.json()
        hot_searches = json_data.get("data")["hotRankList"]
        result = []
        cache_list = []
        for hot_search in hot_searches:
            material = hot_search.get("templateMaterial")
            mid = material.get("itemId")
            title = material.get("widgetTitle")
            score = material.get("statRead")
            hot_url = f"https://www.36kr.com/p/{mid}"

            news = News(title=title, url=hot_url, score=score, source=self.crawler_name(), create_time=now(),
                        update_time=now())
            result.append(news)
            cache_list.append(news.to_cache_json())

        cache._hset(date_str, self.crawler_name(), json.dumps(cache_list, ensure_ascii=False))
        return result

    def crawler_name(self):
        return "36kr"
