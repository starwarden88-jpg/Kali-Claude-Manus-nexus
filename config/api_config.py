"""
KLMC Nexus API Configuration — Token-Efficient Defaults

Key strategies:
1. Prompt caching: Static system prompts get cache_control to avoid re-processing
2. Explicit max_tokens: Every call has a budget — no runaway completions
3. Streaming: Enabled by default for faster perceived latency
4. Task-specific budgets: Different tasks get different token limits
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class TokenBudget:
    """Per-task token limits to prevent waste."""
    max_input: int
    max_output: int

    @property
    def total(self) -> int:
        return self.max_input + self.max_output


# Task-specific budgets — tune these based on actual usage patterns
TASK_BUDGETS: dict[str, TokenBudget] = {
    "quick_answer":    TokenBudget(max_input=1_000,  max_output=300),
    "code_review":     TokenBudget(max_input=4_000,  max_output=1_500),
    "code_generation": TokenBudget(max_input=4_000,  max_output=4_000),
    "security_scan":   TokenBudget(max_input=8_000,  max_output=2_000),
    "summarize":       TokenBudget(max_input=8_000,  max_output=1_000),
    "full_analysis":   TokenBudget(max_input=16_000, max_output=4_000),
}


@dataclass
class APIConfig:
    """Token-optimized API configuration for Claude."""

    model: str = "claude-sonnet-4-20250514"
    api_key: str = field(default_factory=lambda: os.environ.get("ANTHROPIC_API_KEY", ""))
    base_url: str = "https://api.anthropic.com"

    # -- Token efficiency settings --
    default_max_tokens: int = 1024
    stream: bool = True
    temperature: float = 0.0  # Deterministic = fewer retries = fewer tokens

    # -- Prompt caching --
    enable_prompt_caching: bool = True
    cache_static_system_prompt: bool = True

    def get_budget(self, task: str) -> TokenBudget:
        return TASK_BUDGETS.get(task, TokenBudget(max_input=4_000, max_output=1_024))

    def build_request(
        self,
        messages: list[dict[str, Any]],
        system: str | None = None,
        task: str = "quick_answer",
        **overrides: Any,
    ) -> dict[str, Any]:
        """Build a token-efficient API request.

        Automatically applies:
        - Task-specific max_tokens budget
        - Prompt caching on the system prompt
        - Streaming
        """
        budget = self.get_budget(task)

        request: dict[str, Any] = {
            "model": self.model,
            "max_tokens": budget.max_output,
            "messages": messages,
            "stream": self.stream,
            "temperature": self.temperature,
        }

        # Apply prompt caching to static system prompt
        if system:
            if self.enable_prompt_caching and self.cache_static_system_prompt:
                request["system"] = [
                    {
                        "type": "text",
                        "text": system,
                        "cache_control": {"type": "ephemeral"},
                    }
                ]
            else:
                request["system"] = system

        request.update(overrides)
        return request

    def build_messages_compact(
        self,
        conversation: list[dict[str, Any]],
        keep_last_n: int = 10,
    ) -> list[dict[str, Any]]:
        """Trim conversation history to keep only the most recent exchanges.

        Older messages are summarized into a single context message to
        preserve meaning while drastically cutting input tokens.
        """
        if len(conversation) <= keep_last_n:
            return conversation

        old = conversation[:-keep_last_n]
        recent = conversation[-keep_last_n:]

        # Compress old messages into a brief context summary
        summary_parts = []
        for msg in old:
            role = msg["role"]
            content = msg["content"] if isinstance(msg["content"], str) else str(msg["content"])
            # Take first 80 chars of each old message as a hint
            summary_parts.append(f"[{role}]: {content[:80]}...")

        context_msg = {
            "role": "user",
            "content": (
                "[Prior conversation summary — details truncated to save tokens]\n"
                + "\n".join(summary_parts)
            ),
        }

        # Ensure conversation starts with user message
        if recent[0]["role"] == "assistant":
            return [context_msg] + recent
        return [context_msg, {"role": "assistant", "content": "Understood."}, *recent]


# Singleton for import convenience
config = APIConfig()
