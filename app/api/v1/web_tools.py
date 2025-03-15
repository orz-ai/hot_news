# app/api/endpoints/website_meta.py
import json
import time
from urllib.parse import urlparse, urljoin

import cloudscraper

from app.utils.logger import log

import requests
from bs4 import BeautifulSoup
from fastapi import APIRouter

from app.core import cache

router = APIRouter()


@router.get("/")
def get_meta(url: str = None):
    if not url:
        return {
            "status": "404",
            "data": [],
            "msg": "`url` is required"
        }

    # get from cache
    cached_metadata = cache._get(url)
    if cached_metadata:
        return {
            "status": "200",
            "data": json.loads(cached_metadata),
            "msg": "success",
            "cache": True
        }

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "zh-CN,zh;q=0.9,zh-TW;q=0.8,ar;q=0.7,en;q=0.6",
        "cache-control": "max-age=0",
        "priority": "u=0, i",
        "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
    }


    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        page_content = response.content
    except requests.RequestException as e:
        scraper = cloudscraper.create_scraper(delay=100)
        response = scraper.get(url)
        page_content = response.content

    if not page_content:
        return {
            "status": "404",
            "data": [],
            "msg": "No content"
        }

    soup = BeautifulSoup(page_content, "html.parser")
    meta_info = {
        "title": soup.title.string if soup.title else "No title",
        "description": "",
        "keywords": "",
        "author": "",
        "og:title": "",
        "og:description": "",
        "og:image": "",
        "og:url": url,
        "twitter:card": "",
        "twitter:title": "",
        "twitter:description": "",
        "twitter:image": ""
    }

    for meta_tag in soup.find_all("meta"):
        name_attr = meta_tag.get("name", "").lower()
        property_attr = meta_tag.get("property", "").lower()
        content = meta_tag.get("content", "")

        if name_attr == "description":
            meta_info["description"] = content
        elif name_attr == "keywords":
            meta_info["keywords"] = content
        elif name_attr == "author":
            meta_info["author"] = content

        elif property_attr == "og:title":
            meta_info["og:title"] = content
        elif property_attr == "og:description":
            meta_info["og:description"] = content
        elif property_attr == "og:image":
            meta_info["og:image"] = content
        elif property_attr == "og:url":
            meta_info["og:url"] = content

        elif name_attr == "twitter:card":
            meta_info["twitter:card"] = content
        elif name_attr == "twitter:title":
            meta_info["twitter:title"] = content
        elif name_attr == "twitter:description":
            meta_info["twitter:description"] = content
        elif name_attr == "twitter:image":
            meta_info["twitter:image"] = content

    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    favicon_url = urljoin(base_url, "favicon.ico")  # 默认 favicon 路径

    link_tag = soup.find("link", rel=["icon", "shortcut icon"])
    if link_tag:
        favicon_url = urljoin(base_url, link_tag.get("href", "favicon.ico"))

    metadata = {
        "meta_info": meta_info,
        "favicon_url": favicon_url
    }

    cache._set(url, json.dumps(metadata, ensure_ascii=False), ex=60)
    result = {
        "status": "200",
        "data": metadata,
        "msg": "Success",
        "cache": False
    }

    return result
