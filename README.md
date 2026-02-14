# Kali-Claude-Manus-nexus

Seamless unification of Kali Linux, Manus AI, and Claude AI — the KLMC Nexus.

## Token Efficiency

This project is built around minimizing token consumption while maintaining high-quality output from Claude. Here's how:

### 1. Prompt Caching (`utils/prompt_cache.py`)
Static system prompts and tool definitions are marked with `cache_control` so Anthropic's API caches them across requests. Cached tokens are billed at 10% of the normal rate.

```python
from utils.prompt_cache import PromptCache

cache = PromptCache()
cache.register_system_prompt("You are a security analyst...")
request = cache.build_cached_request(messages=[...])
```

### 2. Prompt Compression (`utils/token_optimizer.py`)
Strips filler words, collapses whitespace, and truncates to token budgets — all before the request is sent.

```python
from utils.token_optimizer import TokenOptimizer

result = TokenOptimizer.compress_prompt("Could you please analyze this code for me?")
# -> "analyze this code for me?"  (saves ~30% tokens)
```

### 3. Task-Specific Token Budgets (`config/api_config.py`)
Every API call gets a budget. A quick answer caps at 300 output tokens. A full analysis gets 4,000. No runaway completions.

### 4. Reusable Prompt Templates (`config/prompts/templates.py`)
Pre-built templates for code review, vulnerability scanning, code generation, and more. Each template has a tuned system prompt and max_tokens budget.

```python
from config.prompts.templates import get_template

template = get_template("code_review")
rendered = template.render(code="def foo(): eval(input())", language="python")
```

### 5. Conversation Compaction (`config/api_config.py`)
Long conversations are automatically trimmed — older messages get summarized into a brief context block so you don't pay for stale history.

### 6. CLAUDE.md Project Memory
The `CLAUDE.md` file is automatically loaded by Claude Code, giving it full project context without needing to explore the codebase each session.

## Quick Start

```python
from klmc_client import KLMCClient

client = KLMCClient()

# Quick question (300 token budget)
client.ask("What is CVSS?")

# Security code review (1500 token budget, JSON output)
client.review_code("def login(u,p): return db.query(f'SELECT * FROM users WHERE name={u}')", language="python")

# Check usage
print(client.usage_report())
```

## Project Structure

```
├── CLAUDE.md                    # Project memory for Claude Code
├── klmc_client.py               # High-level token-efficient client
├── config/
│   ├── api_config.py            # API settings + token budgets
│   └── prompts/
│       └── templates.py         # Reusable prompt templates
├── utils/
│   ├── token_optimizer.py       # Compression + token counting
│   └── prompt_cache.py          # Anthropic prompt caching manager
└── README.md
```
