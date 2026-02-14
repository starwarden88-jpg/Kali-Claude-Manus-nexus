"""
Token Optimizer — Reduce input tokens without losing meaning.

Three main strategies:
1. Prompt compression: Strip filler words, collapse whitespace, abbreviate
2. Context windowing: Keep only the most relevant parts of long inputs
3. Token counting: Estimate token usage before sending (avoids surprises)
"""

from __future__ import annotations

import re
import math
from dataclasses import dataclass


# Filler phrases that add tokens but not meaning
_FILLER_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bplease\b", re.I), ""),
    (re.compile(r"\bkindly\b", re.I), ""),
    (re.compile(r"\bcould you\b", re.I), ""),
    (re.compile(r"\bcan you\b", re.I), ""),
    (re.compile(r"\bI would like you to\b", re.I), ""),
    (re.compile(r"\bI want you to\b", re.I), ""),
    (re.compile(r"\bI need you to\b", re.I), ""),
    (re.compile(r"\bbasically\b", re.I), ""),
    (re.compile(r"\bessentially\b", re.I), ""),
    (re.compile(r"\bin order to\b", re.I), "to"),
    (re.compile(r"\bdue to the fact that\b", re.I), "because"),
    (re.compile(r"\bat this point in time\b", re.I), "now"),
    (re.compile(r"\bfor the purpose of\b", re.I), "to"),
    (re.compile(r"\bin the event that\b", re.I), "if"),
    (re.compile(r"\bwith regard to\b", re.I), "about"),
    (re.compile(r"\ba large number of\b", re.I), "many"),
    (re.compile(r"\bin spite of the fact that\b", re.I), "although"),
]


@dataclass
class CompressionResult:
    """Result of prompt compression."""
    original: str
    compressed: str
    original_tokens: int
    compressed_tokens: int

    @property
    def savings_pct(self) -> float:
        if self.original_tokens == 0:
            return 0.0
        return (1 - self.compressed_tokens / self.original_tokens) * 100

    def __str__(self) -> str:
        return (
            f"Tokens: {self.original_tokens} -> {self.compressed_tokens} "
            f"({self.savings_pct:.1f}% saved)"
        )


class TokenOptimizer:
    """Utilities for reducing token usage in prompts and messages."""

    # Rough average: 1 token ≈ 4 chars for English text (Claude tokenizer)
    CHARS_PER_TOKEN = 4.0

    @staticmethod
    def count_tokens(text: str) -> int:
        """Estimate token count without requiring the tokenizer library.

        Uses the ~4 chars/token heuristic for Claude models.
        For exact counts, use anthropic.count_tokens() from the SDK.
        """
        if not text:
            return 0
        return math.ceil(len(text) / TokenOptimizer.CHARS_PER_TOKEN)

    @staticmethod
    def compress_prompt(text: str, aggressive: bool = False) -> CompressionResult:
        """Compress a prompt by removing filler and tightening language.

        Args:
            text: The prompt to compress.
            aggressive: If True, also collapse multiple spaces and strip
                        markdown formatting.
        """
        original_tokens = TokenOptimizer.count_tokens(text)
        result = text

        # Remove filler words/phrases
        for pattern, replacement in _FILLER_PATTERNS:
            result = pattern.sub(replacement, result)

        # Collapse multiple spaces into one
        result = re.sub(r"[ \t]+", " ", result)

        # Collapse multiple blank lines into one
        result = re.sub(r"\n{3,}", "\n\n", result)

        if aggressive:
            # Strip markdown bold/italic (keeps the text, drops the **)
            result = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", result)
            # Collapse indentation
            result = re.sub(r"^[ \t]+", "", result, flags=re.MULTILINE)

        result = result.strip()
        compressed_tokens = TokenOptimizer.count_tokens(result)

        return CompressionResult(
            original=text,
            compressed=result,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
        )

    @staticmethod
    def truncate_to_budget(text: str, max_tokens: int, keep: str = "end") -> str:
        """Truncate text to fit within a token budget.

        Args:
            text: Input text.
            max_tokens: Maximum tokens allowed.
            keep: 'start' keeps the beginning, 'end' keeps the end.
        """
        estimated = TokenOptimizer.count_tokens(text)
        if estimated <= max_tokens:
            return text

        max_chars = int(max_tokens * TokenOptimizer.CHARS_PER_TOKEN)
        if keep == "start":
            return text[:max_chars] + "\n[...truncated]"
        return "[truncated...]\n" + text[-max_chars:]

    @staticmethod
    def chunk_for_context(
        text: str,
        chunk_tokens: int = 2000,
        overlap_tokens: int = 200,
    ) -> list[str]:
        """Split long text into overlapping chunks for multi-turn processing.

        Useful for processing large files without blowing up a single
        request's input token count.
        """
        chunk_chars = int(chunk_tokens * TokenOptimizer.CHARS_PER_TOKEN)
        overlap_chars = int(overlap_tokens * TokenOptimizer.CHARS_PER_TOKEN)
        step = chunk_chars - overlap_chars

        chunks: list[str] = []
        for i in range(0, len(text), step):
            chunk = text[i : i + chunk_chars]
            if chunk:
                chunks.append(chunk)
            if i + chunk_chars >= len(text):
                break

        return chunks

    @staticmethod
    def format_efficient_message(role: str, content: str) -> dict[str, str]:
        """Create a message dict with compressed content."""
        compressed = TokenOptimizer.compress_prompt(content)
        return {"role": role, "content": compressed.compressed}

    @staticmethod
    def report(text: str) -> str:
        """Print a token usage report for a piece of text."""
        result = TokenOptimizer.compress_prompt(text)
        return (
            f"--- Token Report ---\n"
            f"Original:   ~{result.original_tokens} tokens\n"
            f"Compressed: ~{result.compressed_tokens} tokens\n"
            f"Savings:    ~{result.original_tokens - result.compressed_tokens} tokens "
            f"({result.savings_pct:.1f}%)\n"
        )
