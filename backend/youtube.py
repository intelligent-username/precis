"""
YouTube transcript extraction.
"""

import re

from fastapi import HTTPException
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)

YT_ID_RE = re.compile(r"(?:v=|youtu\.be/|embed/|shorts/)([A-Za-z0-9_-]{11})")


def extract_video_id(url: str) -> str:
    match = YT_ID_RE.search(url)
    if not match:
        raise HTTPException(status_code=400, detail="Could not extract a video ID from that URL.")
    return match.group(1)


def fetch_transcript(video_id: str) -> str:
    """Synchronous transcript fetch. Call via asyncio.to_thread."""
    try:
        ytt = YouTubeTranscriptApi()
        fetch = getattr(ytt, "fetch", None) or getattr(YouTubeTranscriptApi, "get_transcript", None)
        if fetch is None:
            raise AttributeError("No transcript fetch method")
        try:
            transcript = fetch(video_id, languages=["en", "en-US", "en-GB"]) if fetch is getattr(ytt, "fetch", None) else fetch(video_id, languages=["en", "en-US", "en-GB"])
        except TypeError:
            transcript = fetch(video_id)
    except TranscriptsDisabled:
        raise HTTPException(status_code=422, detail="This video has transcripts disabled.")
    except NoTranscriptFound:
        raise HTTPException(status_code=422, detail="No transcript found for this video.")
    except VideoUnavailable:
        raise HTTPException(status_code=404, detail="Video is unavailable or does not exist.")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Transcript fetch failed: {exc}")

    return " ".join(snippet.text for snippet in transcript)
