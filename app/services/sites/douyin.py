import json
import datetime
import time

from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

from ...core import cache
from ...db.mysql import News
from .crawler import Crawler
from ..browser_manager import BrowserManager


class DouYinCrawler(Crawler):
    def fetch(self, date_str):
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

    def crawler_name(self):
        return "douyin"
