from typing import Optional

import httpx
from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from config import (
    OLLAMA_BASE_URL, DEFAULT_MODEL, AVAILABLE_MODELS,
    MAX_SUMMARY_TOKENS, TEMPERATURE,
)


def build_prompt(title: Optional[str], text: str) -> str:
    if title:
        instructions = (
            f'The article is titled "{title}". '
            "If the title is a question, answer it directly in one sentence using only facts from the article. "
            "If the title is not a question, write one sentence that gives a concise, high-level overview "
            "of the article, briefly enumerating all key facts."
        )
    else:
        instructions = (
            "Write one sentence that gives a concise, high-level overview of the article, "
            "briefly enumerating all key facts."
        )
    return (
        f"{instructions}\n"
        "Do not add opinions, commentary, or filler phrases like 'The article discusses'.\n"
        "Output the summary sentence only — nothing else.\n\n"
        f"Article:\n{text}\n\n"
        "Summary:"
    )


def resolve_model(model: Optional[str]) -> str:
    if not model:
        return DEFAULT_MODEL
    if model not in AVAILABLE_MODELS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown model '{model}'. Available: {AVAILABLE_MODELS}",
        )
    return model


async def ollama_stream(prompt: str, model: str):
    """Async generator: yields raw NDJSON lines from Ollama."""
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True,
        "options": {
            "num_predict": MAX_SUMMARY_TOKENS,
            "temperature": TEMPERATURE,
            "stop": ["\n\n", "Article:", "Title:"],
        },
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            async with client.stream(
                "POST", f"{OLLAMA_BASE_URL}/api/generate", json=payload,
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line:
                        yield line + "\n"
        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail="Cannot reach Ollama. Make sure `ollama serve` is running.",
            )


def stream_summary(
    text: str,
    title: Optional[str] = None,
    model: Optional[str] = None,
) -> StreamingResponse:
    """Universal funnel: text -> prompt -> Ollama stream -> NDJSON response."""
    resolved = resolve_model(model)
    prompt = build_prompt(title, text)
    return StreamingResponse(
        ollama_stream(prompt, resolved),
        media_type="application/x-ndjson",
        headers={"X-Accel-Buffering": "no"},
    )
