from __future__ import annotations

import os
import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ModelConfig:
    model: str
    base_url: str | None
    api_key: str
    temperature: float = 0.0
    timeout: float = 120.0
    extra_body: dict[str, Any] | None = None
    reasoning_effort: str | None = None

    @classmethod
    def from_env(
        cls,
        model: str | None = None,
        temperature: float = 0.0,
        timeout: float = 120.0,
        extra_body: dict[str, Any] | None = None,
        reasoning_effort: str | None = None,
    ) -> "ModelConfig":
        selected_model = model or os.environ.get("MODEL")
        if not selected_model:
            raise ValueError("model is required via --model or MODEL")
        effort = reasoning_effort or os.environ.get("OPENAI_REASONING_EFFORT")
        merged_extra_body = _extra_body_from_env()
        if extra_body:
            merged_extra_body.update(extra_body)
        return cls(
            model=selected_model,
            base_url=os.environ.get("OPENAI_BASE_URL"),
            api_key=os.environ.get("OPENAI_API_KEY") or os.environ.get("DASHSCOPE_API_KEY", "EMPTY"),
            temperature=temperature,
            timeout=timeout,
            extra_body=merged_extra_body or None,
            reasoning_effort=effort,
        )


class OpenAICompatibleClient:
    def __init__(self, config: ModelConfig) -> None:
        try:
            from openai import OpenAI
        except ModuleNotFoundError as exc:
            raise RuntimeError("openai package is required. Install with: pip install -r requirements.txt") from exc

        kwargs: dict[str, str] = {"api_key": config.api_key}
        if config.base_url:
            kwargs["base_url"] = config.base_url
        self.client = OpenAI(**kwargs)
        self.config = config

    def complete(self, messages: list[dict[str, str]]) -> str:
        request: dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "timeout": self.config.timeout,
        }
        if self.config.extra_body:
            request["extra_body"] = self.config.extra_body
        if self.config.reasoning_effort:
            request["reasoning_effort"] = self.config.reasoning_effort
        response = self.client.chat.completions.create(
            **request,
        )
        content = response.choices[0].message.content
        if not content:
            raise RuntimeError("model returned empty content")
        return content.strip()


def _extra_body_from_env() -> dict[str, Any]:
    body: dict[str, Any] = {}
    raw = os.environ.get("OPENAI_EXTRA_BODY_JSON")
    if raw:
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            raise ValueError("OPENAI_EXTRA_BODY_JSON must decode to a JSON object")
        body.update(parsed)
    enable_thinking = os.environ.get("OPENAI_ENABLE_THINKING")
    if enable_thinking:
        body["enable_thinking"] = enable_thinking.strip().lower() in {"1", "true", "yes", "on"}
    return body
