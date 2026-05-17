from pydantic import BaseModel

class ParseRequest(BaseModel):
    url: str

class VideoInfo(BaseModel):
    title: str
    cover_url: str | None = None
    duration: int | None = None
    platform: str  # "douyin" or "bilibili"
    video_url: str | None = None

class ParseResponse(BaseModel):
    success: bool
    data: VideoInfo | None = None
    error: str | None = None

class HealthResponse(BaseModel):
    status: str