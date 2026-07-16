"""LLM provider interface — direct LLM calls for standalone execution.

NOTE: This is a fallback for when Hermes Agent CLI is not available.
The primary Elysium-Bench execution path uses `hermes run --skill elysium-swarmloop`,
which lets Hermes handle the LLM provider/model configuration internally.
"""

from __future__ import annotations

import httpx
import os
import re
import subprocess
import sys
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class LLMProvider(ABC):
    """Abstract base for LLM providers (fallback mode)."""

    def __init__(self, model: str, config: dict[str, Any]):
        self.model = model
        self.config = config

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str, timeout: int) -> str:
        ...


class OpenAILikeProvider(LLMProvider):
    """OpenAI-compatible APIs."""

    def generate(self, system_prompt: str, user_prompt: str, timeout: int) -> str:
        api_key = self.config.get("api_key") or os.environ.get(self.config.get("env_key", "OPENAI_API_KEY"))
        base_url = self.config.get("base_url", "https://api.openai.com/v1")
        if not api_key:
            raise ValueError(f"No API key. Set {self.config.get('env_key', 'OPENAI_API_KEY')} env var.")

        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": self.config.get("temperature", 0.3),
            "max_tokens": self.config.get("max_tokens", 8000),
        }
        with httpx.Client(timeout=timeout + 30, follow_redirects=True) as client:
            resp = client.post(f"{base_url}/chat/completions", json=payload, headers=headers)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]


class OllamaProvider(LLMProvider):
    """Local Ollama."""

    def generate(self, system_prompt: str, user_prompt: str, timeout: int) -> str:
        base_url = self.config.get("base_url", "http://localhost:11434")
        payload = {
            "model": self.model,
            "system": system_prompt,
            "prompt": user_prompt,
            "options": {"temperature": self.config.get("temperature", 0.3), "num_predict": self.config.get("max_tokens", 8000)},
            "stream": False,
        }
        with httpx.Client(timeout=timeout + 30) as client:
            resp = client.post(f"{base_url}/api/generate", json=payload)
            resp.raise_for_status()
            return resp.json().get("response", "")


class AnthropicProvider(LLMProvider):
    """Anthropic Claude."""

    def generate(self, system_prompt: str, user_prompt: str, timeout: int) -> str:
        api_key = self.config.get("api_key") or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("No Anthropic API key. Set ANTHROPIC_API_KEY env var.")
        headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
        payload = {
            "model": self.model,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
            "temperature": self.config.get("temperature", 0.3),
            "max_tokens": self.config.get("max_tokens", 8000),
        }
        with httpx.Client(timeout=timeout + 30) as client:
            resp = client.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers)
            resp.raise_for_status()
            return resp.json()["content"][0]["text"]


def create_llm_provider(llm_config: dict[str, Any] | None) -> LLMProvider | None:
    """Factory: returns LLMProvider or None if disabled."""
    if not llm_config or not llm_config.get("enabled", False):
        return None
    provider_name = llm_config.get("provider", "ollama")
    model = llm_config.get("model", "qwen2.5:7b")
    base_config = {k: v for k, v in llm_config.items() if k not in ("provider", "model", "enabled")}

    providers = {
        "openai": lambda: OpenAILikeProvider(model=model, config=base_config | {"env_key": "OPENAI_API_KEY"}),
        "anthropic": lambda: AnthropicProvider(model=model, config=base_config),
        "ollama": lambda: OllamaProvider(model=model, config=base_config),
        "openrouter": lambda: OpenAILikeProvider(model=model, config=base_config | {"base_url": "https://openrouter.ai/api/v1", "env_key": "OPENROUTER_API_KEY"}),
        "together": lambda: OpenAILikeProvider(model=model, config=base_config | {"base_url": "https://api.together.xyz/v1", "env_key": "TOGETHER_API_KEY"}),
    }
    factory = providers.get(provider_name)
    if not factory:
        raise ValueError(f"Unknown provider: {provider_name}")
    return factory()
