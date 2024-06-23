from datetime import datetime

import pytz

timezone = pytz.timezone('Asia/Shanghai')
now_time = datetime.now(timezone)
date_str = now_time.strftime("%Y-%m-%d")


class TestCrawler:

    def test_init(self):
        pass

    def test_crawler(self):
        from sites.hupu import HuPuCrawler

        crawler = HuPuCrawler()
        crawler.fetch(date_str)


if __name__ == '__main__':
    test = TestCrawler()
    test.test_crawler()
