from datetime import datetime

import pytz


class Crawler:
    header = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,"
                  "*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/86.0.4240.183 Safari/537.36",
        'accept-language': 'zh-CN,zh-Hans;q=0.9',
        'accept-encoding': 'gzip, deflate, br',
    }

    proxy = {
        "http": "http://127.0.0.1:7890",
        "https": "http://127.0.0.1:7890"
    }

    timezone = pytz.timezone('Asia/Shanghai')
    now_time = datetime.now(timezone)
    date_str = now_time.strftime("%Y-%m-%d")

    timeout = 2

    def fetch(self):
        raise NotImplementedError("Subclasses must implement fetch method")

    def crawler_name(self):
        raise NotImplementedError("Subclasses must implement crawler_name method")
