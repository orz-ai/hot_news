import json

import requests
import urllib3
from bs4 import BeautifulSoup
from sqlalchemy.sql.functions import now

from .crawler import Crawler
from ...core import cache
from ...db.mysql import News

urllib3.disable_warnings()


class BaiduNewsCrawler(Crawler):
    # 返回news_list
    def fetch(self, date_str) -> list[News]:

        url = "https://top.baidu.com/api/board?platform=wise&tab=realtime"

        resp = requests.get(url=url, params=self.header, verify=False, timeout=self.timeout)
        if resp.status_code != 200:
            print(f"request failed, status: {resp.status_code}")
            return []

        json_data = resp.json()
        contents = json_data.get("data")["cards"][0]["content"]
        result = []
        cache_list = []
        for content in contents:
            title = content.get("query")
            url = content.get("url")
            desc = content.get("desc")
            score = content.get("hotScore")

            # replace url m to www
            url = url.replace("m.", "www.")
            news = News(title=title, url=url, score=score, desc=desc, source=self.crawler_name(), create_time=now(),
                        update_time=now())
            result.append(news)
            cache_list.append(news.to_cache_json())

        cache._hset(date_str, self.crawler_name(), json.dumps(cache_list, ensure_ascii=False))
        return result

    def crawler_name(self):
        return "baidu"

    @staticmethod
    def fetch_v0():

        url = "https://top.baidu.com/board?tab=realtime"
        proxies = {
            # "http": "http://127.0.0.1:7890",
            # "https": "http://127.0.0.0:7890"
        }

        header = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,"
                      "*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "upgrade-insecure-requests": 1,
            "host": "www.baidu.com",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/86.0.4240.183 Safari/537.36"
        }
        html = requests.get(url=url, params=header, verify=False, proxies=proxies)
        html.encoding = "utf-8"
        html_text = html.text
        soup = BeautifulSoup(html_text, "html.parser")
        main_content = soup.find_all("main")[0]
        news_main_content = main_content.find("div", style='margin-bottom:20px')

        div_elements = news_main_content.find_all('div', class_='category-wrap_iQLoo horizontal_1eKyQ')

        result = []
        for div_element in div_elements:
            hot_index = div_element.find(class_='hot-index_1Bl1a').text.strip()
            news_title = div_element.find(class_='c-single-text-ellipsis').text.strip()
            news_link = div_element.find('a', class_='title_dIF3B')['href']

            news = News(title=news_title, url=news_link, score=hot_index, desc="", source="baidu", create_time=now(),
                        update_time=now())
            result.append(news)

        return result
