# 短视频去水印下载工具 - 设计文档

## 概述

一个公开的网页工具，支持抖音和B站短视频的链接解析与无水印下载。

## 技术栈

| 模块 | 技术选型 |
|------|----------|
| 前端 | Vue 3 + Vite + TailwindCSS |
| 后端 | FastAPI + httpx（异步请求） |
| 部署 | Docker（支持本地部署） |

## 功能范围

### 当前实现
- 抖音视频链接解析与下载（去水印）
- B站视频链接解析与下载
- 流式转发（不占用服务器存储）
- 支持 Docker 本地部署

### 预留扩展（待办）
- 管理后台 API 接口
- Token 验证机制
- 访问量统计

## 项目结构

```
/Users/xuwei/projects/zzxx/
├── docs/
│   └── superpowers/
│       └── specs/
│           └── 2026-05-17-video-downloader-design.md
├── frontend/                  # Vue 3 前端项目
│   ├── src/
│   │   ├── components/       # 组件
│   │   ├── views/            # 页面
│   │   ├── services/         # API 调用
│   │   └── App.vue
│   ├── index.html
│   └── package.json
├── backend/                   # FastAPI 后端项目
│   ├── app/
│   │   ├── routers/          # API 路由
│   │   ├── services/         # 解析服务
│   │   ├── models/           # 数据模型
│   │   └── main.py
│   ├── requirements.txt
│   └── Dockerfile
└── docker-compose.yml         # 容器编排
```

## API 设计

### 解析视频
```
POST /api/v1/parse
Body: { "url": "https://v.douyin.com/xxx" }
Response: { "title": "视频标题", "video_url": "无水印直链" }
```

### 获取视频（流式转发）
```
GET /api/v1/download?url=xxx
Response: 视频流（Content-Type: video/mp4）
```

### 健康检查
```
GET /api/v1/health
Response: { "status": "ok" }
```

## 后端服务设计

### 抖音解析
1. 跟踪短链接重定向，获取真实页面 URL
2. 解析页面提取视频信息
3. 将 `playwm` 替换为 `play` 获取无水印链接

### B站解析
1. 处理短链接 `b23.tv/xxx` 或 av/BV 号
2. 调用 B站官方 API 获取视频信息
3. 返回视频直链下载

## 前端页面设计

### 单页应用
- 顶部：工具标题
- 中间：链接输入框 + 解析按钮
- 下方：解析结果展示（标题、预览、下载按钮）

### 交互流程
1. 用户粘贴视频链接
2. 点击解析 → 调用后端 API
3. 显示视频信息（标题、封面）
4. 点击下载 → 流式转发获取视频

## 配置

### 环境变量
- `BACKEND_HOST`: 后端地址（默认 0.0.0.0）
- `BACKEND_PORT`: 后端端口（默认 8000）
- `FRONTEND_PORT`: 前端端口（默认 3000）

### Docker 环境
- 通过 `docker-compose.yml` 编排前后端服务