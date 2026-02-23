"""FastAPI backend for Précis — powered by Ollama (phi4-mini:3.8b)."""

import logging
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

OLLAMA_BASE_URL = "http://127.0.0.1:11434"
OLLAMA_COMPLETIONS_URL = f"{OLLAMA_BASE_URL}/v1/completions"
MODEL_NAME = "phi4-mini:3.8b"

# Tokens to generate for the summary — keep short for speed
MAX_SUMMARY_TOKENS = 120
TEMPERATURE = 0.2

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Précis API",
    description="Content summarisation service powered by phi4-mini via Ollama",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class YouTubeRequest(BaseModel):
    url: str
    max_length: Optional[int] = 512


class TranscriptRequest(BaseModel):
    text: str
    title: Optional[str] = None
    max_length: Optional[int] = 512


class SummarizeResponse(BaseModel):
    summary: str
    success: bool
    source_type: str
    model: str = MODEL_NAME


# ---------------------------------------------------------------------------
# Ollama helper
# ---------------------------------------------------------------------------

def _build_prompt(title: Optional[str], text: str) -> str:
    header = f"Title: {title}\n" if title else ""
    return (
        "Summarise the following article in 2–4 clear, factual sentences. "
        "Do not add opinions or commentary.\n\n"
        f"{header}"
        f"Article:\n{text}\n\n"
        "Summary:"
    )


async def call_ollama(prompt: str, max_tokens: int = MAX_SUMMARY_TOKENS) -> str:
    """Send a prompt to the local Ollama completions endpoint and return the text."""
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "max_tokens": max_tokens,
        "temperature": TEMPERATURE,
        "stop": ["\n\n", "Article:", "Title:"],  # prevent runaway generation
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            resp = await client.post(OLLAMA_COMPLETIONS_URL, json=payload)
            resp.raise_for_status()
        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Cannot reach Ollama at 127.0.0.1:11434. "
                    "Make sure `ollama serve` is running."
                ),
            )
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Ollama returned an error: {exc.response.text}",
            )

    data = resp.json()
    try:
        return data["choices"][0]["text"].strip()
    except (KeyError, IndexError) as exc:
        logger.error("Unexpected Ollama response: %s", data)
        raise HTTPException(
            status_code=502,
            detail=f"Unexpected response shape from Ollama: {exc}",
        )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with basic info."""
    return """
    <!DOCTYPE html>
    <html>
        <head>
            <title>Précis API</title>
            <style>
                body { font-family: system-ui; max-width: 800px; margin: 50px auto; padding: 20px; }
                h1 { color: #333; }
                code { background: #f4f4f4; padding: 2px 6px; border-radius: 3px; }
                .model { color: #6366f1; font-weight: bold; }
            </style>
        </head>
        <body>
            <h1>Précis API</h1>
            <p>Model: <span class="model">phi4-mini:3.8b</span> via Ollama</p>
            <h2>Endpoints</h2>
            <ul>
                <li><code>POST /summarize/transcript</code> — Summarise raw text</li>
                <li><code>POST /summarize/file</code> — Summarise a .txt file</li>
                <li><code>POST /summarize/youtube</code> — Summarise a YouTube video (transcript required)</li>
                <li><code>GET /health</code> — Health check</li>
                <li><code>GET /status</code> — Service status</li>
                <li><code>GET /docs</code> — Interactive API docs</li>
            </ul>
        </body>
    </html>
    """


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "precis"}


@app.get("/status")
async def status():
    """Service status — also pings Ollama to confirm it is reachable."""
    ollama_ok = False
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            ollama_ok = r.status_code == 200
    except Exception:
        pass

    return {
        "service": "Précis API",
        "version": "0.2.0",
        "model": MODEL_NAME,
        "ollama_reachable": ollama_ok,
        "endpoints": ["/", "/health", "/status", "/summarize/transcript",
                      "/summarize/file", "/summarize/youtube"],
    }


@app.post("/summarize/transcript", response_model=SummarizeResponse)
async def summarize_transcript(request: TranscriptRequest):
    """Summarise a provided article or transcript."""
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="text must not be empty")

    prompt = _build_prompt(request.title, request.text)
    summary = await call_ollama(prompt)

    return SummarizeResponse(summary=summary, success=True, source_type="transcript")


@app.post("/summarize/file", response_model=SummarizeResponse)
async def summarize_file(file: UploadFile = File(...)):
    """Summarise content from an uploaded .txt file."""
    if not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt files are supported")

    content = await file.read()
    text = content.decode("utf-8")

    if not text.strip():
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    prompt = _build_prompt(file.filename, text)
    summary = await call_ollama(prompt)

    return SummarizeResponse(summary=summary, success=True, source_type="file")


@app.post("/summarize/youtube", response_model=SummarizeResponse)
async def summarize_youtube(request: YouTubeRequest):
    """
    Summarise a YouTube video.

    NOTE: Automatic transcript fetching is not yet implemented.
    Pass the transcript text in a separate /summarize/transcript call,
    or extend this endpoint with youtube-transcript-api.
    """
    # Placeholder — returns a clear message rather than silently lying
    raise HTTPException(
        status_code=501,
        detail=(
            "Automatic YouTube transcript fetching is not yet implemented. "
            "Extract the transcript yourself and POST it to /summarize/transcript."
        ),
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
