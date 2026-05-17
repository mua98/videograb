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
        """
        video_info = await self._fetch_video_info(share_url)
        if not video_info:
            raise ValueError("无法解析抖音视频链接")

        video_url = video_info.get("video_url")
        if not video_url:
            raise ValueError("无法获取视频链接，请检查链接是否有效")

        return {
            "title": video_info.get("title", "抖音视频"),
            "cover_url": video_info.get("cover_url"),
            "duration": video_info.get("duration"),
            "platform": "douyin",
            "video_url": video_url
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

            # 从 URL 中提取视频 ID
            video_id = self._extract_video_id(real_url)
            if not video_id:
                return None

            # 通过 API 获取视频信息
            return await self._fetch_via_api(client, video_id, real_url)

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

    async def _fetch_via_api(self, client: httpx.AsyncClient, video_id: str, original_url: str) -> Optional[dict]:
        """通过视频 ID 获取视频信息"""
        # 尝试多个 API 端点
        api_endpoints = [
            f"https://www.douyin.com/aweme/v1/web/aweme/detail/?aweme_id={video_id}",
            f"https://www.iesdouyin.com/share/video/{video_id}/",
        ]

        for api_url in api_endpoints:
            try:
                response = await client.get(api_url, follow_redirects=True)
                html = response.text

                # 从 HTML 中提取视频信息
                video_info = self._extract_from_html(html)
                if video_info and video_info.get("video_url"):
                    return video_info
            except Exception:
                continue

        # 最后尝试直接解析页面
        try:
            response = await client.get(original_url)
            return self._extract_from_html(response.text)
        except Exception:
            pass

        return None

    def _extract_from_html(self, html: str) -> Optional[dict]:
        """从 HTML 中提取视频信息"""
        result = {}

        # 提取标题
        title_match = re.search(r'"desc":"([^"]+)"', html)
        if title_match:
            result["title"] = title_match.group(1)
        else:
            result["title"] = "抖音视频"

        # 提取无水印视频链接
        video_url = None

        # 尝试 playAddr (有水印但更稳定)
        play_match = re.search(r'"playAddr":"([^"]+)"', html)
        if play_match:
            video_url = play_match.group(1).replace("\\u002F", "/")

        # 尝试 downloadAddr (无水印)
        if not video_url:
            download_match = re.search(r'"downloadAddr":"([^"]+)"', html)
            if download_match:
                video_url = download_match.group(1).replace("\\u002F", "/")

        # 尝试 playwm 替换为 play
        if not video_url:
            playwm_match = re.search(r'playwm\?url=([^&"]+)', html)
            if playwm_match:
                video_url = playwm_match.group(1)

        result["video_url"] = video_url
        result["cover_url"] = None
        result["duration"] = None

        return result if video_url else None