# Daily Intensive Reading

每日精读运营工具，用于维护信息源、管理提示词、抓取网页内容、调用大模型生成精读卡片，并将结果保存为可复用的收藏卡片。

项目是一个前后端分离的 Docker Compose 应用：

- 前端：React + Vite + TypeScript + Ant Design + Zustand
- 后端：Flask + Gunicorn + SQLAlchemy + Alembic
- 数据库：MySQL 8
- 缓存：Redis
- 入口代理：Nginx
- 内容抓取：Direct HTTP -> JigsawStack -> Firecrawl fallback
- 大模型：DeepSeek/OpenAI-compatible API

## 功能概览

- 信息源管理：新增、编辑、删除和查看内容来源。
- 提示词管理：维护报告生成、卡片生成、URL 筛选等提示词。
- 每日精读生成：从信息源抓取网页，筛选高价值链接，生成精读卡片。
- 单链接卡片生成：对单个 URL 抓取正文并生成卡片。
- 海报内容生成：基于已抓取或缓存的原文生成适合海报展示的内容。
- 收藏卡片管理：保存、搜索、更新和删除卡片。
- 爬虫配额观测：查看 JigsawStack key 的使用和失败状态。
- Redis 内容缓存：成功抓取的 URL 内容缓存 14 天，避免重复爬取和浪费 API 额度。

## 系统架构

```text
Browser
  |
  v
Nginx :20001
  |-- /              -> frontend container (static React app)
  |-- /api/*         -> backend container (Flask/Gunicorn)
                         |
                         |-- MySQL: sources/prompts/cards
                         |-- Redis: scraped content cache + quota state
                         |-- Direct HTTP scraper
                         |-- JigsawStack scraper
                         |-- Firecrawl fallback scraper
                         |-- DeepSeek/OpenAI-compatible model API
```

### Docker 服务

| Service | 作用 | 说明 |
| --- | --- | --- |
| `nginx` | 对外入口 | 宿主机端口 `20001`，转发静态页面和 API |
| `frontend` | 前端静态应用 | Vite build 后由容器内 Nginx 提供 |
| `backend` | Flask API | Gunicorn + gevent，启动时执行 Alembic migration |
| `mysql` | 业务数据 | 默认数据目录 `/data/daily_intensive_reading/mysql` |
| `redis` | 内容缓存和状态缓存 | 默认数据目录 `/data/daily_intensive_reading/redis` |

### 后端模块

```text
backend/app/
  app.py                    # Flask app, CORS, health check, blueprint registration
  config/db.py              # SQLAlchemy engine/session
  migrations/               # 初始化数据逻辑
  models/models.py          # sources/prompts/favorite_cards 数据模型
  routes/                   # API 路由层
  schemas/schemas.py        # Marshmallow schema
  services/
    content_cache.py        # Redis 内容缓存统一入口
    scraper_service.py      # Direct HTTP/JigsawStack/Firecrawl 编排和 quota 追踪
    firecrawl_service.py    # Firecrawl API fallback
    deepseek_service.py     # DeepSeek/OpenAI-compatible 调用和内容生成
  utils/logger.py           # 日志
```

### 前端模块

```text
frontend/src/
  App.tsx
  pages/                    # 页面级组件
  components/               # 布局、执行流、设置、来源表单等组件
  services/                 # axios API client 和各业务 API service
  store/                    # Zustand stores
  types/                    # 前端类型定义
```

## 核心流程

### 每日精读生成流程

1. 用户在前端选择信息源和提示词。
2. 前端调用 `POST /api/daily-reading/generate`。
3. 后端批量抓取信息源页面。
4. 爬虫按顺序尝试：
   - Redis 内容缓存
   - Direct HTTP + BeautifulSoup
   - JigsawStack
   - Firecrawl fallback（仅配置 `FIRECRAWL_API_TOKEN` 时启用）
5. DeepSeek/OpenAI-compatible 模型从抓取内容中筛选高价值 URL。
6. 后端继续抓取筛选出的内容详情。
7. 模型生成精读卡片。
8. 后端返回结果，并将历史结果写入后端输出目录。

