from .baidu import BaiduNewsCrawler
from .bilibili import BilibiliCrawler
from .crawler import Crawler
from .douban import DouBanCrawler
from .douyin import DouYinCrawler
from .ftpojie import FtPoJieCrawler
from .hupu import HuPuCrawler
from .jinritoutiao import JinRiTouTiaoCrawler
from .juejin import JueJinCrawler
from .sspai import ShaoShuPaiCrawler
from .tieba import TieBaCrawler
from .tskr import TsKrCrawler
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
            "jinritoutiao": JinRiTouTiaoCrawler(),
        }

        return crawler_map

    def get_crawlers(self):
        return self.register().values()
