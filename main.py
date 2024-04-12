import json
import time

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


@_scheduler.scheduled_job('interval', id='crawler_logic', seconds=1800)
def crawlers_logic():
    retry_crawler = []
    for crawler_name, crawler in factory.items():
        try:
            news_list = crawler.fetch()
        except Exception as e:
            print(e)
            retry_crawler.append(crawler_name)
            continue

        if len(news_list) != 0:
            db.insert_news(news_list)
            print(f"{crawler_name}爬取成功，共爬取{len(news_list)}条新闻")
        else:
            retry_crawler.append(crawler_name)

    print(f"\n剩余爬取{len(retry_crawler)}个网站")
    for crawler_name in retry_crawler:
        crawler = factory[crawler_name]
        try:
            news_list = crawler.fetch()
        except Exception as e:
            print(e)
            continue

        if len(news_list) != 0:
            db.insert_news(news_list)
            print(f"{crawler_name}爬取成功，共爬取{len(news_list)}条新闻")

    print("爬取结束: ", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))


@app.get("/dailynews/")
def get_hot_news(date: str = time.strftime("%Y-%m-%d", time.localtime()), platform: str = None):
    if platform not in factory.keys():
        return {
            "status": "404",
            "data": [],
            "msg": "`platform` is required, valid platform: " + ", ".join(factory.keys())
        }

    result = cache._hget(date, platform).decode("utf-8")
    return {
        "status": "200",
        "data": json.loads(result),
        "msg": "success"
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=18080)
