import httpx
import re
import json
from typing import Optional

class DouyinParser:
    BASE_URL = "https://www.douyin.com"

    async def parse(self, share_url: str) -> dict:
        """
        解析抖音分享链接，返回视频信息
        1. 跟踪短链接重定向获取真实页面
        2. 解析页面提取视频信息
        """
        video_info = await self._fetch_video_info(share_url)
        if not video_info:
            raise ValueError("无法解析抖音视频链接")

        return {
            "title": video_info.get("title", "抖音视频"),
            "cover_url": video_info.get("cover_url"),
            "duration": video_info.get("duration"),
            "platform": "douyin",
            "video_url": video_info.get("video_url")
        }

    async def _fetch_video_info(self, share_url: str) -> Optional[dict]:
        """获取视频信息"""
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
            }
        ) as client:
            response = await client.get(share_url)
            real_url = str(response.url)
            html = response.text

            # 尝试从 HTML 中提取 RENDER_DATA
            video_info = self._parse_render_data(html)
            if video_info:
                return video_info

            # 尝试从 URL 中提取视频 ID 并构建 API 请求
            video_id = self._extract_video_id(real_url)
            if video_id:
                return await self._fetch_via_api(client, video_id)

            return None

    def _parse_render_data(self, html: str) -> Optional[dict]:
        """从 HTML 中提取 RENDER_DATA JSON"""
        # 抖音使用 RENDER_DATA 或 __RENDER_DATA__ 存储视频信息
        patterns = [
            r'<script id="__RENDER_DATA__" type="application/json">([^<]+)</script>',
            r'"desc":"([^"]+)"',
            r'"playAddr":"([^"]+)"',
            r'"downloadAddr":"([^"]+)"',
        ]

        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                try:
                    if "desc" in pattern:
                        # 简单提取标题
                        title = match.group(1)
                        return {"title": title, "video_url": None, "cover_url": None, "duration": None}
                except:
                    continue
        return None

    def _extract_video_id(self, url: str) -> Optional[str]:
        """从 URL 中提取视频 ID"""
        patterns = [
            r'/video/(\d+)',
            r'v.douyin.com/([a-zA-Z0-9]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1) if len(match.groups()) == 1 else match.group(0)
        return None

    async def _fetch_via_api(self, client: httpx.AsyncClient, video_id: str) -> Optional[dict]:
        """通过视频 ID 获取视频信息"""
        # 抖音有 API 可以获取视频信息
        api_url = f"https://www.douyin.com/aweme/v1/web/aweme/detail/?aweme_id={video_id}"

        try:
            response = await client.get(api_url)
            data = response.json()

            if data.get("aweme_detail"):
                aweme = data["aweme_detail"]
                video_data = aweme.get("video", {})

                # 获取无水印视频链接
                video_url = None
                download_addr = video_data.get("download_addr", {})
                if download_addr:
                    video_url = download_addr.get("url_list", [None])[0]

                if not video_url:
                    play_addr = video_data.get("play_addr", {})
                    video_url = play_addr.get("url_list", [None])[0]

                return {
                    "title": aweme.get("desc", "抖音视频"),
                    "cover_url": video_data.get("cover", {}).get("url_list", [None])[0],
                    "duration": video_data.get("duration"),
                    "video_url": video_url
                }
        except Exception:
            pass

        return None