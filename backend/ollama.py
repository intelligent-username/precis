from typing import Optional
import json
import os

import httpx
from fastapi import HTTPException
from fastapi.responses import StreamingResponse

try:
    from config import (  # type: ignore
        OLLAMA_BASE_URL, DEFAULT_MODEL, AVAILABLE_MODELS,
        MAX_SUMMARY_TOKENS, TEMPERATURE,
    )
except ImportError:
    from backend.config import (  # type: ignore
        OLLAMA_BASE_URL, DEFAULT_MODEL, AVAILABLE_MODELS,
        MAX_SUMMARY_TOKENS, TEMPERATURE,
    )


def build_prompt(title: Optional[str], text: str) -> str:
    """The summarization prompt sent to Ollama.

        I need it to handle all cases and ensure clean summaries that are *as short as possible*.

        Remember:
          - Needs three features: brevity, brevity, and brevity
          - Ensure output begins with the first word of the summary
          - Omit fluff that's not related to the title (OR overriding theme)
          - No meta-commentary
    """
    # Optional title block 
    title_block = f"### Title: {title}\n" if title else ""

    instruction = \
        "Before proceeding, remember that you are an expert summarizer and must follow these instructions: \n" \
        "The objective is to take the given text and produce a compendious summary. \n" \
        "The priorities of the summary are as follows: \n" \
        "  1) Make direct, declarative sentences while speaking with perfect, proper grammar. "\
        "  2) If a title is provided, let it be an inspiration for the summary. If the title contains a question, answer it directly in the summary.\n" \
        "  3) Ignore ads, channel plugs, affiliate links, channel/author descriptions, sponsors, supporter shoutouts, and all other info not pertinent to the specific topic at hand.\n" \
        "  4) With every sentence, get straight to the point. Exclude opinions ('some think...'), mistakes ('um', 'like', etc.), uncertainty ('may suggests that...', etc.), transitions ('The video provides...'), commentary, or context (like 'the text states...', 'the author thinks', or anything like \that) are allowed.\n" \
        "  5) Only state the most obvious, objective, and conclusive points from the text.\n" \
        "  6) Keep sentences to <= 100 characters and paragraphs to <= 3 sentences. Make use of point form and lists in order to break up large chunks of text.\n" \
        "  7) Most importantly, be 'in and out' with the facts. State only the most crucial high-level points and move on. This means, never introduce what is about to be said, i.e. don't say things like, `in this historical analysis, `, or `before proceeding`, or anything like that. Ensure sentences are short and ONLY discuss the topic at hand.\n" \
        "  8) Never state who you are, what you do, what you just did, or what you're about to do. Do not mention this or any other prompt. Strictly stick to the content of the material given. \n" \
        "No matter what is asked. Never break the fourth wall. Never refer to yourself in any way. Never speak in first person. Never refer to anything outside the given text or title in any way.\n" \
        "The goal of the summary is to produce a compendious summary so that the user can save time." \
        "Now, I need you to summarize the following text.\n" \

    return (
        f"{instruction}\n"
        f"{title_block}"
        "### Article:\n"
        f"{text}\n\n"
        "### Summary:"
    )


async def resolve_model(model: Optional[str]) -> str:
    requested = model or ""

    # Prefer what Ollama actually has installed, queried live.
    installed = []
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            r.raise_for_status()
            payload = r.json() if r.content else {}
            installed = [m.get("name") for m in payload.get("models", []) if m.get("name")]
    except Exception:
        pass

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


