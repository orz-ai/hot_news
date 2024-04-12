import json
import re

import requests
from bs4 import BeautifulSoup
from sqlalchemy.sql.functions import now

import cache
from db import News
from .crawler import Crawler


class FtPoJieCrawler(Crawler):

    def fetch(self):
        url = "https://www.52pojie.cn/forum.php?mod=guide&view=hot"

        html = requests.get(url=url, headers=self.header, verify=False, timeout=self.timeout)
        html.encoding = "gbk"
        html_text = html.text
        soup = BeautifulSoup(html_text, "html.parser")
        div_elements = soup.find_all('a', class_='xst')

        result = []
        cache_list = []
        for div_element in div_elements:
            title = div_element.text.strip()
            href = div_element.get('href')
            link = "https://www.52pojie.cn/" + href
            score = div_element.nextSibling.next.text.strip()
            score = re.sub("\D", "", score)

            news = News(title=title,
                        url=link,
                        score=score,
                        desc="",
                        source=self.crawler_name(),
                        create_time=now(),
                        update_time=now()
                        )
            result.append(news)
            cache_list.append(news.to_cache_json())

        cache._hset(self.date_str, self.crawler_name(), json.dumps(cache_list, ensure_ascii=False))
        return result

    def crawler_name(self):
        return "52pojie"