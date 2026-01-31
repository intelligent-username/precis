"""FastAPI backend for Précis."""

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional

app = FastAPI(
    title="Précis API",
    description="Content summarization API",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



class YouTubeRequest(BaseModel):
    url: str
    max_length: Optional[int] = 512

class TranscriptRequest(BaseModel):
    text: str
    max_length: Optional[int] = 512

class SummarizeResponse(BaseModel):
    summary: str
    success: bool
    source_type: str



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
            </style>
        </head>
        <body>
            <h1>Précis API</h1>
            <p>Content summarization service</p>
            <h2>Endpoints</h2>
            <ul>
                <li><code>POST /summarize</code> - Summarize content from URL</li>
                <li><code>GET /health</code> - Health check</li>
                <li><code>GET /status</code> - Service status</li>
                <li><code>GET /docs</code> - API documentation</li>
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
    """Service status endpoint."""
    return {
        "service": "Précis API",
        "version": "0.1.0",
        "model": "Qwen/Qwen2.5-7B-Instruct",
        "model_loaded": False,  # TODO: Track actual model state
        "endpoints": ["/", "/health", "/status", "/summarize"]
    }


@app.post("/summarize/youtube", response_model=SummarizeResponse)
async def summarize_youtube(request: YouTubeRequest):
    """Summarize a YouTube video from its URL."""
    # TODO: Implement YT transcript extraction and summarization
    return SummarizeResponse(
        summary=f"Summary for YouTube video at {request.url}. (Placeholder)",
        success=True,
        source_type="youtube"
    )

@app.post("/summarize/transcript", response_model=SummarizeResponse)
async def summarize_transcript(request: TranscriptRequest):
    """Summarize a provided transcript or article text."""
    # TODO: Implement summarization
    return SummarizeResponse(
        summary=f"Summary for provided text ({len(request.text)} chars). (Placeholder)",
        success=True,
        source_type="transcript"
    )

@app.post("/summarize/file", response_model=SummarizeResponse)
async def summarize_file(file: UploadFile = File(...)):
    """Summarize content from a .txt file."""
    if not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt files are supported")
    
    content = await file.read()
    text = content.decode("utf-8")
    
    # TODO: Implement summarization
    return SummarizeResponse(
        summary=f"Summary for file {file.filename} ({len(text)} chars). (Placeholder)",
        success=True,
        source_type="file"
    )



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
