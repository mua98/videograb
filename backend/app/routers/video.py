from fastapi import APIRouter, HTTPException
from app.models.schemas import ParseRequest, ParseResponse, VideoInfo
from app.services.douyin import DouyinParser

router = APIRouter()
douyin_parser = DouyinParser()

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
        else:
            raise HTTPException(status_code=400, detail="不支持的链接平台")

    except Exception as e:
        return ParseResponse(
            success=False,
            error=str(e)
        )