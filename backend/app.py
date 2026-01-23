"""FastAPI backend for Précis."""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional

app = FastAPI(
    title="Précis API",
    description="Content summarization API",
    version="0.1.0"
)


class SummarizeRequest(BaseModel):
    """Request model for summarization."""
    url: str
    max_length: Optional[int] = 512


class SummarizeResponse(BaseModel):
    """Response model for summarization."""
    url: str
    summary: str
    success: bool


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


@app.post("/summarize", response_model=SummarizeResponse)
async def summarize(request: SummarizeRequest):
    """
    Summarize content from a URL.
    
    Currently returns dummy data. Will be implemented with actual model.
    """
    # TODO: Implement actual summarization
    # 1. Fetch content from URL
    # 2. Parse text (YouTube transcript or article)
    # 3. Run through model
    # 4. Return summary
    
    dummy_summary = (
        f"This is a placeholder summary for content at {request.url}. "
        "The actual summarization model will be integrated in the next phase. "
        "This summary respects the max_length parameter of {request.max_length} tokens."
    )
    
    return SummarizeResponse(
        url=request.url,
        summary=dummy_summary,
        success=True
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
