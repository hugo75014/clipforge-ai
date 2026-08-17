# AI providers

ClipForge ships with a single `AIProvider` protocol. Implementations live in
`backend/app/providers/ai/`. Switching provider is a single env-var change —
no code change.

```text
AIProvider
 ├── DemoProvider       (default — works offline)
 ├── OpenAIProvider
 ├── AnthropicProvider
 ├── GeminiProvider
 ├── OpenRouterProvider
 └── LocalProvider      (Ollama-compatible)
```

## Configuration

```env
# In .env
AI_PROVIDER=openai              # demo | openai | anthropic | gemini | openrouter | local
AI_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-...
```

The same pattern applies to transcription:

```text
TranscriptionProvider
 ├── DemoTranscriptionProvider
 ├── WhisperProvider
 └── WhisperXProvider
```

```env
TRANSCRIPTION_PROVIDER=whisper
WHISPER_MODEL=base
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8
WHISPER_LANGUAGE=en        # optional, auto-detected when empty
```

## Pricing estimates

We track approximate cost in the `Job` table. Numbers come from each
provider's public pricing page at the time of writing and are
**estimates only** — always check the latest price.

| Model | Input ($/Mtok) | Output ($/Mtok) |
| --- | --- | --- |
| gpt-4o-mini | 0.15 | 0.60 |
| gpt-4o | 2.50 | 10.00 |
| claude-3-5-sonnet | 3.00 | 15.00 |
| claude-3-5-haiku | 0.80 | 4.00 |
| gemini-1.5-flash | (free tier) | — |

## Adding a new provider

1. Create `backend/app/providers/ai/myprovider.py` implementing the
   `AIProvider` protocol.
2. Register it in `backend/app/providers/ai/__init__.py`.
3. Add a section to `.env.example`.
4. Document it in this file.

That's it. The rest of the app picks it up automatically.

## Demo mode

`DEMO_MODE=true` (the default) means **the entire pipeline runs without any
API key**. The demo provider returns a deterministic but realistic JSON
shaped to match a real LLM, and the demo transcription provider generates
plausible speech segments based on the audio's duration.

This is what lets the project work end-to-end out of the box. When you wire
a real provider, the rest of the app does **not** change.

## Cost control tips

- Use `AI_MODEL=gpt-4o-mini` for the cheapest path with high quality.
- Set `top_k=10` in the detection step (configurable per request).
- Cap `max_tokens` per request (e.g. 1024 — we only need JSON).
- Use a local model (Ollama) for development.
