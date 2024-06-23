import json
import re

import requests
from bs4 import BeautifulSoup
from sqlalchemy.sql.functions import now

import cache
from db import News
from .crawler import Crawler


class VtexCrawler(Crawler):

    def fetch(self, date_str):
        url = "https://www.v2ex.com/?tab=hot"
        header = self.header.copy()
        header.update(
            {
                "accept-encoding": "",
                "accept-language": "zh-CN,zh;q=0.9",
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "host": "www.v2ex.com",
            }
        )

        html = requests.get(url=url, headers=header, verify=False, timeout=self.timeout)
        html.encoding = "utf-8"
        html_text = html.text
        soup = BeautifulSoup(html_text, "html.parser")
        items = soup.find_all('div', class_='cell item')
        base_link = "https://www.v2ex.com"

        result = []
        cache_list = []
        for i, item in enumerate(items):
            item_a = item.find('a', class_='topic-link')
            title = item_a.text.strip()

            href = item_a['href']
            link = base_link + href

            score_a = item.find('a', class_='count_livid')
            if score_a is None:
                score = 0
            else:
                score = score_a.text.strip()

            news = News(title=title, url=link, score=score, desc="", source=self.crawler_name(), create_time=now(),
                        update_time=now())
            result.append(news)
            cache_list.append(news.to_cache_json())

        cache._hset(date_str, self.crawler_name(), json.dumps(cache_list, ensure_ascii=False))
        return result

    def crawler_name(self):
        return "v2ex"