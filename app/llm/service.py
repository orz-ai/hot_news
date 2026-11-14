from datetime import datetime
from typing import Any, Dict, List, Optional

import pytz

from app.core import cache
from app.core.config import LLMConfig, get_llm_config
from app.db.redis import get_redis_client
from app.llm.client import OpenAICompatibleClient
from app.llm.prompts import build_hot_summary_messages
from app.llm.schemas import HotNewsItem, HotSummaryResult
from app.utils.logger import log


SHANGHAI_TZ = pytz.timezone("Asia/Shanghai")


class HotSummaryService:
    def __init__(self, llm_config: Optional[LLMConfig] = None):
        self.llm_config = llm_config or get_llm_config()
        self.client = OpenAICompatibleClient(self.llm_config)
        self.cache_key_prefix = "llm:hot_summary:"
        self.latest_cache_key = "llm:hot_summary:latest"

    def get_summary(self, date_str: Optional[str] = None, refresh: bool = False) -> Dict[str, Any]:
        date_str = date_str or self._get_today_str()

        if not self.llm_config.enabled:
            return {
                "status": "disabled",
                "message": "LLM 热点总结功能未启用",
                "date": date_str,
            }

        cache_key = self._build_date_cache_key(date_str)
        if not refresh:
            cached_data = cache.get_cache(cache_key)
            if cached_data:
                log.info(f"Retrieved LLM hot summary from cache for {date_str}")
                return cached_data

        return self.generate_summary(date_str)

    def get_latest_summary(self) -> Dict[str, Any]:
        if not self.llm_config.enabled:
            return {
                "status": "disabled",
                "message": "LLM 热点总结功能未启用",
                "date": self._get_today_str(),
            }

        latest_summary = cache.get_cache(self.latest_cache_key)
        if latest_summary:
            return latest_summary

        return self.get_summary()

    def generate_summary(self, date_str: Optional[str] = None) -> Dict[str, Any]:
        date_str = date_str or self._get_today_str()

        if not self.client.is_configured():
            return {
                "status": "disabled",
                "message": "LLM 配置不完整，已跳过热点总结生成",
                "date": date_str,
            }

        news_items = self._load_news_items(date_str)
        if not news_items:
            return {
                "status": "empty",
                "message": "暂无热点数据可生成总结",
                "date": date_str,
            }

        previous_summary = self._get_previous_summary(date_str)
        messages = build_hot_summary_messages(date_str, previous_summary, news_items)

        try:
            summary_text = self.client.chat_completion(messages)
        except Exception as exc:
            log.error(f"Error generating LLM hot summary for {date_str}: {exc}")
            return {
                "status": "error",
                "message": str(exc),
                "date": date_str,
            }

        result = HotSummaryResult(
            status="success",
            message="LLM 热点总结生成完成",
            date=date_str,
            summary=summary_text,
            previous_summary_date=previous_summary.get("date") if previous_summary else None,
            news_count=len(news_items),
            platforms=sorted({item.platform for item in news_items}),
            generated_at=datetime.now(SHANGHAI_TZ).isoformat(),
        ).dict()

        self._save_summary(date_str, result)
        return result

    def _load_news_items(self, date_str: str) -> List[HotNewsItem]:
        redis_client = get_redis_client()
        keys = redis_client.keys(f"crawler:*:{date_str}")
        if not keys:
            return []

        normalized_keys = []
        for key in keys:
            if isinstance(key, bytes):
                normalized_keys.append(key.decode("utf-8"))
            else:
                normalized_keys.append(key)

        selected_platforms = set(self.llm_config.summary_platforms or [])

        collected_items: List[HotNewsItem] = []
        for key in sorted(normalized_keys):
            parts = key.split(":")
            platform = parts[1] if len(parts) >= 3 else "unknown"
            if selected_platforms and platform not in selected_platforms:
                continue
            platform_news = cache.get_cache(key) or []
            platform_count = 0
            for news in platform_news:
                if platform_count >= self.llm_config.summary_platform_news_limit:
                    break
                if not isinstance(news, dict):
                    continue
                collected_items.append(
                    HotNewsItem(
                        platform=platform,
                        title=str(news.get("title", "")).strip(),
                        url=str(news.get("url", "")).strip(),
                        content=str(news.get("content") or news.get("desc") or "").strip(),
                        score=news.get("score") or news.get("hot"),
                        rank=news.get("rank"),
                    )
                )
                platform_count += 1
        return [item for item in collected_items if item.title]

    def _get_previous_summary(self, date_str: str) -> Optional[Dict[str, Any]]:
        latest_summary = cache.get_cache(self.latest_cache_key)
        if latest_summary and latest_summary.get("summary"):
            return latest_summary

        redis_client = get_redis_client()
        keys = redis_client.keys(f"{self.cache_key_prefix}*")
        date_candidates = []
        for key in keys:
            normalized_key = key.decode("utf-8") if isinstance(key, bytes) else key
            if normalized_key == self.latest_cache_key:
                continue
            date_value = normalized_key.replace(self.cache_key_prefix, "", 1)
            if date_value and date_value < date_str:
                date_candidates.append(date_value)

        if not date_candidates:
            return None

        previous_date = sorted(date_candidates)[-1]
        return cache.get_cache(self._build_date_cache_key(previous_date))

    @staticmethod
    def is_due(llm_config: Optional[LLMConfig] = None) -> bool:
        config = llm_config or get_llm_config()
        interval = config.summary_interval
        if interval <= 0:
            return True

        latest_summary = cache.get_cache("llm:hot_summary:latest")
        generated_at = (latest_summary or {}).get("generated_at")
        if not generated_at:
            return True

        try:
            last_time = datetime.fromisoformat(generated_at)
        except (TypeError, ValueError):
            return True

        if last_time.tzinfo is None:
            last_time = SHANGHAI_TZ.localize(last_time)

        return (datetime.now(SHANGHAI_TZ) - last_time).total_seconds() >= interval

    def should_generate_summary(self) -> bool:
        return self.is_due(self.llm_config)

    def _save_summary(self, date_str: str, result: Dict[str, Any]) -> None:
        expire = self.llm_config.summary_expire
        cache.set_cache(self._build_date_cache_key(date_str), result, expire)
        cache.set_cache(self.latest_cache_key, result, expire)

    def _build_date_cache_key(self, date_str: str) -> str:
        return f"{self.cache_key_prefix}{date_str}"

    def _get_today_str(self) -> str:
        return datetime.now(SHANGHAI_TZ).strftime("%Y-%m-%d")
