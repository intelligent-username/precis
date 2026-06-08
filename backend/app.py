from typing import Optional

import os

import httpx
from fastapi import FastAPI, HTTPException, UploadFile, File, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import (
    OLLAMA_BASE_URL,
    DEFAULT_MODEL,
    AVAILABLE_MODELS,
    ALLOWED_ORIGINS,
    API_KEY,
    MAX_UPLOAD_BYTES,
)
from schemas import TranscriptRequest, YouTubeRequest
from ollama import stream_summary
from helpers.transcript import transcript as fetch_yt_transcript

app = FastAPI(
    title="Précis API",
    description="Content summarisation service powered by Ollama",
    version="0.4.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key"],
)

# Only mount frontend in production when dist/ exists
if os.path.isdir("frontend/dist"):
    app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="static")

def verify_api_key(x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")):
    if not API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Server misconfigured: PRECIS_API_KEY must be set.",
        )
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key.")


@app.get("/favicon.ico")
async def favicon():
    return {}

@app.get("/")
async def root():
    return {
        "service": "Précis API",
        "docs": "/docs",
        "health": "/health",
        "status": "/status",
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "precis"}


@app.get("/status")
async def status():
    ollama_ok = False
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            ollama_ok = r.status_code == 200
    except Exception:
        pass

    return {
        "service": "Précis API",
        "version": "0.4.0",
        "default_model": DEFAULT_MODEL,
        "available_models": AVAILABLE_MODELS,
        "ollama_reachable": ollama_ok,
    }


@app.get("/models")
async def list_models():
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            r.raise_for_status()
            payload = r.json() if r.content else {}
            installed = [m.get("name") for m in payload.get("models", []) if m.get("name")]
            if installed:
                default = DEFAULT_MODEL if DEFAULT_MODEL in installed else installed[0]
                return {"default": default, "available": installed}
    except Exception:
        pass

    return {"default": DEFAULT_MODEL, "available": AVAILABLE_MODELS}


@app.post("/warmup")
async def warmup_model(model: Optional[str] = None):
    """Load a model into Ollama VRAM.

    Per the Ollama API docs: sending a generate request with an empty
    prompt (no 'prompt' key at all) causes Ollama to load the model into
    memory and return once it is ready.  stream=False means this endpoint
    only returns *after* the model is fully loaded — the frontend can await
    it to know exactly when the model is warm.
    """
    keep_alive = os.getenv("OLLAMA_KEEP_ALIVE", "30m")
    target = model or DEFAULT_MODEL
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={"model": target, "keep_alive": keep_alive, "stream": False},
            )
    except Exception:
        pass  # Non-fatal
    return {"model": target, "status": "warmed"}


@app.get("/warmup/status")
async def warmup_status(model: Optional[str] = None):
    """Check whether a model is currently loaded in Ollama's memory.

    Hits GET /api/ps (the equivalent of `ollama ps`) and returns
    {"loaded": true/false, "model": name}.
    """
    target = model or DEFAULT_MODEL
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{OLLAMA_BASE_URL}/api/ps")
            r.raise_for_status()
            payload = r.json() if r.content else {}
            running = [m.get("name", "") for m in payload.get("models", [])]
            # Match on exact name or prefix (e.g. "phi4-mini" matches "phi4-mini:latest")
            loaded = any(
                name == target or name.startswith(target + ":")
                for name in running
            )
            return {"model": target, "loaded": loaded}
    except Exception:
        return {"model": target, "loaded": False}


@app.post("/summarize/transcript")
async def summarize_transcript(
    request: TranscriptRequest,
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
):
    verify_api_key(x_api_key)
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text must not be empty.")
    return stream_summary(request.text, title=request.title, model=request.model)


@app.post("/summarize/youtube")
async def summarize_youtube(
    request: YouTubeRequest,
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
):
    verify_api_key(x_api_key)
    title, text = await fetch_yt_transcript(request.url)
    return stream_summary(text, title=title, model=request.model)


@app.post("/summarize/file")
async def summarize_file(
    req: Request,
    file: UploadFile = File(...),
    model: Optional[str] = None,
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
):
    verify_api_key(x_api_key)
    content_length = req.headers.get("content-length")
    if content_length and int(content_length) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Uploaded file is too large.")

    if not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt files are supported.")

    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Uploaded file is too large.")

    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be valid UTF-8 text.")

    if not text.strip():
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    return stream_summary(text, title=file.filename, model=model)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
