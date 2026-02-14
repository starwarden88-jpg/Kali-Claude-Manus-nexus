"""
KLMC Nexus Client — Token-efficient Claude API wrapper.

Combines all optimization strategies into one easy-to-use client:
- Prompt caching (system prompts + tools cached automatically)
- Conversation compaction (old messages summarized)
- Token budgets per task type
- Prompt compression before sending
- Usage tracking and reporting

Usage:
    from klmc_client import KLMCClient

    client = KLMCClient()
    response = client.ask("What ports are commonly targeted in a scan?")
    response = client.review_code("def foo(): eval(input())", language="python")
"""

from __future__ import annotations

import json
from typing import Any

from config.api_config import APIConfig, config as default_config
from config.prompts.templates import TEMPLATES, PromptTemplate
from utils.prompt_cache import PromptCache
from utils.token_optimizer import TokenOptimizer


class KLMCClient:
    """High-level client that enforces token efficiency on every call."""

    def __init__(self, api_config: APIConfig | None = None) -> None:
        self.config = api_config or default_config
        self.cache = PromptCache()
        self.optimizer = TokenOptimizer()
        self._conversation: list[dict[str, Any]] = []
        self._total_input_tokens: int = 0
        self._total_output_tokens: int = 0
        self._total_cache_read_tokens: int = 0

    # -- High-level task methods --

    def ask(self, question: str) -> dict[str, Any]:
        """Quick question — minimal token budget."""
        template = TEMPLATES["quick_answer"]
        return self._run_template(template, question=question)

    def review_code(self, code: str, language: str = "python") -> dict[str, Any]:
        """Security code review — returns JSON findings."""
        template = TEMPLATES["code_review"]
        return self._run_template(template, code=code, language=language)

    def scan(self, target: str, context: str = "web application") -> dict[str, Any]:
        """Vulnerability scan prompt — returns JSON findings."""
        template = TEMPLATES["vuln_scan"]
        return self._run_template(template, target=target, context=context)

    def summarize(self, text: str) -> dict[str, Any]:
        """Summarize long text — capped output."""
        template = TEMPLATES["summarize"]
        return self._run_template(template, text=text)

    def generate_code(
        self, task: str, language: str = "python", constraints: str = "none"
    ) -> dict[str, Any]:
        """Generate code — no boilerplate, no filler."""
        template = TEMPLATES["code_gen"]
        return self._run_template(
            template, task=task, language=language, constraints=constraints
        )

    def plan_pentest(
        self, scope: str, objective: str, constraints: str = "standard rules of engagement"
    ) -> dict[str, Any]:
        """Generate a pentest plan for authorized engagements."""
        template = TEMPLATES["pentest_plan"]
        return self._run_template(
            template, scope=scope, objective=objective, constraints=constraints
        )

    # -- Conversation management --

    def chat(self, message: str, task: str = "quick_answer") -> dict[str, Any]:
        """Multi-turn chat with automatic conversation compaction."""
        # Compress the user message
        compressed = self.optimizer.compress_prompt(message)
        self._conversation.append({"role": "user", "content": compressed.compressed})

        # Compact conversation if it's getting long
        messages = self.config.build_messages_compact(
            self._conversation, keep_last_n=10
        )

        request = self.config.build_request(
            messages=messages,
            system="Concise security AI assistant. Be direct.",
            task=task,
        )

        return self._prepare_response(request)

    # -- Usage tracking --

    def usage_report(self) -> str:
        """Report total token usage for this session."""
        saved = self._total_cache_read_tokens
        effective_input = self._total_input_tokens - (saved * 0.9)
        return (
            f"=== KLMC Nexus Token Usage ===\n"
            f"Input tokens:       {self._total_input_tokens:,}\n"
            f"Output tokens:      {self._total_output_tokens:,}\n"
            f"Cache read tokens:  {self._total_cache_read_tokens:,}\n"
            f"Effective input:    {effective_input:,.0f} (after cache savings)\n"
            f"Cache savings:      ~{saved * 0.9:,.0f} tokens\n"
        )

    # -- Internal methods --

    def _run_template(self, template: PromptTemplate, **kwargs: Any) -> dict[str, Any]:
        """Render a template and build a cached request."""
        rendered = template.render(**kwargs)

        # Register system prompt for caching
        system_text = rendered["system"]
        self.cache.register_system_prompt(system_text)

        request = self.cache.build_cached_request(
            messages=rendered["messages"],
            model=self.config.model,
            max_tokens=rendered.get("max_tokens", template.suggested_max_tokens),
            temperature=self.config.temperature,
            stream=self.config.stream,
        )

        return self._prepare_response(request)

    def _prepare_response(self, request: dict[str, Any]) -> dict[str, Any]:
        """Finalize a request dict. In production, this calls the API.

        Currently returns the request for inspection/testing.
        Wire up `anthropic.Anthropic().messages.create(**request)` to go live.
        """
        # Estimate tokens for tracking
        msg_text = json.dumps(request.get("messages", []))
        sys_text = json.dumps(request.get("system", ""))
        self._total_input_tokens += self.optimizer.count_tokens(msg_text + sys_text)

        return {
            "request": request,
            "estimated_input_tokens": self.optimizer.count_tokens(msg_text + sys_text),
            "max_output_tokens": request.get("max_tokens", 1024),
            "cache_stats": self.cache.get_stats(),
        }

    def track_response(self, api_response_usage: dict[str, int]) -> None:
        """Call after receiving an API response to track actual usage."""
        self._total_input_tokens += api_response_usage.get("input_tokens", 0)
        self._total_output_tokens += api_response_usage.get("output_tokens", 0)
        self._total_cache_read_tokens += api_response_usage.get(
            "cache_read_input_tokens", 0
        )
        self.cache.update_stats_from_response(api_response_usage)
