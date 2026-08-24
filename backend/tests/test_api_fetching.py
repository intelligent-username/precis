import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

# Mock env before importing app
import os
import sys
from pathlib import Path
# Ensure `backend` is on path when running `pytest` from repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

os.environ.setdefault("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
os.environ.setdefault("DEFAULT_MODEL", "phi4-mini:latest")
os.environ.setdefault("PRECIS_API_KEY", "test-key")
os.environ.setdefault("AVAILABLE_MODELS", "phi4-mini:latest,qwen:4b")

from app import app

client = TestClient(app)
API_KEY = "test-key"
HEADERS = {"X-API-Key": API_KEY}


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "healthy", "service": "precis"}


@patch("app.httpx.AsyncClient")
def test_status_ollama_reachable(mock_client):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_resp)
    r = client.get("/status")
    assert r.status_code == 200
    assert "ollama_reachable" in r.json()


@patch("app.httpx.AsyncClient")
def test_models_returns_installed_when_present(mock_client):
    # /api/tags returns 2 models, /api/ps returns 1 running
    tags_resp = MagicMock()
    tags_resp.status_code = 200
    tags_resp.content = b'{"models":[{"name":"phi4-mini:latest"},{"name":"qwen:4b"}]}'
    tags_resp.json.return_value = {"models": [{"name": "phi4-mini:latest"}, {"name": "qwen:4b"}]}
    tags_resp.raise_for_status = MagicMock()

    ps_resp = MagicMock()
    ps_resp.status_code = 200
    ps_resp.content = b'{"models":[{"name":"phi4-mini:latest"}]}'
    ps_resp.json.return_value = {"models": [{"name": "phi4-mini:latest"}]}

    mock_instance = MagicMock()
    mock_instance.get = AsyncMock(side_effect=[tags_resp, ps_resp])
    mock_client.return_value.__aenter__.return_value = mock_instance

    r = client.get("/models")
    assert r.status_code == 200
    data = r.json()
    assert set(data["available"]) == {"phi4-mini:latest", "qwen:4b"}
    assert data["running"] == ["phi4-mini:latest"]
    assert data["default"] in data["available"]


@patch("app.httpx.AsyncClient")
def test_models_returns_empty_when_ollama_has_no_models(mock_client):
    # Ollama reachable but 0 models — should NOT fallback to AVAILABLE_MODELS
    tags_resp = MagicMock()
    tags_resp.status_code = 200
    tags_resp.content = b'{"models":[]}'
    tags_resp.json.return_value = {"models": []}
    tags_resp.raise_for_status = MagicMock()

    ps_resp = MagicMock()
    ps_resp.status_code = 200
    ps_resp.content = b'{"models":[]}'
    ps_resp.json.return_value = {"models": []}

    mock_instance = MagicMock()
    mock_instance.get = AsyncMock(side_effect=[tags_resp, ps_resp])
    mock_client.return_value.__aenter__.return_value = mock_instance

    r = client.get("/models")
    assert r.status_code == 200
    data = r.json()
    # Fixed bug: should be empty, not fallback
    assert data["available"] == []
    assert data["default"] is None
    assert data["running"] == []


@patch("app.httpx.AsyncClient")
def test_models_fallback_when_ollama_unreachable(mock_client):
    mock_client.return_value.__aenter__.return_value.get = AsyncMock(side_effect=Exception("connection refused"))
    r = client.get("/models")
    assert r.status_code == 200
    data = r.json()
    # Fallback to env when Ollama down
    assert "phi4-mini:latest" in data["available"]
    assert data["default"] == "phi4-mini:latest"


def test_youtube_id_strips_timestamp():
    from helpers.transcript import _extract_video_id, _strip_timestamp

    # t=, start, time_continue stripped before ID extraction
    assert _extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42s") == "dQw4w9WgXcQ"
    assert _extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=1m30s&start=30") == "dQw4w9WgXcQ"
    assert _extract_video_id("https://youtu.be/dQw4w9WgXcQ?t=120") == "dQw4w9WgXcQ"
    assert _extract_video_id("https://www.youtube.com/shorts/dQw4w9WgXcQ?t=10") == "dQw4w9WgXcQ"

    # _strip_timestamp removes params
    assert "t=" not in _strip_timestamp("https://www.youtube.com/watch?v=abc12345678&t=120s")
    assert "start=" not in _strip_timestamp("https://www.youtube.com/watch?v=abc12345678&start=30")


@patch("helpers.transcript.YouTubeTranscriptApi")
def test_transcript_fetch_uses_stripped_id(mock_api):
    from helpers.transcript import transcript
    import asyncio

    mock_instance = MagicMock()
    mock_instance.fetch.return_value = [MagicMock(text="hello"), MagicMock(text="world")]
    mock_api.return_value = mock_instance

    # Should strip t= and fetch with clean ID
    title, text = asyncio.run(transcript("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42s"))
    # fetch called with clean ID, not including t=
    assert mock_instance.fetch.called
    args, kwargs = mock_instance.fetch.call_args
    assert args[0] == "dQw4w9WgXcQ"


@patch("app.stream_summary", new_callable=AsyncMock)
def test_summarize_transcript_requires_api_key(mock_summary):
    mock_summary.return_value = MagicMock()
    # No key -> 401, with key -> mocked success (not 401)
    r = client.post("/summarize/transcript", json={"text": "hello"})
    assert r.status_code == 401

    r = client.post("/summarize/transcript", json={"text": "hello"}, headers=HEADERS)
    assert r.status_code != 401
    mock_summary.assert_called_once()


def test_summarize_file_rejects_non_txt():
    import io
    files = {"file": ("test.pdf", io.BytesIO(b"hello"), "application/pdf")}
    r = client.post("/summarize/file", files=files, headers=HEADERS)
    assert r.status_code == 400
    assert "Only .txt" in r.text
