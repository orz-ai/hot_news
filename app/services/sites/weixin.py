import json
import datetime
import time
import requests
from bs4 import BeautifulSoup
import urllib3
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from ...core import cache
from ...db.mysql import News
from .crawler import Crawler
from ..browser_manager import BrowserManager

# 禁用SSL警告
urllib3.disable_warnings()

class WeiXinCrawler(Crawler):
    """
    微信热门内容爬虫
    使用微信看一看热门页面获取数据
    """
    
    def fetch(self, date_str):
        """获取微信热门内容"""
        current_time = datetime.datetime.now()
        browser_manager = BrowserManager()
        
        try:
            # 首先尝试从微信看一看获取热门内容
            result = self._fetch_from_weixin_kankan(browser_manager)
            
            if result and len(result) > 0:
                # 缓存数据
                cache.hset(date_str, self.crawler_name(), json.dumps(result, ensure_ascii=False))
                return result
                
            # 如果看一看失败，尝试从微信读书获取热门书评
            result = self._fetch_from_weixin_dushu(browser_manager)
            if result and len(result) > 0:
                # 缓存数据
                cache.hset(date_str, self.crawler_name(), json.dumps(result, ensure_ascii=False))
                return result
                
        except Exception as e:
            # 如果遇到错误，返回空列表
            return []
            
        # 所有方法都失败，返回空列表
        return []
    
    def _fetch_from_weixin_kankan(self, browser_manager):
        """从微信看一看页面获取热门内容"""
        url = "https://k.weixin.qq.com/"
        
        try:
            # 获取页面内容
            page_source, driver = browser_manager.get_page_content(url, wait_time=10)
            
            # 等待热门内容加载
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".hot"))
                )
            except:
                # 如果等待超时，仍然尝试获取内容
                pass
                
            # 点击"热点"标签切换到热门内容
            try:
                hot_tab = driver.find_element(By.XPATH, "//div[contains(text(), '热点') and @class='tab']")
                hot_tab.click()
                time.sleep(3)  # 等待内容加载
            except:
                # 如果找不到热点标签，继续尝试获取当前页面内容
                pass
                
            result = []
            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 获取文章列表
            articles = driver.find_elements(By.CSS_SELECTOR, ".article-item")
            
            if not articles:
                # 尝试其他可能的选择器
                articles = driver.find_elements(By.CSS_SELECTOR, ".doc-item")
                
            if not articles:
                # 再尝试其他可能的选择器
                articles = driver.find_elements(By.CSS_SELECTOR, ".item")
                
            for article in articles:
                try:
                    # 获取文章标题和链接
                    title_elem = article.find_element(By.CSS_SELECTOR, "h3, .title")
                    title = title_elem.text.strip()
                    
                    # 尝试获取链接
                    link = None
                    try:
                        link_elem = article.find_element(By.TAG_NAME, "a")
                        link = link_elem.get_attribute("href")
                    except:
                        # 如果直接获取链接失败，则记录文章id，以后可以构建链接
                        try:
                            article_id = article.get_attribute("data-id") or article.get_attribute("id")
                            link = f"https://k.weixin.qq.com/article?id={article_id}"
                        except:
                            link = "https://k.weixin.qq.com/"
                    
                    # 获取来源
                    source = ""
                    try:
                        source_elem = article.find_element(By.CSS_SELECTOR, ".account, .source")
                        source = source_elem.text.strip()
                    except:
                        pass
                    
                    # 获取摘要
                    summary = ""
                    try:
                        summary_elem = article.find_element(By.CSS_SELECTOR, ".desc, .summary, p")
                        summary = summary_elem.text.strip()
                    except:
                        pass
                    
                    news = {
                        'title': title,
                        'url': link,
                        'content': f"来源: {source} | 摘要: {summary[:50] if summary else '无摘要'}",
                        'source': 'weixin',
                        'publish_time': current_time
                    }
                    
                    result.append(news)
                    
                    # 限制获取前20条
                    if len(result) >= 20:
                        break
                        
                except Exception as e:
                    continue
                    
            return result
            
        except Exception as e:
            return []
    
    def _fetch_from_weixin_dushu(self, browser_manager):
        """从微信读书获取热门书评"""
        url = "https://weread.qq.com/web/category/all"
        
        try:
            # 获取页面内容
            page_source, driver = browser_manager.get_page_content(url, wait_time=8)
            
            result = []
            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 尝试点击排行榜标签
            try:
                rank_tab = driver.find_element(By.XPATH, "//a[contains(text(), '排行榜')]")
                rank_tab.click()
                time.sleep(3)  # 等待内容加载
            except:
                # 如果找不到排行榜标签，继续尝试获取当前页面内容
                pass
            
            # 获取热门书籍列表
            books = driver.find_elements(By.CSS_SELECTOR, ".shelf-item, .book-item")
            
            for book in books:
                try:
                    # 获取书籍标题和链接
                    title_elem = book.find_element(By.CSS_SELECTOR, ".title, h3")
                    title = title_elem.text.strip()
                    
                    # 尝试获取链接
                    link = "https://weread.qq.com/web/category/all"
                    try:
                        link_elem = book.find_element(By.TAG_NAME, "a")
                        link = link_elem.get_attribute("href")
                    except:
                        book_id = book.get_attribute("data-bid") or book.get_attribute("id")
                        if book_id:
                            link = f"https://weread.qq.com/web/reader/{book_id}"
                    
                    # 获取作者
                    author = ""
                    try:
                        author_elem = book.find_element(By.CSS_SELECTOR, ".author, .writer")
                        author = author_elem.text.strip()
                    except:
                        pass
                    
                    # 获取摘要/简介
                    intro = ""
                    try:
                        intro_elem = book.find_element(By.CSS_SELECTOR, ".intro, .desc")
                        intro = intro_elem.text.strip()
                    except:
                        pass
                    
                    news = {
                        'title': f"热门书籍: {title}",
                        'url': link,
                        'content': f"作者: {author} | 简介: {intro[:50] if intro else '无简介'}",
                        'source': 'weixin',
                        'publish_time': current_time
                    }
                    
                    result.append(news)
                    
                    # 限制获取前20条
                    if len(result) >= 20:
                        break
                        
                except Exception as e:
                    continue
                    
            return result
            
        except Exception as e:
            return []
    
    def crawler_name(self):
        return "weixin"
