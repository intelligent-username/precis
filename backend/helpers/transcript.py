"""
Async YouTube transcript + title fetcher.

Public API
----------
    title, text = await transcript(url_or_id)

* ``title`` is the video title (str) or ``None`` if unavailable.
* ``text``  is the joined transcript body (str).

Both the title fetch (YouTube oEmbed) and the transcript fetch
(youtube_transcript_api, run in a thread) are launched concurrently,
so total latency is max(title_time, transcript_time) rather than the sum.
"""

from __future__ import annotations

import asyncio
import re
import urllib.parse
from typing import Optional

import httpx
from fastapi import HTTPException
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_YT_ID_RE = re.compile(r"(?:v=|youtu\.be/|embed/|shorts/)([A-Za-z0-9_-]{11})")
_OEMBED_URL = "https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
_LANG_PREFS = ["en", "en-US", "en-GB"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _strip_timestamp(url: str) -> str:
    """Strip t/start/time_continue from YouTube URLs so transcript fetch ignores timestamp."""
    try:
        parsed = urllib.parse.urlparse(url)
        # query e.g. ?v=abc&t=120s&start=30
        q = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
        for k in ("t", "start", "time_continue"):
            q.pop(k, None)
        # fragment e.g. #t=120s
        frag = parsed.fragment
        if frag:
            # handle #t=1m30s or #t=90
            if frag.startswith("t="):
                frag = ""
            else:
                fq = urllib.parse.parse_qs(frag, keep_blank_values=True)
                for k in ("t", "start", "time_continue"):
                    fq.pop(k, None)
                frag = urllib.parse.urlencode(fq, doseq=True)
        new_query = urllib.parse.urlencode(q, doseq=True)
        return urllib.parse.urlunparse(parsed._replace(query=new_query, fragment=frag))
    except Exception:
        return url


def _extract_video_id(url: str) -> str:
    """Return the 11-char video ID from a YouTube URL or bare ID."""
    # Strip timestamp first (t=120s, t=1m30s, &start=, etc.) — transcript is always full
    url = _strip_timestamp(url)
    # Accept a bare 11-char ID directly
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", url):
        return url
    match = _YT_ID_RE.search(url)
    if not match:
        raise HTTPException(
            status_code=400,
            detail="Could not extract a video ID from that URL.",
        )
    return match.group(1)


def _fetch_transcript_sync(video_id: str) -> str:
    """Blocking transcript fetch. Always call via ``asyncio.to_thread``."""
    try:
        ytt = YouTubeTranscriptApi()
        fetch = getattr(ytt, "fetch", None) or getattr(YouTubeTranscriptApi, "get_transcript", None)
        if fetch is None:
            raise AttributeError("No transcript fetch method")
        # instance fetch vs static get_transcript have different signatures
        try:
            t = fetch(video_id, languages=_LANG_PREFS) if fetch is getattr(ytt, "fetch", None) else fetch(video_id, languages=_LANG_PREFS)
        except TypeError:
            t = fetch(video_id)
    except TranscriptsDisabled:
        raise HTTPException(
            status_code=422,
            detail="This video has transcripts disabled.",
        )
    except NoTranscriptFound:
        raise HTTPException(
            status_code=422,
            detail="No English transcript found for this video.",
        )
    except VideoUnavailable:
        raise HTTPException(
            status_code=404,
            detail="Video is unavailable or does not exist.",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Transcript fetch failed: {exc}",
        )
    return " ".join(snippet.text for snippet in t)


async def _fetch_title(video_id: str) -> Optional[str]:
    """Fetch the video title via YouTube's oEmbed endpoint (non-blocking)."""
    url = _OEMBED_URL.format(video_id=video_id)
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(url)
            if r.status_code == 200:
                return r.json().get("title")
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def transcript(url: str) -> tuple[Optional[str], str]:
    """Fetch (title, transcript_text) for a YouTube URL concurrently.

    Parameters
    ----------
    url:
        A full YouTube URL or a bare 11-character video ID.

    Returns
    -------
    (title, text):
        ``title`` is the video title or ``None``; ``text`` is the plain-text
        transcript suitable for passing directly to ``stream_summary``.
    """
    video_id = _extract_video_id(url)

    # Run the blocking transcript fetch in a thread while the async title
    # fetch runs on the event loop (parallel).
    title_task = asyncio.create_task(_fetch_title(video_id))
    text = await asyncio.to_thread(_fetch_transcript_sync, video_id)

    # Give the title at most 1 extra second after the transcript is done.
    # oEmbed can be slow; we never want it to be the bottleneck.
    try:
        title = await asyncio.wait_for(asyncio.shield(title_task), timeout=1.0)
    except (asyncio.TimeoutError, Exception):
        title_task.cancel()
        title = None

    # Return the fetched title (or None if unavailable) and the transcript text.
    # Callers (e.g., backend/app.py) forward the title to `stream_summary`, which includes it in the prompt
    # via `build_prompt`. If `title` is None, the prompt omits the title block, which is appropriate for
    # plain‑text or other non‑title scenarios.
    return title, text
