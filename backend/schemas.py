from typing import Optional
from pydantic import BaseModel, Field

from config import MAX_TRANSCRIPT_CHARS


class YouTubeRequest(BaseModel):
    url: str = Field(min_length=10, max_length=2048)
    model: Optional[str] = None


class TranscriptRequest(BaseModel):
    text: str = Field(min_length=1, max_length=MAX_TRANSCRIPT_CHARS)
    title: Optional[str] = None
    model: Optional[str] = None
