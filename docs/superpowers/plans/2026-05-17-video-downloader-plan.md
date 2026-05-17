# 短视频去水印下载工具 - 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个公开的网页工具，支持抖音和B站短视频的链接解析与无水印下载

**Architecture:** 前端 Vue 3 单页应用调用后端 FastAPI 服务，后端负责解析各平台视频链接并通过流式转发将视频推送给用户浏览器，不占用服务器存储空间

**Tech Stack:** Vue 3 + Vite + TailwindCSS (前端) | FastAPI + httpx (后端) | Docker

---

## 文件结构

```
/Users/xuwei/projects/zzxx/
├── docs/superpowers/
│   ├── specs/2026-05-17-video-downloader-design.md
│   └── plans/2026-05-17-video-downloader-plan.md
├── frontend/
│   ├── src/
│   │   ├── components/VideoParser.vue    # 主解析组件
│   │   ├── services/api.js              # API 调用
│   │   ├── App.vue
│   │   └── main.js
│   ├── index.html
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── package.json
├── backend/
│   ├── app/
│   │   ├── routers/
│   │   │   └── video.py                 # 视频解析API
│   │   ├── services/
│   │   │   ├── douyin.py                # 抖音解析服务
│   │   │   └── bilibili.py              # B站解析服务
│   │   ├── models/
│   │   │   └── schemas.py               # Pydantic模型
│   │   └── main.py
│   ├── requirements.txt
│   └── Dockerfile
└── docker-compose.yml
```

---

## Task 1: 后端项目基础结构

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/schemas.py`
- Create: `backend/app/routers/__init__.py`
- Create: `backend/app/services/__init__.py`

- [ ] **Step 1: 创建 requirements.txt**

```txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
httpx==0.26.0
pydantic==2.5.3
python-dotenv==1.0.0
```

- [ ] **Step 2: 创建 Pydantic 模型**

```python
# backend/app/models/schemas.py
from pydantic import BaseModel

class ParseRequest(BaseModel):
    url: str

class VideoInfo(BaseModel):
    title: str
    cover_url: str | None = None
    duration: int | None = None
    platform: str  # "douyin" or "bilibili"

class ParseResponse(BaseModel):
    success: bool
    data: VideoInfo | None = None
    error: str | None = None

class HealthResponse(BaseModel):
    status: str
```

- [ ] **Step 3: 创建 FastAPI 主应用**

```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import video

