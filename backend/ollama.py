from typing import Optional
import json
import os

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
        "Do not add opinions, commentary, or filler phrases like 'The article discusses' or 'This document provides'.\n"
        "or any similar phrasing, whether the similarity be in meaning or otherwise. Get straight to the point."
        "Output the summary sentence only. The sentence should be no longer than 200 characetrs long. Nothing else should be included.\n\n"
        f"Article:\n{text}\n\n"
        "Summary:"
    )


def resolve_model(model: Optional[str]) -> str:
    requested = model or ""

    # Prefer what Ollama actually has installed.
    try:
        with httpx.Client(timeout=5.0) as client:
            r = client.get(f"{OLLAMA_BASE_URL}/api/tags")
            r.raise_for_status()
            payload = r.json() if r.content else {}
            installed = [m.get("name") for m in payload.get("models", []) if m.get("name")]
    except Exception:
        installed = []

    if installed:
        if not requested:
            return DEFAULT_MODEL if DEFAULT_MODEL in installed else installed[0]
        if requested not in installed:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Model '{requested}' is not installed in Ollama. "
                    f"Installed: {installed}. Run `ollama pull {requested}`."
                ),
            )
        return requested

    # Fallback: use configured allowlist when Ollama isn't reachable.
    if not requested:
        return DEFAULT_MODEL
    if requested not in AVAILABLE_MODELS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown model '{requested}'. Available: {AVAILABLE_MODELS}",
        )
    return requested


def ensure_ollama_reachable() -> None:
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(f"{OLLAMA_BASE_URL}/api/tags")
            response.raise_for_status()
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Cannot reach Ollama. Make sure `ollama serve` is running.",
        )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Ollama responded with an error: {exc}",
        )


async def ollama_stream(prompt: str, model: str):
    """Async generator: yields NDJSON lines from Ollama, filtering out thinking-only chunks."""
    keep_alive = os.getenv("OLLAMA_KEEP_ALIVE", "30m")
    # Set num_predict high so thinking tokens don't limit output.
    num_predict = MAX_SUMMARY_TOKENS * 3
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True,
        "keep_alive": keep_alive,
        "options": {
            "num_predict": num_predict,
            "temperature": TEMPERATURE,
            "stop": ["Article:", "Title:"],
        },
    }
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            async with client.stream(
                "POST", f"{OLLAMA_BASE_URL}/api/generate", json=payload,
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                        # Skips thinking-only chunks.
                        if chunk.get("response"):
                            yield line + "\n"
                    except json.JSONDecodeError:
                        yield line + "\n"
        except httpx.ConnectError:
            error_line = json.dumps({
                "error": "Cannot reach Ollama. Make sure `ollama serve` is running.",
            })
            yield error_line + "\n"
        except httpx.TimeoutException:
            error_line = json.dumps({
                "error": "Ollama timed out. The model may still be loading — try again in a moment.",
            })
            yield error_line + "\n"
        except httpx.HTTPError as exc:
            error_line = json.dumps({
                "error": f"Ollama error: {exc}",
            })
            yield error_line + "\n"


def stream_summary(
    text: str,
    title: Optional[str] = None,
    model: Optional[str] = None,
) -> StreamingResponse:
    """Universal funnel: text -> prompt -> Ollama stream -> NDJSON response."""
    ensure_ollama_reachable()
    resolved = resolve_model(model)
    prompt = build_prompt(title, text)
    return StreamingResponse(
        ollama_stream(prompt, resolved),
        media_type="application/x-ndjson",
        headers={"X-Accel-Buffering": "no"},
    )
