from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
import httpx
from app.models.schemas import ParseRequest, ParseResponse, VideoInfo
from app.services.douyin import DouyinParser
from app.services.bilibili import BilibiliParser

router = APIRouter()
douyin_parser = DouyinParser()
bilibili_parser = BilibiliParser()

@router.get("/health")
async def health():
    return {"status": "ok"}

@router.post("/parse", response_model=ParseResponse)
async def parse_video(request: ParseRequest):
    try:
        url = request.url.strip()

        # 检测平台
        if "douyin.com" in url:
            result = await douyin_parser.parse(url)
            return ParseResponse(
                success=True,
                data=VideoInfo(**result)
            )
        elif "bilibili.com" in url or "b23.tv" in url:
            result = await bilibili_parser.parse(url)
            return ParseResponse(
                success=True,
                data=VideoInfo(**result)
            )
        else:
            raise HTTPException(status_code=400, detail="不支持的链接平台")

    except Exception as e:
        return ParseResponse(
            success=False,
            error=str(e)
        )

@router.get("/download")
async def download_video(url: str = Query(..., description="视频直链URL")):
    """
    流式转发视频到用户浏览器
    不占用服务器存储空间
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.douyin.com/",
        }

        async def stream_content():
            async with httpx.AsyncClient(follow_redirects=True, timeout=300.0) as client:
                async with client.stream("GET", url, headers=headers) as response:
                    response.raise_for_status()
                    async for chunk in response.aiter_bytes(chunk_size=1024 * 1024):
                        yield chunk

        return StreamingResponse(
            stream_content(),
            media_type="video/mp4",
            headers={
                "Content-Disposition": "attachment; filename=video.mp4",
                "Accept-Ranges": "bytes",
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载失败: {str(e)}")