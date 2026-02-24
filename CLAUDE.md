# CLAUDE.md - Project Configuration for Claude Code

## Project Overview

KLMC Nexus (Kali Linux + Manus AI + Claude AI) — a unified platform integrating Kali Linux security tooling with Claude AI capabilities for authorized security testing, defensive security, and educational contexts.

## Claude Model

This project targets **Claude Opus 4** (model ID: `claude-opus-4-6`), the most recent frontier Claude model as of 2025.

### Available Claude Models (current as of 2025)

| Model | Model ID | Use Case |
|-------|----------|----------|
| Claude Opus 4 | `claude-opus-4-6` | Most capable, complex reasoning and analysis |
| Claude Sonnet 4 | `claude-sonnet-4-20250514` | Balanced performance and speed |
| Claude Haiku 3.5 | `claude-haiku-3-5-20241022` | Fast, lightweight tasks |

## Development Guidelines

- All security tooling must operate within authorized testing boundaries
- Follow responsible disclosure practices
- Claude integration should validate authorization context before executing security operations
- Use the Anthropic Python SDK (`anthropic`) or TypeScript SDK (`@anthropic-ai/sdk`) for API calls

## API Integration

```python
import anthropic

client = anthropic.Anthropic()

message = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Your prompt here"}
    ]
)
```

## Key Features

- **Extended Thinking**: Use `thinking` parameter for complex multi-step security analysis
- **Tool Use**: Define custom tools for interacting with Kali Linux utilities
- **Streaming**: Real-time output for long-running analysis tasks

## Repository Structure

```
/                   # Project root
├── CLAUDE.md       # Claude Code project configuration
├── README.md       # Project overview
```

## Security Policy

This project is for **authorized security testing, defensive security, CTF challenges, and educational purposes only**. All Claude-powered operations must verify authorization before execution.