### 内容缓存策略

- 缓存模块：`backend/app/services/content_cache.py`
- 缓存 key：`content:{md5(url)}`
- 缓存时间：14 天，即 `1209600` 秒
- 缓存内容：成功抓取后的正文/Markdown 内容
- 命中缓存时：`scrape_single_url` 返回 `provider: "cache"`
- arXiv HTML 错误页：会清理对应缓存并回退到 `/abs/` 摘要页重试

### JigsawStack 配额保护

- 支持多个 `JigsawStack_APIKEYs`，逗号分隔。
- 单 key 出现 quota 错误时，会在 Redis 中标记一段时间，后续请求跳过该 key。
- 项目级 quota 耗尽时，会短期缓存耗尽状态，避免继续消耗无效请求。
- 可通过 `GET /api/daily-reading/quota-status` 查看状态。

## 快速启动

### 1. 准备配置文件

从示例复制配置：

```bash
cp .env.example .env
cp backend/.env.example backend/.env
```

编辑 `.env` 和 `backend/.env`。不要提交真实密钥。

根目录 `.env` 主要给 Docker Compose 使用：

```bash
DB_USER=root
DB_PASSWORD=changeme
DB_NAME=everyday_card
```

后端 `backend/.env` 常用配置：

```bash
DB_USER=root
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=3306
DB_NAME=everyday_card

OPENAI_API_KEY=your_openai_api_key_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL_NAME=deepseek-chat

JigsawStack_APIKEYs=
FIRECRAWL_API_TOKEN=

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
```

Docker Compose 会覆盖后端容器内的数据库和 Redis 地址，让后端连接 Compose 内部服务：

```text
DB_HOST=mysql
REDIS_HOST=redis
```

### 2. Docker 启动

推荐用 Docker 运行完整栈：

```bash
docker compose up -d --build
```

如果需要确保所有容器都用最新镜像重建：

```bash
docker compose up -d --build --force-recreate
```

访问：

```text
http://localhost:20001
```

健康检查：

```bash
curl -i http://localhost:20001/api/health
```

查看服务状态：

```bash
docker compose ps
```

查看日志：

```bash
docker compose logs backend --tail=200
docker compose logs nginx --tail=100
```

停止服务：

```bash
docker compose down
```

## 本地开发

### 后端本地运行

进入后端目录：

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

确保本地 MySQL 和 Redis 可用，并在 `backend/.env` 中配置：

```bash
DB_HOST=localhost
REDIS_HOST=localhost
```

执行数据库迁移：

```bash
alembic upgrade head
```

启动后端：

```bash
gunicorn -w 2 --timeout 1200 -b 0.0.0.0:5000 wsgi:app
```

或者开发调试：

```bash
python -m app.app
```

### 前端本地运行

进入前端目录：

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

开发服务器：

```text
http://localhost:5300
```

前端服务层默认使用 `/api/...`，Vite dev server 会将 API 代理到 Docker 入口或配置的后端地址。

## 常用 API

### 基础

| Method | Path | 说明 |
| --- | --- | --- |
| `GET` | `/api/health` | 健康检查 |

### 信息源

| Method | Path | 说明 |
| --- | --- | --- |
| `GET` | `/api/sources/` | 获取信息源列表 |
| `GET` | `/api/sources/{id}` | 获取单个信息源 |
| `POST` | `/api/sources/` | 新增信息源 |
| `PUT` | `/api/sources/{id}` | 更新信息源 |
| `DELETE` | `/api/sources/{id}` | 删除信息源 |

### 提示词

| Method | Path | 说明 |
| --- | --- | --- |
| `GET` | `/api/prompts/` | 获取提示词列表 |
| `GET` | `/api/prompts/defaults` | 获取默认提示词 |
| `GET` | `/api/prompts/defaults/{type}` | 获取指定类型默认提示词 |
| `POST` | `/api/prompts/` | 新增提示词 |
| `PUT` | `/api/prompts/{id}` | 更新提示词 |
| `DELETE` | `/api/prompts/{id}` | 删除提示词 |

### 卡片

