import json
import datetime
import time

import requests
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

from ...core import cache
from ...db.mysql import News
from .crawler import Crawler
from ..browser_manager import BrowserManager


class DouYinCrawler(Crawler):
    def fetch(self, date_str):
        return self.fetch_v2(date_str)

    def fetch_v1(self, date_str):
        current_time = datetime.datetime.now()
        url = "https://www.douyin.com/hot"
        browser_manager = BrowserManager()
        
        try:
            # 使用浏览器管理器获取页面内容
            page_source, driver = browser_manager.get_page_content(url, wait_time=5)
            
            result = []
            cache_list = []

            # 抖音热榜条目（li 标签里含 /video/ 链接）
            items = driver.find_elements(By.XPATH, '//li[a[contains(@href, "/video/")]]')

            for item in items:
                try:
                    # 提取标题（含 # 标签或较长文本）
                    title_elem = item.find_element(By.XPATH, './/div[contains(text(), "#") or string-length(text()) > 10]')
                    # 提取链接
                    link_elem = item.find_element(By.XPATH, './/a[contains(@href, "/video/")]')
                    # 提取热度
                    hot_elem = item.find_element(By.XPATH, './/span[contains(text(), "万") or contains(text(), "亿")]')

                    title = title_elem.text.strip()
                    item_url = "https://www.douyin.com" + link_elem.get_attribute("href")
                    hot = hot_elem.text.strip()

                    news = {
                        'title': title,
                        'url': item_url,
                        'content': f"热度: {hot}",
                        'source': 'douyin',
                        'publish_time': current_time.strftime('%Y-%m-%d %H:%M:%S')
                    }

                    result.append(news)
                    cache_list.append(news)
                except Exception:
                    continue  # 跳过无效项
            
            # 缓存并返回
            if cache_list:
                cache._hset(date_str, self.crawler_name(), json.dumps(cache_list, ensure_ascii=False))
            return result
            
        except Exception as e:
            return []

    def fetch_v2(self, date_str):
        current_time = datetime.datetime.now()
        url = "https://www.douyin.com/aweme/v1/web/hot/search/list/?device_platform=webapp&aid=6383&channel=channel_pc_web&detail_list=1&source=6&pc_client_type=1&pc_libra_divert=Windows&support_h265=1&support_dash=1&version_code=170400&version_name=17.4.0&cookie_enabled=true&screen_width=1920&screen_height=1080&browser_language=zh-CN&browser_platform=Win32&browser_name=Chrome&browser_version=136.0.0.0&browser_online=true&engine_name=Blink&engine_version=136.0.0.0&os_name=Windows&os_version=10&cpu_core_num=16&device_memory=8&platform=PC&downlink=10&effective_type=4g&round_trip_time=50&webid=7490997798633555467"

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "Chrome/122.0.0.0 Safari/537.36"
                "AppleWebKit/537.36 (KHTML, like Gecko) "
            ),
            "Referer": "https://www.douyin.com/",
        }

        resp = requests.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        if resp.status_code != 200:
            print(f"request failed, status: {resp.status_code}")
            return []

        data = resp.json()
        # https://www.douyin.com/hot/2094286?&trending_topic=%E5%A4%8F%E5%A4%A9%E7%9A%84%E5%91%B3%E9%81%93%E5%9C%A8%E6%8A%96%E9%9F%B3&previous_page=main_page&enter_method=trending_topic&modeFrom=hotDetail&tab_name=trend&position=1&hotValue=11892557
        result = []
        cache_list = []

        for item in data["data"]["word_list"]:
            title = item["word"]
            url =  f"https://www.douyin.com/hot/{item['sentence_id']}?&trending_topic={item['word']}&previous_page=main_page&enter_method=trending_topic&modeFrom=hotDetail&tab_name=trend&position=1&hotValue={item['hot_value']}"

            news = {
                'title': title,
                'url': url,
                'content': title,
                'source': 'douyin',
                'publish_time': current_time.strftime('%Y-%m-%d %H:%M:%S')
            }

            result.append(news)
            cache_list.append(news)

        cache._hset(date_str, self.crawler_name(), json.dumps(cache_list, ensure_ascii=False))
        return result


    def crawler_name(self):
        return "douyin"
