[English](README_EN.md)

# 每日热点新闻 API

## 概述

每日热点新闻 API 提供来自多个平台的实时热点新闻数据。数据大约每半小时自动刷新一次。此 API 可用于检索热点新闻标题及其 URL 和评分。

- **基础 URL**: `https://orz.ai/api/v1/dailynews`

## 使用方法

- **方法**: `GET`
- **参数**:
  - `platform`: 指定平台。支持的平台有：
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

- **请求示例**:
  ```shell
  GET https://orz.ai/api/v1/dailynews/?platform=baidu
  ```

- **响应示例**:
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

## 注意事项

- 此 API 仅供合法使用。`任何非法使用均不受支持`，且由用户自行负责。
- 本 API 提供的数据仅供参考，不应作为新闻的主要来源。

## 速率限制

目前此 API `没有明确的速率限制`，但请合理使用以避免服务器过载。

## 免责声明

本 API 提供的信息可能并非始终准确或最新。用户应在依赖这些信息之前从其他平台进行验证。


## Telegram机器人
[链接](https://t.me/SpaceWatcherBot)

你可以直接使用机器人或添加到你的群组中。如果你想自己部署，你需要在环境变量中设置好 `TG_BOT_TOKEN`，再执行下面的命令：`python3 news_tg_bot.py`

## 网站基础信息接口

[https://orz.ai/api/v1/tools/website-meta/?url=https://v2ex.com/](https://orz.ai/api/v1/tools/website-meta/?url=https://v2ex.com/)

使用方法：`GET`
```shell
GET https://orz.ai/api/v1/tools/website-meta/?url=https://v2ex.com/

{
  "status": "200",
  "data": {
    "meta_info": {
      "title": "V2EX",
      "description": "创意工作者的社区。讨论编程、设计、硬件、游戏等令人激动的话题。",
      "keywords": "",
      "author": "",
      "og:title": "",
      "og:description": "",
      "og:image": "/static/icon-192.png",
      "og:url": "https://v2ex.com/",
      "twitter:card": "",
      "twitter:title": "",
      "twitter:description": "",
      "twitter:image": "/static/icon-192.png"
    },
    "favicon_url": "https://v2ex.com/static/icon-192.png"
  },
  "msg": "Success"
}

```