from .crawler import Crawler
from .douyin import DouYinCrawler
from .ftpojie import FtPoJieCrawler
from .hupu import HuPuCrawler
from .juejin import JueJinCrawler
from .tieba import TieBaCrawler
from .tskr import TsKrCrawler
from .baidu import BaiduNewsCrawler
from .bilibili import BilibiliCrawler
from .douban import DouBanCrawler
from .sspai import ShaoShuPaiCrawler
from .vtex import VtexCrawler
from .weibo import WeiboCrawler
from .zhihu import ZhiHuCrawler


class CrawlerRegister:

    @staticmethod
    def register() -> dict[str, Crawler]:
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
        }

        return crawler_map

    def get_crawlers(self):
        return self.register().values()
