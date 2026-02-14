# KLMC Nexus - Project Context

## What This Is
KLMC Nexus integrates Kali Linux, Manus AI, and Claude AI into a unified security-focused AI framework.

## Architecture
```
klmc-nexus/
├── config/           # API configs, prompt templates, token budgets
│   ├── api_config.py
│   └── prompts/      # Reusable prompt templates (keeps tokens low)
├── utils/            # Token optimizer, prompt cache, helpers
│   ├── token_optimizer.py
│   └── prompt_cache.py
├── CLAUDE.md         # This file (auto-loaded by Claude Code)
└── README.md
```

## Token Efficiency Rules
- Use prompt caching (`cache_control`) for static system prompts
- Set explicit `max_tokens` on every API call — never leave it open-ended
- Prefer structured output (JSON) over free-form text to reduce waste
- Reuse prompt templates from `config/prompts/` instead of inline strings
- Use the `TokenOptimizer` class to compress prompts before sending

## Key Commands
```bash
# Count tokens in a prompt
python -c "from utils.token_optimizer import TokenOptimizer; print(TokenOptimizer.count_tokens('your text'))"

# Run with optimized config
python -m config.api_config
```

## Conventions
- Python 3.10+, type hints everywhere
- anthropic SDK for Claude API calls
- All prompts stored as templates in `config/prompts/`
- Token budgets enforced per-task in `config/api_config.py`
