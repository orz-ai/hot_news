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

class HackerNewsCrawler(Crawler):
    """hacker news"""
    def fetch(self, date_str):
        current_time = datetime.datetime.now()
        
        try:
            # 首先尝试直接请求方式获取内容
            result = self._fetch_with_requests()
            
            if result and len(result) > 0:
                # 缓存数据
                cache.hset(date_str, self.crawler_name(), json.dumps(result, ensure_ascii=False))
                return result
                
            # 如果请求方式失败，尝试使用浏览器模拟获取
            browser_manager = BrowserManager()
            result = self._fetch_with_browser(browser_manager)
            if result and len(result) > 0:
                # 缓存数据
                cache.hset(date_str, self.crawler_name(), json.dumps(result, ensure_ascii=False))
                return result
                
        except Exception as e:
            # 如果遇到错误，返回空列表
            return []
            
        # 所有方法都失败，返回空列表
        return []
    
    def _fetch_with_requests(self):
        """使用requests直接获取Hacker News内容"""
        url = "https://news.ycombinator.com/"
        
        try:
            # 发送HTTP请求
            response = requests.get(url, headers=self.header, timeout=self.timeout)
            if response.status_code != 200:
                return []
                
            # 解析HTML内容
            soup = BeautifulSoup(response.text, 'html.parser')
            
            result = []
            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 获取所有新闻条目
            items = soup.select("tr.athing")
            
            for item in items:
                try:
                    # 获取ID用于关联评论和元数据
                    item_id = item.get('id')
                    if not item_id:
                        continue
                        
                    # 获取标题和链接
                    title_element = item.select_one(".titleline a")
                    if not title_element:
                        continue
                        
                    title = title_element.text.strip()
                    url = title_element.get('href')
                    
                    # 如果URL是相对路径，转换为绝对路径
                    if url and not url.startswith('http'):
                        url = f"https://news.ycombinator.com/{url}"
                    
                    # 获取来源网站
                    site_element = item.select_one(".sitestr")
                    site = site_element.text.strip() if site_element else ""
                    
                    # 查找下一个tr获取元数据（分数、用户、时间等）
                    metadata = item.find_next_sibling('tr')
                    if not metadata:
                        continue
                        
                    # 获取分数
                    score_element = metadata.select_one(".score")
                    score = score_element.text.strip() if score_element else "0 points"
                    
                    # 获取作者
                    user_element = metadata.select_one(".hnuser")
                    user = user_element.text.strip() if user_element else "unknown"
                    
                    # 获取评论数
                    comments_element = metadata.select_one("a:last-child")
                    comments = comments_element.text.strip() if comments_element else "0 comments"
                    if "discuss" in comments:
                        comments = "0 comments"
                    
                    # 构建内容摘要
                    content = f"来源: {site} | 得分: {score} | 作者: {user} | 评论: {comments}"
                    
                    news = {
                        'title': title,
                        'url': url,
                        'content': content,
                        'source': 'hackernews',
                        'publish_time': current_time
                    }
                    
                    result.append(news)
                    
                    # 限制获取前30条
                    if len(result) >= 30:
                        break
                        
                except Exception as e:
                    continue
                    
            return result
            
        except Exception as e:
            return []
    
    def _fetch_with_browser(self, browser_manager):
        """使用浏览器模拟方式获取Hacker News内容"""
        url = "https://news.ycombinator.com/"
        
        try:
            # 获取页面内容
            page_source, driver = browser_manager.get_page_content(url, wait_time=5)
            
            # 等待页面元素加载
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".athing"))
                )
            except:
                # 如果等待超时，仍然尝试获取内容
                pass
            
            result = []
            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 获取所有新闻条目
            items = driver.find_elements(By.CSS_SELECTOR, "tr.athing")
            
            for item in items:
                try:
                    # 获取ID用于关联评论和元数据
                    item_id = item.get_attribute("id")
                    if not item_id:
                        continue
                    
                    # 获取标题和链接
                    title_element = item.find_element(By.CSS_SELECTOR, ".titleline a")
                    title = title_element.text.strip()
                    url = title_element.get_attribute("href")
                    
                    # 获取来源网站
                    site = ""
                    try:
                        site_element = item.find_element(By.CSS_SELECTOR, ".sitestr")
                        site = site_element.text.strip()
                    except:
                        pass
                    
                    # 查找下一个tr获取元数据（分数、用户、时间等）
                    try:
                        metadata = driver.find_element(By.XPATH, f"//tr[@id='{item_id}']/following-sibling::tr[1]")
                        
                        # 获取分数
                        score = "0 points"
                        try:
                            score_element = metadata.find_element(By.CSS_SELECTOR, ".score")
                            score = score_element.text.strip()
                        except:
                            pass
                        
                        # 获取作者
                        user = "unknown"
                        try:
                            user_element = metadata.find_element(By.CSS_SELECTOR, ".hnuser")
                            user = user_element.text.strip()
                        except:
                            pass
                        
                        # 获取评论数
                        comments = "0 comments"
                        try:
                            comments_element = metadata.find_element(By.XPATH, ".//a[last()]")
                            comments = comments_element.text.strip()
                            if "discuss" in comments:
                                comments = "0 comments"
                        except:
                            pass
                        
                        # 构建内容摘要
                        content = f"来源: {site} | 得分: {score} | 作者: {user} | 评论: {comments}"
                    except:
                        content = f"来源: {site}"
                    
                    news = {
                        'title': title,
                        'url': url,
                        'content': content,
                        'source': 'hackernews',
                        'publish_time': current_time
                    }
                    
                    result.append(news)
                    
                    # 限制获取前30条
                    if len(result) >= 30:
                        break
                        
                except Exception as e:
                    continue
                    
            return result
            
        except Exception as e:
            return []
    
    def crawler_name(self):
        return "hackernews"
