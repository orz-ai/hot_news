import json
import datetime
import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from ...core import cache
from ...db.mysql import News
from .crawler import Crawler


class DouYinCrawler(Crawler):
    def fetch(self, date_str):
        current_time = datetime.datetime.now()
        url = "https://www.douyin.com/hot"

        # 启动浏览器（无头）
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")  # 去掉这行可以看可视化浏览器
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--log-level=3")

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(url)
        time.sleep(5)  # 等待初始加载

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
                url = "https://www.douyin.com" + link_elem.get_attribute("href")
                hot = hot_elem.text.strip()

                news = {
                    'title': title,
                    'url': url,
                    'content': f"热度: {hot}",
                    'source': 'douyin',
                    'publish_time': current_time.strftime('%Y-%m-%d %H:%M:%S')
                }

                result.append(news)
                cache_list.append(news)
            except Exception:
                continue  # 跳过无效项

        driver.quit()

        # 缓存并返回
        cache._hset(date_str, self.crawler_name(), json.dumps(cache_list, ensure_ascii=False))
        return result

    def crawler_name(self):
        return "douyin"
