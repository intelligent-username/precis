"""Précis API — routes and app setup."""

import asyncio
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from config import OLLAMA_BASE_URL, DEFAULT_MODEL, AVAILABLE_MODELS
from schemas import TranscriptRequest, YouTubeRequest
from ollama import stream_summary
from youtube import extract_video_id, fetch_transcript

app = FastAPI(
    title="Précis API",
    description="Content summarisation service powered by Ollama",
    version="0.4.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    return {"default": DEFAULT_MODEL, "available": AVAILABLE_MODELS}


@app.post("/summarize/transcript")
async def summarize_transcript(request: TranscriptRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text must not be empty.")
    return stream_summary(request.text, title=request.title, model=request.model)


@app.post("/summarize/youtube")
async def summarize_youtube(request: YouTubeRequest):
    video_id = extract_video_id(request.url)
    text = await asyncio.to_thread(fetch_transcript, video_id)
    return stream_summary(text, model=request.model)


@app.post("/summarize/file")
async def summarize_file(file: UploadFile = File(...), model: Optional[str] = None):
    if not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt files are supported.")
    content = await file.read()
    text = content.decode("utf-8")
    if not text.strip():
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    return stream_summary(text, title=file.filename, model=model)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
