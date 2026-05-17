# VideoGrab - 短视频去水印下载工具

支持抖音、B站视频链接解析与无水印下载的在线工具。

## 功能特点

- 支持抖音视频链接解析（去水印）
- 支持 B站视频链接解析（av号、BV号、b23.tv短链接）
- 流式转发下载，不占用服务器存储
- 支持 Docker 部署
- 预留管理后台 API 接口（Token 验证、访问统计）

## 技术栈

| 模块 | 技术选型 |
|------|----------|
| 前端 | Vue 3 + Vite + TailwindCSS |
| 后端 | FastAPI + httpx（异步请求） |
| 部署 | Docker Compose |

## 项目结构

```
videograb/
├── backend/                  # FastAPI 后端
│   ├── app/
│   │   ├── routers/         # API 路由
│   │   ├── services/        # 解析服务（抖音、B站）
│   │   ├── models/          # Pydantic 模型
│   │   └── main.py          # 应用入口
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                 # Vue 3 前端
│   ├── src/
│   │   ├── components/      # 组件
│   │   ├── services/        # API 调用
│   │   └── App.vue
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── docker-compose.yml
└── docs/                     # 设计文档
```

## 开发

### 前置条件

- Python 3.11+
- Node.js 20+
- pnpm

### 后端启动

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 前端启动

```bash
cd frontend
pnpm install
pnpm dev
```

### 访问

- 前端页面：http://localhost:3000
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

## 部署

### Docker 部署（推荐）

```bash
# 构建并启动
docker-compose up -d

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 手动部署

```bash
# 后端
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 前端构建
cd frontend
pnpm install
pnpm build
# 使用 Nginx 托管 dist 目录
```

### 访问部署服务

- 前端：http://localhost:3000
- 后端：http://localhost:8000

## API 接口

### 健康检查

```
GET /api/v1/health
```

### 解析视频

```
POST /api/v1/parse
Content-Type: application/json

{
  "url": "https://v.douyin.com/xxx"
}

# 响应
{
  "success": true,
  "data": {
    "title": "视频标题",
    "cover_url": "封面URL",
    "duration": 60,
    "platform": "douyin",
    "video_url": "无水印视频直链"
  }
}
```

### 下载视频

```
GET /api/v1/download?url=视频直链
```

返回流式视频数据，直接下载或播放。

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `TZ` | Asia/Shanghai | 时区 |

## 待办功能

- [ ] 管理后台 API 接口
- [ ] Token 验证机制
- [ ] 访问量统计
- [ ] SFTP 上传功能

## License

MIT