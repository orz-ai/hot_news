import json
import logging as log
import time
import traceback
from datetime import datetime

import pytz
import uvicorn
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI

import cache
import db
from sites.factory import CrawlerRegister

app = FastAPI()
_scheduler = BackgroundScheduler()
_scheduler.start()

factory = CrawlerRegister().register()

log.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=log.INFO
)


@_scheduler.scheduled_job('interval', id='crawler_logic', seconds=1800)
def crawlers_logic():
    retry_crawler = []

    timezone = pytz.timezone('Asia/Shanghai')
    now_time = datetime.now(timezone)
    date_str = now_time.strftime("%Y-%m-%d")

    for crawler_name, crawler in factory.items():
        try:
            news_list = crawler.fetch(date_str)
        except Exception as e:
            log.error("first time crawler %s error: %s" % (crawler_name, traceback.format_exc()))
            retry_crawler.append(crawler_name)
            continue

        if len(news_list) != 0:
            db.insert_news(news_list)
            log.info(f"{crawler_name}爬取成功，共爬取{len(news_list)}条新闻")
        else:
            retry_crawler.append(crawler_name)
            log.info(f"{crawler_name}爬取失败，爬取到0条新闻")

    log.info(f"剩余爬取{len(retry_crawler)}个网站，开始重试爬取")
    for crawler_name in retry_crawler:
        crawler = factory[crawler_name]
        try:
            news_list = crawler.fetch(date_str)
            if len(news_list) != 0:
                db.insert_news(news_list)
                log.info(f"{crawler_name}爬取成功，共爬取{len(news_list)}条新闻")
            else:
                log.info(f"第二次重试{crawler_name}爬取失败，爬取到0条新闻")
        except Exception as e:
            log.error("second time crawler %s error: %s" % (crawler_name, traceback.format_exc()))
            continue

    log.info("爬取结束: " + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))


@app.get("/dailynews/")
def get_hot_news(date: str = None, platform: str = None):
    if platform not in factory.keys():
        return {
            "status": "404",
            "data": [],
            "msg": "`platform` is required, valid platform: " + ", ".join(factory.keys())
        }

    if not date:
        date = datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d")

    result = cache._hget(date, platform)
    if result:
        return {
            "status": "200",
            "data": json.loads(result.decode("utf-8")),
            "msg": "success"
        }

    return {
        "status": "200",
        "data": [],
        "msg": "success"
    }


if __name__ == "__main__":
    crawlers_logic()
    uvicorn.run(app, host="0.0.0.0", port=18080)
