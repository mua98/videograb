import httpx
import re
from typing import Optional

class DouyinParser:
    BASE_URL = "https://www.douyin.com"

    async def parse(self, share_url: str) -> dict:
        """
        解析抖音分享链接，返回视频信息
        1. 跟踪短链接重定向获取真实页面
        2. 解析页面提取视频信息
        3. 将 playwm 替换为 play 获取无水印链接
        """
        video_url = await self._get_video_url(share_url)
        if not video_url:
            raise ValueError("无法解析抖音视频链接")

        title = await self._get_title(share_url)
        return {
            "title": title or "抖音视频",
            "cover_url": None,
            "duration": None,
            "platform": "douyin",
            "video_url": video_url
        }

    async def _get_video_url(self, share_url: str) -> Optional[str]:
        """跟踪重定向并获取无水印视频链接"""
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            response = await client.get(share_url)
            real_url = str(response.url)

            # 从页面提取视频ID
            video_id = self._extract_video_id(real_url)
            if not video_id:
                return None

            # 尝试从页面源码中提取无水印链接
            html = response.text
            return self._extract_no_watermark_url(html)

    def _extract_video_id(self, url: str) -> Optional[str]:
        """从URL中提取视频ID"""
        patterns = [
            r'/video/(\d+)',
            r'v.douyin.com/([a-zA-Z0-9]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1) if len(match.groups()) == 1 else match.group(0)
        return None

    def _extract_no_watermark_url(self, html: str) -> Optional[str]:
        """从HTML中提取无水印视频链接"""
        # 尝试匹配 playwm 链接并替换为 play
        match = re.search(r'playwm\?url=([^&"]+)', html)
        if match:
            encoded_url = match.group(1)
            return f"https://www.iesdouyin.com/share/video/{encoded_url}/?region=CN&mid=..."

        # 尝试直接匹配 play 链接
        match = re.search(r'"playAddr":"([^"]+)"', html)
        if match:
            return match.group(1).replace("\\u002F", "/")

        return None

    async def _get_title(self, share_url: str) -> Optional[str]:
        """获取视频标题"""
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            response = await client.get(share_url)
            match = re.search(r'"desc":"([^"]+)"', response.text)
            if match:
                return match.group(1)
        return None