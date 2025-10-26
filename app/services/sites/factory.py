from typing import Dict, Type

from .baidu import BaiduNewsCrawler
from .bilibili import BilibiliCrawler
from .crawler import Crawler
from .douban import DouBanCrawler
from .douyin import DouYinCrawler
from .ftpojie import FtPoJieCrawler
from .github import GithubCrawler
from .hackernews import HackerNewsCrawler
from .hupu import HuPuCrawler
from .jinritoutiao import JinRiTouTiaoCrawler
from .juejin import JueJinCrawler
from .sspai import ShaoShuPaiCrawler
from .stackoverflow import StackOverflowCrawler
from .tenxunwang import TenXunWangCrawler
from .tieba import TieBaCrawler
from .tskr import TsKrCrawler
from .vtex import VtexCrawler
from .weibo import WeiboCrawler
from .weixin import WeiXinCrawler
from .zhihu import ZhiHuCrawler
from .sina_finance import SinaFinanceCrawler
from .eastmoney import EastMoneyCrawler
from .xueqiu import XueqiuCrawler
from .cls import CLSCrawler


class CrawlerRegister:
    def __init__(self):
        self.crawlers = {}
    
    def register(self) -> Dict[str, Crawler]:
        """注册所有爬虫"""
        crawler_map = {
            "baidu": BaiduNewsCrawler(),
            "shaoshupai": ShaoShuPaiCrawler(),
            "weibo": WeiboCrawler(),
            "zhihu": ZhiHuCrawler(),
            "36kr": TsKrCrawler(),
            "52pojie": FtPoJieCrawler(),
            "bilibili": BilibiliCrawler(),
            "douban": DouBanCrawler(),
            "hupu": HuPuCrawler(),
            "tieba": TieBaCrawler(),
            "juejin": JueJinCrawler(),
            "douyin": DouYinCrawler(),
            "v2ex": VtexCrawler(),
            "jinritoutiao": JinRiTouTiaoCrawler(),
            "tenxunwang": TenXunWangCrawler(),
            "stackoverflow": StackOverflowCrawler(),
            "github": GithubCrawler(),
            "hackernews": HackerNewsCrawler(),
            "sina_finance": SinaFinanceCrawler(),
            "eastmoney": EastMoneyCrawler(),
            "xueqiu": XueqiuCrawler(),
            "cls": CLSCrawler(),
        }
        
        self.crawlers = crawler_map
        return self.crawlers

    def get_crawlers(self):
        return self.register().values()
