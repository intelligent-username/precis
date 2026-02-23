from typing import Optional
from pydantic import BaseModel


class YouTubeRequest(BaseModel):
    url: str
    model: Optional[str] = None


class TranscriptRequest(BaseModel):
    text: str
    title: Optional[str] = None
    model: Optional[str] = None
