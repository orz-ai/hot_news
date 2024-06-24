import json
import re

import requests
from bs4 import BeautifulSoup
from sqlalchemy.sql.functions import now

import cache
from db import News
from .crawler import Crawler
import urllib3
urllib3.disable_warnings()


class HuPuCrawler(Crawler):

    def fetch(self, date_str):
        url = "https://bbs.hupu.com/all-gambia"
        html = requests.get(url=url, headers=self.header, verify=False, timeout=self.timeout)
        html.encoding = "utf-8"
        html_text = html.text
        soup = BeautifulSoup(html_text, "html.parser")
        items = soup.find_all('div', class_='t-info')

        result = []
        cache_list = []
        for i, item in enumerate(items):
            item_a = item.find('a')
            title = item_a.text.strip()

            href = item_a['href']
            link = "https://bbs.hupu.com" + href

            t_light_span = item.find('span', class_='t-lights')
            t_light = t_light_span.text.strip()
            t_light = re.sub("\D", "", t_light)

            t_reply_span = item.find('span', class_='t-replies')
            t_reply = t_reply_span.text.strip()
            t_reply = re.sub("\D", "", t_reply)

            score = int(t_light) + int(t_reply)
            news = News(title=title, url=link, score=score, source=self.crawler_name(),create_time=now(), update_time=now())
            result.append(news)
            cache_list.append(news.to_cache_json())

        cache._hset(date_str, self.crawler_name(), json.dumps(cache_list, ensure_ascii=False))
        return result

    def crawler_name(self):
        return "hupu"