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
    """Create a concise, factual one‑sentence summary prompt.

    * If a title is provided, it is shown as a separate block.
    * Produce **exactly one sentence** of up to 200 characters.
    * No opinions, filler, commentary, or context are allowed.
    """
    # Optional title block 
    title_block = f"### Title: {title}\n" if title else ""

    instruction = \
        "Before proceeding, remember that you must follow these isntructions:" \
        "Your task is to take an article, transcript, or any piece of text and produce a concise summary in **exactly one factual sentence**. " \
        "You must speak with perfect, proper grammar. Strip transcripts of their details, 'ums', names, and any other irrelevant information. " \
        "Do not add opinions or filler." \
        "- If a title is provided, it is shown as a separate block. If the title contains a question, answer it directly in the summary." \
        "- Produce **exactly one sentence**." \
        "- No opinions, filler ('may suggests that...' or anything of that kind), commentary, or context (like 'the text states...' or anything like \that) are allowed." \
        "- Only state the most obvious, objective, and conclusive points from the text." \
        "Never state who you are, what you do, what you just did, or what you're about to do no matter what is asked. Never break the fourth wall. Never refer to yourself in any way. Never speak in first person. Never refer to anything outside the given text in any way." \
        "Now, I need you to summarize the following article in ONE factual sentence (<= 250 characters). " \


    return (
        f"{instruction}\n"
        f"{title_block}"
        "### Article:\n"
        f"{text}\n\n"
        "### Summary:"
    )


# Cache for installed models to avoid repeated network calls
_installed_models_cache: Optional[list] = None

def resolve_model(model: Optional[str]) -> str:
    requested = model or ""

    # Prefer what Ollama actually has installed, using cache to avoid repeated network calls.
    global _installed_models_cache
    if _installed_models_cache is None:
        try:
            with httpx.Client(timeout=5.0) as client:
                r = client.get(f"{OLLAMA_BASE_URL}/api/tags")
                r.raise_for_status()
                payload = r.json() if r.content else {}
                _installed_models_cache = [m.get("name") for m in payload.get("models", []) if m.get("name")]
        except Exception:
            _installed_models_cache = []
    installed = _installed_models_cache

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