app = FastAPI(title="Video Downloader API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(video.router, prefix="/api/v1")

@app.get("/api/v1/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 4: 创建健康检查路由**

```python
# backend/app/routers/video.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 5: 提交**

```bash
cd backend && pip install -r requirements.txt && cd ..
git add backend/requirements.txt backend/app/
git commit -m "feat: scaffold backend project structure

- Add FastAPI main app with CORS middleware
- Add Pydantic models for request/response
- Add health endpoint"

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
```

---

## Task 2: 抖音解析服务

**Files:**
- Create: `backend/app/services/douyin.py`
- Modify: `backend/app/routers/video.py:17-50`

- [ ] **Step 1: 编写抖音解析服务**

```python
# backend/app/services/douyin.py
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
```

- [ ] **Step 2: 更新路由添加解析接口**

```python
# backend/app/routers/video.py
from fastapi import APIRouter, HTTPException
from app.models.schemas import ParseRequest, ParseResponse, VideoInfo
from app.services.douyin import DouyinParser

router = APIRouter()
douyin_parser = DouyinParser()

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
```

- [ ] **Step 3: 提交**

```bash
git add backend/app/services/douyin.py backend/app/routers/video.py
git commit -m "feat: add Douyin parser service

- Track redirect to get real video page
- Extract video info and no-watermark URL
- Add /parse endpoint in router"

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
```

---

## Task 3: B站解析服务

**Files:**
- Create: `backend/app/services/bilibili.py`
- Modify: `backend/app/routers/video.py:1-70`

- [ ] **Step 1: 编写B站解析服务**

```python
# backend/app/services/bilibili.py
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
                "video_url": video_data["videourl"]  # B站官方直链通常无水印
            }
```

- [ ] **Step 2: 更新路由支持双平台**

```python
# backend/app/routers/video.py
from app.services.bilibili import BilibiliParser

router = APIRouter()
douyin_parser = DouyinParser()
bilibili_parser = BilibiliParser()

@router.post("/parse", response_model=ParseResponse)
async def parse_video(request: ParseRequest):
    try:
        url = request.url.strip()

        if "douyin.com" in url:
            result = await douyin_parser.parse(url)
        elif "bilibili.com" in url or "b23.tv" in url:
            result = await bilibili_parser.parse(url)
        else:
            raise HTTPException(status_code=400, detail="不支持的链接平台")

        return ParseResponse(
            success=True,
            data=VideoInfo(**result)
        )

    except HTTPException:
        raise
    except Exception as e:
        return ParseResponse(
            success=False,
            error=str(e)
        )
```

- [ ] **Step 3: 提交**

```bash
git add backend/app/services/bilibili.py backend/app/routers/video.py
git commit -m "feat: add Bilibili parser service

- Support b23.tv short links and av/BV URLs
- Use official Bilibili API for video info
- Update router to handle both platforms"

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
```

---

## Task 4: 流式下载接口

**Files:**
- Modify: `backend/app/routers/video.py:70-120`

- [ ] **Step 1: 添加流式下载路由**

```python
# backend/app/routers/video.py
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
import httpx

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
```

- [ ] **Step 2: 提交**

```bash
git add backend/app/routers/video.py
git commit -m "feat: add streaming video download endpoint

- Stream video directly to browser without server storage
- Support range requests for seeking"

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
```

---

## Task 5: 前端项目基础结构

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.js`
- Create: `frontend/tailwind.config.js`
- Create: `frontend/index.html`
- Create: `frontend/src/main.js`
- Create: `frontend/src/App.vue`
- Create: `frontend/postcss.config.js`

- [ ] **Step 1: 创建 package.json**

```json
{
  "name": "video-downloader-frontend",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.4.15",
    "axios": "^1.6.5"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.3",
    "vite": "^5.0.11",
    "tailwindcss": "^3.4.1",
    "postcss": "^8.4.33",
    "autoprefixer": "^10.4.17"
  }
}
```

- [ ] **Step 2: 创建 Vite 配置**

```javascript
// frontend/vite.config.js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
```

- [ ] **Step 3: 创建 Tailwind 配置**

```javascript
// frontend/tailwind.config.js
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

- [ ] **Step 4: 创建 PostCSS 配置**

```javascript
// frontend/postcss.config.js
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

- [ ] **Step 5: 创建 HTML 入口**

```html
<!-- frontend/index.html -->
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>短视频去水印下载</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.js"></script>
  </body>
</html>
```

- [ ] **Step 6: 创建入口文件**

```javascript
// frontend/src/main.js
import { createApp } from 'vue'
import './style.css'
import App from './App.vue'

createApp(App).mount('#app')
```

- [ ] **Step 7: 创建全局样式**

```css
/* frontend/src/style.css */
@tailwind base;
@tailwind components;
@tailwind utilities;
```

- [ ] **Step 8: 创建 App.vue 基础结构**

```vue
<!-- frontend/src/App.vue -->
<script setup>
// App.vue will be updated in Task 7
</script>

<template>
  <div class="min-h-screen bg-gray-100">
    <h1 class="text-3xl font-bold">短视频去水印下载</h1>
  </div>
</template>
```

- [ ] **Step 9: 安装依赖并提交**

```bash
cd frontend && pnpm install && cd ..
git add frontend/package.json frontend/vite.config.js frontend/tailwind.config.js frontend/postcss.config.js frontend/index.html frontend/src/
git commit -m "feat: scaffold Vue 3 frontend project

- Add Vite + Vue 3 + TailwindCSS setup
- Configure dev proxy to backend API"

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
```

---

## Task 6: 前端主解析组件

**Files:**
- Create: `frontend/src/components/VideoParser.vue`
- Create: `frontend/src/services/api.js`

- [ ] **Step 1: 创建 API 服务**

```javascript
// frontend/src/services/api.js
import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 60000,
})

export const parseVideo = (url) => api.post('/parse', { url })

export const downloadVideo = (videoUrl) => `/api/v1/download?url=${encodeURIComponent(videoUrl)}`
```

- [ ] **Step 2: 创建 VideoParser 组件**

```vue
<!-- frontend/src/components/VideoParser.vue -->
<script setup>
import { ref } from 'vue'
import { parseVideo, downloadVideo } from '../services/api'

const videoUrl = ref('')
const loading = ref(false)
const result = ref(null)
const error = ref('')

const handleParse = async () => {
  if (!videoUrl.value.trim()) {
    error.value = '请输入视频链接'
    return
  }

  loading.value = true
  error.value = ''
  result.value = null

  try {
    const response = await parseVideo(videoUrl.value)
    if (response.data.success) {
      result.value = response.data.data
    } else {
      error.value = response.data.error || '解析失败'
    }
  } catch (err) {
    error.value = '网络错误，请稍后重试'
  } finally {
    loading.value = false
  }
}

const handleDownload = () => {
  if (!result.value?.video_url) return
  const url = downloadVideo(result.value.video_url)
  window.open(url, '_blank')
}
</script>

<template>
  <div class="max-w-2xl mx-auto p-6">
    <!-- 标题 -->
    <div class="text-center mb-8">
      <h1 class="text-4xl font-bold text-gray-800 mb-2">短视频去水印下载</h1>
      <p class="text-gray-500">支持抖音、B站视频解析下载</p>
    </div>

    <!-- 输入区域 -->
    <div class="bg-white rounded-xl shadow-lg p-6 mb-6">
      <div class="flex gap-4">
        <input
          v-model="videoUrl"
          type="text"
          placeholder="粘贴视频链接..."
          class="flex-1 px-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          @keyup.enter="handleParse"
        />
        <button
          @click="handleParse"
          :disabled="loading"
          class="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 transition"
        >
          {{ loading ? '解析中...' : '解析' }}
        </button>
      </div>
    </div>

    <!-- 错误提示 -->
    <div v-if="error" class="bg-red-50 text-red-600 p-4 rounded-lg mb-6">
      {{ error }}
    </div>

    <!-- 结果展示 -->
    <div v-if="result" class="bg-white rounded-xl shadow-lg p-6">
      <div class="flex gap-6">
        <!-- 封面 -->
        <div v-if="result.cover_url" class="w-48 h-28 bg-gray-100 rounded-lg overflow-hidden flex-shrink-0">
          <img :src="result.cover_url" alt="封面" class="w-full h-full object-cover" />
        </div>
        <!-- 信息 -->
        <div class="flex-1">
          <h3 class="text-lg font-semibold text-gray-800 mb-2">{{ result.title }}</h3>
          <div class="flex items-center gap-4 text-sm text-gray-500 mb-4">
            <span class="px-2 py-1 bg-blue-100 text-blue-600 rounded">{{ result.platform }}</span>
            <span v-if="result.duration">{{ result.duration }}秒</span>
          </div>
          <button
            @click="handleDownload"
            class="px-6 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition"
          >
            下载视频
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
```

- [ ] **Step 3: 更新 App.vue**

```vue
<!-- frontend/src/App.vue -->
<script setup>
import VideoParser from './components/VideoParser.vue'
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-12">
    <VideoParser />
  </div>
</template>
```

- [ ] **Step 4: 提交**

```bash
git add frontend/src/components/VideoParser.vue frontend/src/services/api.js frontend/src/App.vue
git commit -m "feat: add VideoParser component

- Add URL input and parse button
- Display video info (title, cover, duration)
- Add download button with streaming URL"

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
```

---

## Task 7: Docker 配置

**Files:**
- Create: `backend/Dockerfile`
- Create: `frontend/Dockerfile`
- Create: `docker-compose.yml`

- [ ] **Step 1: 创建后端 Dockerfile**

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: 创建前端 Dockerfile**

```dockerfile
# frontend/Dockerfile
FROM node:20-alpine as builder

WORKDIR /app
COPY package.json .
RUN npm install -g pnpm && pnpm install

COPY . .
RUN pnpm build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
```

- [ ] **Step 3: 创建 Nginx 配置**

```nginx
# frontend/nginx.conf
server {
    listen 3000;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

- [ ] **Step 4: 创建 docker-compose.yml**

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - TZ=Asia/Shanghai

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
```

- [ ] **Step 5: 提交**

```bash
git add backend/Dockerfile frontend/Dockerfile frontend/nginx.conf docker-compose.yml
git commit -m "feat: add Docker configuration

- Backend: Python FastAPI container
- Frontend: Node + Nginx container
- docker-compose orchestration"

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
```

---

## Task 8: 验证部署

**Files:**
- None (验证步骤)

- [ ] **Step 1: 构建 Docker 镜像**

```bash
docker-compose build
```

- [ ] **Step 2: 启动服务**

```bash
docker-compose up -d
```

- [ ] **Step 3: 检查服务状态**

```bash
docker-compose ps
```

- [ ] **Step 4: 测试健康检查**

```bash
curl http://localhost:8000/api/v1/health
# 预期: {"status": "ok"}
```

- [ ] **Step 5: 访问前端页面**

打开浏览器访问 http://localhost:3000

---

## 计划总结

| Task | 内容 | 优先级 |
|------|------|--------|
| 1 | 后端基础结构 | P0 |
| 2 | 抖音解析服务 | P0 |
| 3 | B站解析服务 | P0 |
| 4 | 流式下载接口 | P0 |
| 5 | 前端基础结构 | P0 |
| 6 | 前端主组件 | P0 |
| 7 | Docker配置 | P0 |
| 8 | 验证部署 | P0 |

## 待办扩展（不在本计划内）
- 管理后台API接口
- Token验证机制
- 访问量统计
- SFTP上传功能