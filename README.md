# Kali-Claude-Manus-nexus

A seamless unification of Kali Linux, Manus AI, and Claude AI — the **KLMC Nexus**.

## About

KLMC Nexus integrates Kali Linux security tooling with AI capabilities powered by **Claude Opus 4** (`claude-opus-4-6`), Anthropic's most capable model. The platform enables authorized security testing, defensive security operations, CTF challenges, and security education through an AI-augmented workflow.

## Claude AI Integration

This project uses the latest Claude models via the [Anthropic API](https://docs.anthropic.com/en/api):

- **Claude Opus 4** — Complex reasoning, multi-step security analysis, and advanced tool use
- **Claude Sonnet 4** — Balanced performance for routine analysis tasks
- **Claude Haiku 3.5** — Fast, lightweight operations

### Key Capabilities

- **Tool Use**: Claude can invoke Kali Linux security utilities through defined tool interfaces
- **Extended Thinking**: Multi-step reasoning for complex security analysis workflows
- **Streaming**: Real-time output for long-running operations
- **Vision**: Analyze screenshots, network diagrams, and visual security artifacts

## Getting Started

1. Obtain an API key from [Anthropic Console](https://console.anthropic.com/)
2. Set the environment variable: `export ANTHROPIC_API_KEY="your-key"`
3. Install the SDK: `pip install anthropic` or `npm install @anthropic-ai/sdk`

## Security Policy

This project is intended **exclusively** for:
- Authorized penetration testing engagements
- Defensive security and blue team operations
- CTF competitions and security challenges
- Security research and education

Unauthorized or malicious use is strictly prohibited.

## License

See [LICENSE](LICENSE) for details.