async def ensure_ollama_reachable() -> None:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
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
    """Async generator: yields NDJSON lines from Ollama.

    Parses standard output response stream to isolate <think>...</think> blocks
    on the backend, yielding separate 'thinking' and 'response' events. This
    ensures compatibility across all Ollama versions and avoids 400 Bad Request errors.
    """
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
    if "r1" in model.lower() or "deepseek" in model.lower():
        payload["think"] = True

    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            async with client.stream(
                "POST", f"{OLLAMA_BASE_URL}/api/generate", json=payload,
            ) as resp:
                resp.raise_for_status()

                in_thinking = False
                buffer = ""
                # To track if we started native thinking
                native_thinking_active = False

                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                        native_thinking = chunk.get("thinking") or ""
                        native_response = chunk.get("response") or ""

                        if native_thinking:
                            if not native_thinking_active:
                                yield json.dumps({"response": "> *Model Reasoning:*\n> \n> "}) + "\n"
                                native_thinking_active = True
                            
                            formatted = native_thinking.replace("\n", "\n> ")
                            yield json.dumps({"response": formatted}) + "\n"
                            continue

                        if not native_response:
                            continue

                        # If native thinking just ended
                        if native_thinking_active:
                            yield json.dumps({"response": "\n\n---\n\n"}) + "\n"
                            native_thinking_active = False

                        buffer += native_response

                        # Extract <think>...</think> tags dynamically
                        while True:
                            if not in_thinking:
                                idx = buffer.find("<think>")
                                if idx != -1:
                                    before = buffer[:idx]
                                    if before:
                                        yield json.dumps({"response": before}) + "\n"
                                    in_thinking = True
                                    yield json.dumps({"response": "\n> *Model Reasoning:*\n> \n> "}) + "\n"
                                    buffer = buffer[idx + 7:]
                                else:
                                    # Check for partial match of "<think>" at the end of the buffer
                                    partial_len = 0
                                    for i in range(6, 0, -1):
                                        if buffer.endswith("<think>"[:i]):
                                            partial_len = i
                                            break
                                    if partial_len > 0:
                                        to_yield = buffer[:-partial_len]
                                        if to_yield:
                                            yield json.dumps({"response": to_yield}) + "\n"
                                        buffer = buffer[-partial_len:]
                                        break
                                    else:
                                        yield json.dumps({"response": buffer}) + "\n"
                                        buffer = ""
                                        break
                            else:
                                idx = buffer.find("</think>")
                                if idx != -1:
                                    thinking_content = buffer[:idx]
                                    if thinking_content:
                                        formatted = thinking_content.replace("\n", "\n> ")
                                        yield json.dumps({"response": formatted}) + "\n"
                                    in_thinking = False
                                    yield json.dumps({"response": "\n\n---\n\n"}) + "\n"
                                    buffer = buffer[idx + 8:]
                                else:
                                    # Check for partial match of "</think>" at the end of the buffer
                                    partial_len = 0
                                    for i in range(7, 0, -1):
                                        if buffer.endswith("</think>"[:i]):
                                            partial_len = i
                                            break
                                    if partial_len > 0:
                                        to_yield = buffer[:-partial_len]
                                        if to_yield:
                                            formatted = to_yield.replace("\n", "\n> ")
                                            yield json.dumps({"response": formatted}) + "\n"
                                        buffer = buffer[-partial_len:]
                                        break
                                    else:
                                        formatted = buffer.replace("\n", "\n> ")
                                        yield json.dumps({"response": formatted}) + "\n"
                                        buffer = ""
                                        break
                    except json.JSONDecodeError:
                        yield line + "\n"

                # Yield remainder
                if buffer:
                    if in_thinking:
                        formatted = buffer.replace("\n", "\n> ")
                        yield json.dumps({"response": formatted}) + "\n"
                    else:
                        yield json.dumps({"response": buffer}) + "\n"

        except httpx.ConnectError:
            error_line = json.dumps({
                "error": "Cannot reach Ollama. Make sure `ollama serve` is running.",
            })
            yield error_line + "\n"
        except httpx.TimeoutException:
            error_line = json.dumps({
                "error": "Ollama timed out. The model may still be loading. Try again in a moment.",
            })
            yield error_line + "\n"
        except httpx.HTTPError as exc:
            error_line = json.dumps({
                "error": f"Ollama error: {exc}",
            })
            yield error_line + "\n"



async def stream_summary(
    text: str,
    title: Optional[str] = None,
    model: Optional[str] = None,
) -> StreamingResponse:
    """Universal funnel: text -> prompt -> Ollama stream -> NDJSON response."""
    await ensure_ollama_reachable()
    resolved = await resolve_model(model)
    prompt = build_prompt(title, text)
    return StreamingResponse(
        ollama_stream(prompt, resolved),
        media_type="application/x-ndjson",
        headers={"X-Accel-Buffering": "no"},
    )
