import json
import re

import requests
import urllib3
from bs4 import BeautifulSoup
from sqlalchemy.sql.functions import now

from ...core import cache
from ...db.mysql import News
from .crawler import Crawler

urllib3.disable_warnings()


class DouBanCrawler(Crawler):

    def fetch(self, date_str):
        url = "https://www.douban.com/group/explore"

        header = self.header.copy()
        header.update({
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-encoding": "",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
            "host": "www.douban.com",
            "referer": "https://www.douban.com/group/explore",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
        })

        html = requests.get(url=url, headers=header, verify=False, timeout=self.timeout)
        html.encoding = "utf-8"
        html_text = html.text
        soup = BeautifulSoup(html_text, "html.parser")
        channel_items = soup.find_all('div', class_='channel-item')

        result = []
        cache_list = []
        for channel_item in channel_items:
            likes = channel_item.find('div', class_='likes')
            score = likes.text.strip()
            score = re.sub("\D", "", score)

            title_a = channel_item.find('h3').find('a')
            title = title_a.text.strip()
            link = title_a['href']

            news = News(title=title, url=link, score=score, source=self.crawler_name(), create_time=now(),
                        update_time=now())
            result.append(news)
            cache_list.append(news.to_cache_json())

        cache._hset(date_str, self.crawler_name(), json.dumps(cache_list, ensure_ascii=False))
        return result

    def crawler_name(self):
        return "douban"
