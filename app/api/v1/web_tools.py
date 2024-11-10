# app/api/endpoints/website_meta.py
import json
from urllib.parse import urlparse, urljoin
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
            "msg": "success"
        }

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
    }

    try:
        # 请求网页内容
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        return {
            "status": "500",
            "data": [],
            "msg": f"Failed to fetch page content: {e}"
        }

    # 解析网页内容
    soup = BeautifulSoup(response.content, "html.parser")

    # 提取 meta 信息
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

    # 查找常见的 meta 信息
    for meta_tag in soup.find_all("meta"):
        name_attr = meta_tag.get("name", "").lower()
        property_attr = meta_tag.get("property", "").lower()
        content = meta_tag.get("content", "")

        # 匹配标准 meta 信息
        if name_attr == "description":
            meta_info["description"] = content
        elif name_attr == "keywords":
            meta_info["keywords"] = content
        elif name_attr == "author":
            meta_info["author"] = content

        # 匹配 Open Graph 协议 (og:) 信息
        elif property_attr == "og:title":
            meta_info["og:title"] = content
        elif property_attr == "og:description":
            meta_info["og:description"] = content
        elif property_attr == "og:image":
            meta_info["og:image"] = content
        elif property_attr == "og:url":
            meta_info["og:url"] = content

        # 匹配 Twitter 卡片信息
        elif name_attr == "twitter:card":
            meta_info["twitter:card"] = content
        elif name_attr == "twitter:title":
            meta_info["twitter:title"] = content
        elif name_attr == "twitter:description":
            meta_info["twitter:description"] = content
        elif name_attr == "twitter:image":
            meta_info["twitter:image"] = content

    # 提取 favicon 图标链接
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    favicon_url = urljoin(base_url, "favicon.ico")  # 默认 favicon 路径

    # 尝试从 link 标签中查找 favicon
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
        "msg": "Success"
    }

    return result
