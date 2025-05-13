import sys
import os
import json
from datetime import datetime

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.sites.hackernews import HackerNewsCrawler

def test_hackernews_crawler():
    """测试Hacker News爬虫"""
    print("===== 测试 Hacker News 爬虫 =====")
    crawler = HackerNewsCrawler()
    date_str = datetime.now().strftime('%Y-%m-%d')
    
    print("1. 使用requests方式测试:")
    result = crawler._fetch_with_requests()
    if result and len(result) > 0:
        print(f"  - 成功获取到 {len(result)} 条新闻")
        print("  - 第一条新闻示例:")
        print(f"    标题: {result[0]['title']}")
        print(f"    链接: {result[0]['url']}")
        print(f"    内容: {result[0]['content']}")
    else:
        print("  - 使用requests方式获取失败")
    
    print("\n2. 使用浏览器方式测试:")
    from app.services.browser_manager import BrowserManager
    browser_manager = BrowserManager()
    
    try:
        result = crawler._fetch_with_browser(browser_manager)
        if result and len(result) > 0:
            print(f"  - 成功获取到 {len(result)} 条新闻")
            print("  - 第一条新闻示例:")
            print(f"    标题: {result[0]['title']}")
            print(f"    链接: {result[0]['url']}")
            print(f"    内容: {result[0]['content']}")
        else:
            print("  - 使用浏览器方式获取失败")
    except Exception as e:
        print(f"  - 浏览器测试异常: {str(e)}")
    
    print("\n3. 测试完整的fetch方法:")
    result = crawler.fetch(date_str)
    if result and len(result) > 0:
        print(f"  - 成功获取到 {len(result)} 条新闻")
        print("  - 结果示例(前3条):")
        for i, news in enumerate(result[:3]):
            print(f"    [{i+1}] {news['title']}")
    else:
        print("  - fetch方法获取失败")
    
    print("\n===== 测试完成 =====")

if __name__ == "__main__":
    test_hackernews_crawler() 