[中文](README.md)

# Daily Hot News API

## Overview

The Daily Hot News API provides access to real-time hot news data from various platforms. The data is refreshed automatically about every half an hour. This API can be used to retrieve hot news headlines along with their URLs and scores.

- **Base URL**: `https://orz.ai/dailynews/`

## Usage

- **Method**: `GET`
- **Parameters**:
  - `platform`: Specify the platform. Supported platforms are:
	  - [x] baidu
	  - [x] shaoshupai
	  - [x] weibo
	  - [x] zhihu
	  - [x] 36kr
	  - [x] 52pojie
	  - [x] bilibili
	  - [x] douban
	  - [x] hupu
	  - [x] tieba
	  - [x] juejin
	  - [x] douyin
	  - [x] v2ex
      - [x] jinritoutiao

- **Example Request**:
  ```shell
  GET https://orz.ai/dailynews/?platform=baidu
  ```

- **Example Response**:
  ```json
  {
    "status": "200",
    "data": [
      {
        "title": "32岁“母单”女孩：6年相亲百人",
        "url": "https://www.baidu.com/s?word=32%E5%B2%81%E2%80%9C%E6%AF%8D%E5%8D%95%E2%80%9D%E5%A5%B3%E5%AD%A9%EF%BC%9A6%E5%B9%B4%E7%9B%B8%E4%BA%B2%E7%99%BE%E4%BA%BA&sa=fyb_news",
        "score": "4955232",
        "desc": ""
      },
      {
        "title": "女高中生被父母退学：打工卖包子",
        "url": "https://www.baidu.com/s?word=%E5%A5%B3%E9%AB%98%E4%B8%AD%E7%94%9F%E8%A2%AB%E7%88%B6%E6%AF%8D%E9%80%80%E5%AD%A6%EF%BC%9A%E6%89%93%E5%B7%A5%E5%8D%96%E5%8C%85%E5%AD%90&sa=fyb_news",
        "score": "100000",
        "desc": "近日，一名高二女生被父母强制辍学去广东打工卖包子，引发热议。26日，当地教育局回应：已经妥善处理了，女生已复学。"
      }
    ],
    "msg": "success"
  }
  ```

## Notes

- This API is for legal use only. `Any illegal use is not supported` and is the responsibility of the user.
- The data provided by this API is for informational purposes only and should not be used as a primary platform of news.

## Rate Limiting

There is currently `no explicit rate limiting` on this API, but please use it responsibly to avoid overloading the server.

## Disclaimer

The information provided by this API may not always be accurate or up-to-date. Users should verify the information from other platforms before relying on it.

## Telegram Bot
[Link](https://t.me/SpaceWatcherBot)

You can use the bot directly or add it to your group.

If you want to deploy the bot by yourself, you should set the `TG_BOT_TOKEN` in the environment variables and then run the following command: `python3 news_tg_bot.py`