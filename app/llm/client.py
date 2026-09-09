import json
from typing import Any, Dict, List, Optional

import requests

from app.core.config import LLMConfig


class OpenAICompatibleClient:
    def __init__(self, config: LLMConfig):
        self.config = config

    def is_configured(self) -> bool:
        if self.config.provider.strip().lower() == "codex-responses":
            return bool(
                self.config.enabled
                and self.config.base_url.strip()
                and self.config.model.strip()
                and self.config.codex_token.strip()
                and self.config.codex_account_id.strip()
            )

        return bool(
            self.config.enabled
            and self.config.base_url.strip()
            and self.config.model.strip()
        )

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        if not self.is_configured():
            raise RuntimeError("LLM client is not fully configured")

        if self.config.provider.strip().lower() == "codex-responses":
            return self._codex_responses_completion(messages)

        url = self._build_chat_completion_url()
        headers = {
            "Content-Type": "application/json",
        }
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"

        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature if temperature is None else temperature,
            "max_tokens": self.config.max_tokens if max_tokens is None else max_tokens,
            "chat_template_kwargs": {"thinking": False}
        }

        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=self.config.timeout,
        )
        response_data = response.json()

        choices = response_data.get("choices") or []
        if not choices:
            raise RuntimeError("No choices returned from LLM API")

        message = choices[0].get("message") or {}
        content = message.get("content")
        if isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
            content = "\n".join(part for part in text_parts if part)

        if not content:
            raise RuntimeError("Empty content returned from LLM API")

        return content.strip()

    def _codex_responses_completion(self, messages: List[Dict[str, str]]) -> str:
        """调用 Codex Responses 接口并拼接 SSE 输出文本。"""
        if not self.config.stream:
            raise RuntimeError("codex-responses provider requires stream: true")

        input_items = []
        for message in messages:
            role = message.get("role", "user")
            # Responses API 使用 developer 角色承载原有的系统提示。
            if role == "system":
                role = "developer"
            input_items.append({
                "role": role,
                "content": [{
                    "type": "input_text",
                    "text": message.get("content", ""),
                }],
            })

        payload = {
            "model": self.config.model,
            "store": False,
            "stream": self.config.stream,
            "input": input_items,
        }
        headers = {
            "Authorization": f"Bearer {self.config.codex_token}",
            "ChatGPT-Account-Id": self.config.codex_account_id,
            "Content-Type": "application/json",
            "Origin": "https://chatgpt.com",
            "User-Agent": "Codex CLI",
        }

        response = requests.post(
            self.config.base_url,
            headers=headers,
            json=payload,
            timeout=self.config.timeout,
            stream=True,
        )
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise RuntimeError(
                f"Codex Responses request failed ({response.status_code}): {response.text}"
            ) from exc

        text_parts = []
        completed_response = None
        for line in response.iter_lines(decode_unicode=True):
            if isinstance(line, bytes):
                line = line.decode("utf-8", errors="replace")
            if not line or not line.startswith("data:"):
                continue

            data = line.removeprefix("data:").strip()
            if data == "[DONE]":
                break

            try:
                event = json.loads(data)
            except json.JSONDecodeError:
                continue

            if event.get("type") == "error" or event.get("error"):
                raise RuntimeError(f"Codex Responses API error: {event.get('error') or event}")
            if event.get("type") == "response.output_text.delta":
                delta = event.get("delta", "")
                if isinstance(delta, str):
                    text_parts.append(delta)
            elif event.get("type") == "response.completed":
                completed_response = event.get("response")

        content = "".join(text_parts).strip()
        if not content and isinstance(completed_response, dict):
            content = self._extract_responses_text(completed_response)
        if not content:
            raise RuntimeError("Empty content returned from Codex Responses API")
        return content

    @staticmethod
    def _extract_responses_text(response_data: Dict[str, Any]) -> str:
        """从 Responses 完整对象中提取文本，用于无 delta 的完成事件。"""
        text = response_data.get("output_text")
        if isinstance(text, str) and text.strip():
            return text.strip()

        text_parts = []
        for output_item in response_data.get("output") or []:
            for content_item in output_item.get("content") or []:
                if content_item.get("type") == "output_text":
                    value = content_item.get("text", "")
                    if isinstance(value, str) and value:
                        text_parts.append(value)
        return "\n".join(text_parts).strip()

    def _build_chat_completion_url(self) -> str:
        base_url = self.config.base_url.rstrip("/")
        if base_url.endswith("/chat/completions"):
            return base_url
        return f"{base_url}/chat/completions"
