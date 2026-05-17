import httpx
import re
from typing import Optional

class BilibiliParser:
    B23_REGEX = r'b23\.tv/([a-zA-Z0-9]+)'
    AV_REGEX = r'(av\d+|BV[a-zA-Z0-9]+)'
    API_URL = "https://api.bilibili.com/x/web-interface/view"

    async def parse(self, share_url: str) -> dict:
        """
        解析B站分享链接，返回视频信息
        1. 处理短链接 b23.tv 或 av/BV 号
        2. 调用B站官方API获取视频信息
        """
        # 如果是短链接，先解析真实URL
        video_id = await self._extract_video_id(share_url)
        if not video_id:
            raise ValueError("无法解析B站视频链接")

        # 调用B站API获取视频信息
        info = await self._get_video_info(video_id)
        return {
            "title": info.get("title", "B站视频"),
            "cover_url": info.get("pic"),
            "duration": info.get("duration"),
            "platform": "bilibili",
            "video_url": info.get("video_url")
        }

    async def _extract_video_id(self, url: str) -> Optional[str]:
        """从URL中提取视频ID"""
        # 处理短链接 b23.tv
        match = re.search(self.B23_REGEX, url)
        if match:
            async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
                response = await client.get(f"https://{match.group(0)}")
                url = str(response.url)

        # 提取 av 或 BV 号
        match = re.search(self.AV_REGEX, url)
        if match:
            return match.group(0)

        return None

    async def _get_video_info(self, video_id: str) -> dict:
        """调用B站API获取视频信息"""
        params = {"bvid": video_id} if video_id.startswith("BV") else {"aid": video_id.replace("av", "")}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(self.API_URL, params=params)
            data = response.json()

            if data.get("code") != 0:
                raise ValueError(f"B站API返回错误: {data.get('message')}")

            video_data = data["data"]
            return {
                "title": video_data["title"],
                "pic": video_data["pic"],
                "duration": video_data["duration"],
                "video_url": video_data["videourl"]
            }