| Method | Path | 说明 |
| --- | --- | --- |
| `GET` | `/api/cards/` | 获取保存的卡片 |
| `GET` | `/api/cards/{id}` | 获取单张卡片 |
| `GET` | `/api/cards/search?q=...` | 搜索卡片 |
| `GET` | `/api/cards/popular?limit=10` | 获取近期卡片 |
| `GET` | `/api/cards/stats` | 获取卡片统计 |
| `POST` | `/api/cards/create` | 创建卡片 |
| `PUT` | `/api/cards/{id}` | 更新卡片 |
| `DELETE` | `/api/cards/{id}` | 删除卡片 |

### 每日精读

| Method | Path | 说明 |
| --- | --- | --- |
| `POST` | `/api/daily-reading/generate` | 生成每日精读 |
| `POST` | `/api/daily-reading/generate-one-card` | 从单个 URL 生成卡片 |
| `POST` | `/api/daily-reading/generate-poster` | 从 URL 或缓存内容生成海报内容 |
| `GET` | `/api/daily-reading/history` | 查看历史生成结果 |
| `GET` | `/api/daily-reading/history/{filename}` | 查看某个历史结果 |
| `GET` | `/api/daily-reading/quota-status` | 查看 JigsawStack quota 状态 |

## 数据和持久化

默认 Docker Compose 使用宿主机目录持久化数据：

```text
/data/daily_intensive_reading/mysql
/data/daily_intensive_reading/redis
```

后端生成历史和日志在容器内：

```text
/app/output
/app/logs
```

本地开发时对应：

```text
backend/output
backend/logs
```

这些目录默认不应提交到 Git。

## 测试和验证

后端语法检查：

```bash
cd backend
python3 -m compileall app tests
```

后端缓存回归测试建议在 Docker 容器内运行，避免宿主机 Python 依赖差异：

```bash
docker compose exec -T backend python -m unittest tests.test_content_cache_ttl
```

前端检查：

```bash
cd frontend
npx tsc -b --noEmit
npm run lint
npm run build
```

完整 Docker 冒烟：

```bash
docker compose up -d --build --force-recreate
docker compose ps
curl -i -fsS http://localhost:20001/api/health
curl -i -fsS http://localhost:20001/api/sources/
curl -i -fsS http://localhost:20001/api/cards/
```

## 运维提示

### 重建并重启

```bash
docker compose up -d --build --force-recreate
```

### 查看后端日志

```bash
docker compose logs backend --tail=200
```

### 查看 Redis 缓存 TTL

```bash
docker compose exec -T backend python - <<'PY'
from app.services import content_cache
url = "https://example.com"
key = content_cache.get_url_cache_key(url)
print(key)
print(content_cache.redis_client.ttl(key))
PY
```

### 验证缓存命中

```bash
docker compose exec -T backend python - <<'PY'
from app.services import content_cache, scraper_service
url = "https://example.com/cache-check"
content_cache.cache_content(url, "cached content")
result = scraper_service.scrape_single_url(url)
print(result["success"])
print(result["results"][0]["provider"])
content_cache.delete_cached_content(url)
PY
```

期望输出包含：

```text
True
cache
```

## 安全注意事项

- 不要提交 `.env`、`backend/.env`、API key、数据库密码或私钥。
- `.env.example` 只能放占位符，不要放真实配置。
- 如果密钥曾经被提交到远端历史，必须到对应平台 revoke/rotate。
- `.claude/`、`frontend/dist/`、`node_modules/`、`backend/logs/`、`backend/output/` 都不应提交。
- Docker Compose 示例里使用的 `changeme` 和 `password` 只适合本地或测试环境，线上部署需要改成强密码。

## 目录说明

```text
.
├── docker-compose.yml          # 完整服务编排
├── nginx/nginx.conf            # 对外入口代理配置
├── backend/                    # Flask API
├── frontend/                   # React/Vite 前端
├── .env.example                # Compose 级配置示例
└── README.md                   # 项目总览文档
```

更多细节：

- [backend/README.md](backend/README.md)
- [frontend/README.md](frontend/README.md)
