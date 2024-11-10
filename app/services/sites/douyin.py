import json
import re

import requests
from bs4 import BeautifulSoup
from sqlalchemy.sql.functions import now

from ...core import cache
from ...db.mysql import News
from .crawler import Crawler
import urllib3
urllib3.disable_warnings()


class DouYinCrawler(Crawler):

    def fetch(self, date_str):
        token_url = "https://www.douyin.com/passport/general/login_guiding_strategy/?aid=6383"
        hot_url = "https://www.douyin.com/aweme/v1/web/hot/search/list/?device_platform=webapp&aid=6383&channel=channel_pc_web&detail_list=1&round_trip_time=50"

        token_resp = requests.get(url=token_url, params=self.header, verify=False)
        if token_resp.status_code != 200:
            print(f"请求失败，状态码：{token_resp.status_code}")
            return []

        cookie = token_resp.headers["set-cookie"]
        # js: const pattern = /passport_csrf_token=(.*); Path/s;
        pattern = r"passport_csrf_token_default=(.*); Path"
        cookie = re.search(pattern, cookie).group(1)
        header = self.header.copy()
        header.update({
            "cookie": f"passport_csrf_token={cookie};",
            "referer": "https://www.douyin.com/",
            "accept": "application/json",
            "accept-encoding": "",
        })

        hot_resp = requests.get(url=hot_url, headers=header, verify=False, timeout=self.timeout)
        json_data = hot_resp.json()
        contents = json_data.get("data")["word_list"]
        result = []
        cache_list = []
        for i, discus in enumerate(contents):
            title = discus.get("word")
            score = discus.get("hot_value")
            sentence_id = discus.get("sentence_id")
            link = f"https://www.douyin.com/hot/{sentence_id}/{title}"

            news = News(title=title, url=link, score=score, desc="", source=self.crawler_name(), create_time=now(), update_time=now())
            result.append(news)
            cache_list.append(news.to_cache_json())

        cache._hset(date_str, self.crawler_name(), json.dumps(cache_list, ensure_ascii=False))
        return result

    def crawler_name(self):
        return "douyin"


