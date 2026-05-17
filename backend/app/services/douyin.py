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
            raise ValueError("无法解析抖音视频链接，请检查链接是否有效")

        video_url = video_info.get("video_url")
        if not video_url:
            raise ValueError("无法获取视频链接，抖音可能有反爬措施限制")

        return {
            "title": video_info.get("title", "抖音视频"),
            "cover_url": video_info.get("cover_url"),
            "duration": video_info.get("duration"),
            "platform": "douyin",
            "video_url": video_url
        }

    async def _fetch_video_info(self, share_url: str) -> Optional[dict]:
        """获取视频信息"""
        video_id = None
        real_url = None
        html_content = None

        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            }
        ) as client:
            # 访问分享链接
            response = await client.get(share_url)
            real_url = str(response.url)
            html_content = response.text

            # 提取视频 ID
            video_id_match = re.search(r'/video/(\d+)', real_url)
            if video_id_match:
                video_id = video_id_match.group(1)

        if not video_id or not html_content:
            return None

        # 从 HTML 中提取信息
        result = self._extract_from_html(html_content)

        # 如果从主页面提取不到，尝试移动端
        if not result.get("video_url"):
            mobile_result = await self._try_mobile_page(video_id)
            if mobile_result:
                result = mobile_result

        # 如果仍然没有 video_url，尝试构造
        if not result.get("video_url") and video_id:
            result["video_url"] = await self._try_construct_url(video_id, real_url)

        return result if result.get("title") or result.get("video_url") else None

    async def _try_mobile_page(self, video_id: str) -> Optional[dict]:
        """尝试从移动端页面获取视频信息"""
        try:
            mobile_url = f"https://m.douyin.com/share/video/{video_id}"
            async with httpx.AsyncClient(
                follow_redirects=True,
                timeout=30.0,
                headers={
                    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
                }
            ) as client:
                response = await client.get(mobile_url)
                return self._extract_from_html(response.text)
        except Exception:
            return None

    async def _try_construct_url(self, video_id: str, original_url: str) -> Optional[str]:
        """尝试构造视频 URL"""
        # 抖音视频的直接 URL 格式
        # 这个可能不工作，但值得尝试
        return None

    def _extract_from_html(self, html: str) -> dict:
        """从 HTML 中提取视频信息"""
        result = {"title": None, "video_url": None, "cover_url": None, "duration": None}

        # 提取标题
        result["title"] = self._extract_title(html)

        # 提取无水印视频链接
        video_url = None

        # 方法1: downloadAddr (通常无水印)
        download_match = re.search(r'"downloadAddr":"([^"]+)"', html)
        if download_match:
            video_url = download_match.group(1).replace("\\u002F", "/")

        # 方法2: playAddr (有水印但更稳定)
        if not video_url:
            play_match = re.search(r'"playAddr":"([^"]+)"', html)
            if play_match:
                video_url = play_match.group(1).replace("\\u002F", "/")

        # 方法3: 尝试从 playwm 提取并转换
        if not video_url:
            playwm_match = re.search(r'playwm\?url=([^&"]+)', html)
            if playwm_match:
                encoded_url = playwm_match.group(1)
                from urllib.parse import unquote
                decoded = unquote(encoded_url)
                video_url = decoded.replace("playwm", "play")

        result["video_url"] = video_url

        # 提取封面
        result["cover_url"] = self._extract_cover(html)

        return result

    def _extract_title(self, html: str) -> Optional[str]:
        """提取标题"""
        patterns = [
            r'<meta property="og:title" content="([^"]+)"',
            r'"desc":"([^"]+)"',
            r'<title>([^<]+)</title>',
            r'"nickname":"([^"]+)"',
        ]
        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                return match.group(1)
        return None

    def _extract_cover(self, html: str) -> Optional[str]:
        """提取封面 URL"""
        patterns = [
            r'<meta property="og:image" content="([^"]+)"',
            r'"cover":"([^"]+)"',
            r'"author_avatar":"([^"]+)"',
        ]
        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                return match.group(1)
        return None