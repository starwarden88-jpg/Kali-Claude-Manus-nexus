"""
Prompt Cache — Reuse expensive system prompts across API calls.

Anthropic's prompt caching lets you mark content blocks with
cache_control so identical prefixes aren't re-processed on
subsequent requests. This module manages that automatically.

Token savings: Up to 90% on cached input tokens (billed at 10% rate).
Latency savings: Cached prefixes skip processing entirely.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CacheEntry:
    """A cached prompt block with its hash for deduplication."""
    content_hash: str
    block: dict[str, Any]
    hit_count: int = 0


class PromptCache:
    """Manages prompt caching for Anthropic API calls.

    Usage:
        cache = PromptCache()

        # Register your static system prompt once
        cache.register_system_prompt("You are a security analyst...")

        # Build requests — system prompt is automatically cached
        request = cache.build_cached_request(
            messages=[{"role": "user", "content": "Scan this code"}],
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
        )
    """

    def __init__(self) -> None:
        self._system_blocks: list[CacheEntry] = []
        self._tool_blocks: list[CacheEntry] = []
        self._stats: dict[str, int] = {"cache_hits": 0, "cache_misses": 0}

    @staticmethod
    def _hash(content: str) -> str:
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def register_system_prompt(self, text: str) -> None:
        """Register a static system prompt for caching.

        The last block in the system array gets cache_control applied,
        following Anthropic's caching rules.
        """
        h = self._hash(text)
        # Don't duplicate
        if any(e.content_hash == h for e in self._system_blocks):
            return

        self._system_blocks.append(
            CacheEntry(
                content_hash=h,
                block={
                    "type": "text",
                    "text": text,
                    "cache_control": {"type": "ephemeral"},
                },
            )
        )

    def register_tool_definitions(self, tools: list[dict[str, Any]]) -> None:
        """Register tool definitions for caching.

        Tool definitions are sent on every request and rarely change —
        prime candidates for caching.
        """
        content = json.dumps(tools, sort_keys=True)
        h = self._hash(content)

        if any(e.content_hash == h for e in self._tool_blocks):
            return

        self._tool_blocks.append(
            CacheEntry(content_hash=h, block=tools)
        )

    def build_cached_request(
        self,
        messages: list[dict[str, Any]],
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 1024,
        temperature: float = 0.0,
        stream: bool = True,
        extra_system: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Build an API request with cached system/tool blocks.

        Args:
            messages: Conversation messages.
            model: Model ID.
            max_tokens: Output token budget.
            temperature: Sampling temperature.
            stream: Whether to stream the response.
            extra_system: Additional non-cached system text appended
                          after the cached blocks.
        """
        request: dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": stream,
            "messages": messages,
        }

        # Build system array with cache_control on cached blocks
        system_blocks = [e.block for e in self._system_blocks]
        if extra_system:
            system_blocks.append({"type": "text", "text": extra_system})

        if system_blocks:
            request["system"] = system_blocks

        # Apply cache_control to tool definitions
        if self._tool_blocks:
            tools = []
            for entry in self._tool_blocks:
                tool_list = entry.block
                if isinstance(tool_list, list) and tool_list:
                    # Apply cache_control to the last tool in the list
                    for i, tool in enumerate(tool_list):
                        t = dict(tool)
                        if i == len(tool_list) - 1:
                            t["cache_control"] = {"type": "ephemeral"}
                        tools.append(t)
            if tools:
                request["tools"] = tools

        request.update(kwargs)
        return request

    def get_stats(self) -> dict[str, Any]:
        """Return cache usage statistics."""
        return {
            "registered_system_blocks": len(self._system_blocks),
            "registered_tool_blocks": len(self._tool_blocks),
            **self._stats,
        }

    def update_stats_from_response(self, usage: dict[str, int]) -> None:
        """Update cache stats from an API response's usage field.

        The API returns cache_creation_input_tokens and
        cache_read_input_tokens in the usage object.
        """
        cache_read = usage.get("cache_read_input_tokens", 0)
        cache_creation = usage.get("cache_creation_input_tokens", 0)

        if cache_read > 0:
            self._stats["cache_hits"] += 1
        if cache_creation > 0:
            self._stats["cache_misses"] += 1

        self._stats.setdefault("total_cache_read_tokens", 0)
        self._stats["total_cache_read_tokens"] += cache_read
        self._stats.setdefault("total_cache_creation_tokens", 0)
        self._stats["total_cache_creation_tokens"] += cache_creation
