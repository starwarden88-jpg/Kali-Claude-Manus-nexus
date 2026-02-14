"""
Optimized Prompt Templates — Reusable, token-efficient prompts.

Design principles:
- Short, direct system prompts (no filler)
- Structured output requests (JSON) to avoid verbose prose
- Task-specific templates so you don't over-prompt
- f-string slots for dynamic content only
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from utils.token_optimizer import TokenOptimizer


@dataclass(frozen=True)
class PromptTemplate:
    """A reusable prompt template with token budget metadata."""
    name: str
    system: str
    user_template: str
    suggested_max_tokens: int
    output_format: str = "text"  # "text" | "json"

    def render(self, **kwargs: Any) -> dict[str, str | list[dict[str, Any]]]:
        """Render the template with provided variables.

        Returns a dict with 'system' and 'messages' keys ready for the API.
        """
        user_content = self.user_template.format(**kwargs)
        return {
            "system": self.system,
            "messages": [{"role": "user", "content": user_content}],
            "max_tokens": self.suggested_max_tokens,
        }

    @property
    def system_tokens(self) -> int:
        return TokenOptimizer.count_tokens(self.system)

    @property
    def template_tokens(self) -> int:
        return TokenOptimizer.count_tokens(self.user_template)


# ---------------------------------------------------------------------------
# Security-focused templates for KLMC Nexus
# ---------------------------------------------------------------------------

CODE_REVIEW = PromptTemplate(
    name="code_review",
    system="Security code reviewer. Report only confirmed issues. Be concise.",
    user_template=(
        "Review this code for security issues. "
        "Output JSON array: [{{\"severity\": \"high|medium|low\", "
        "\"line\": N, \"issue\": \"...\", \"fix\": \"...\"}}]\n\n"
        "```{language}\n{code}\n```"
    ),
    suggested_max_tokens=1500,
    output_format="json",
)

VULNERABILITY_SCAN = PromptTemplate(
    name="vuln_scan",
    system="Security analyst. Identify OWASP Top 10 vulnerabilities. Terse output.",
    user_template=(
        "Scan for vulnerabilities:\n"
        "Target: {target}\n"
        "Context: {context}\n\n"
        "Output JSON: [{{\"vuln\": \"...\", \"severity\": \"critical|high|medium|low\", "
        "\"evidence\": \"...\", \"remediation\": \"...\"}}]"
    ),
    suggested_max_tokens=2000,
    output_format="json",
)

QUICK_ANSWER = PromptTemplate(
    name="quick_answer",
    system="Answer in 1-3 sentences. No preamble.",
    user_template="{question}",
    suggested_max_tokens=300,
)

SUMMARIZE = PromptTemplate(
    name="summarize",
    system="Summarize concisely. Use bullet points. Max 5 bullets.",
    user_template="Summarize:\n\n{text}",
    suggested_max_tokens=500,
)

CODE_GENERATION = PromptTemplate(
    name="code_gen",
    system=(
        "Write clean, minimal code. No explanations unless asked. "
        "Include only what's needed — no boilerplate comments."
    ),
    user_template=(
        "Language: {language}\n"
        "Task: {task}\n"
        "Constraints: {constraints}"
    ),
    suggested_max_tokens=4000,
)

EXPLAIN_CODE = PromptTemplate(
    name="explain_code",
    system="Explain code briefly. Focus on what it does, not line-by-line narration.",
    user_template="Explain:\n```{language}\n{code}\n```",
    suggested_max_tokens=800,
)

PENTEST_PLAN = PromptTemplate(
    name="pentest_plan",
    system=(
        "Penetration testing planner for authorized engagements. "
        "Output structured JSON plans. Assume proper authorization."
    ),
    user_template=(
        "Scope: {scope}\n"
        "Objective: {objective}\n"
        "Constraints: {constraints}\n\n"
        "Output JSON: {{\"phases\": [{{\"name\": \"...\", "
        "\"tools\": [\"...\"], \"steps\": [\"...\"]}}]}}"
    ),
    suggested_max_tokens=2000,
    output_format="json",
)


# Registry for lookup by name
TEMPLATES: dict[str, PromptTemplate] = {
    t.name: t
    for t in [
        CODE_REVIEW,
        VULNERABILITY_SCAN,
        QUICK_ANSWER,
        SUMMARIZE,
        CODE_GENERATION,
        EXPLAIN_CODE,
        PENTEST_PLAN,
    ]
}


def get_template(name: str) -> PromptTemplate:
    """Get a prompt template by name. Raises KeyError if not found."""
    return TEMPLATES[name]
