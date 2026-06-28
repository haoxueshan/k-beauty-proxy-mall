# K-Beauty Proxy Mall

面向中文用户的 Olive Young 代购辅助平台。项目提供商品搜索、商品详情、购物车、订单提交、管理员订单管理，以及基于 Olive Young 页面抓取的商品数据能力。

GitHub Repository: <https://github.com/haoxueshan/k-beauty-proxy-mall>

## 项目简介

K-Beauty Proxy Mall 是一个基于 `Next.js + FastAPI + Supabase` 的全栈项目，目标是降低中文用户浏览和购买韩国 Olive Young 商品的门槛。

当前项目重点：

- 将 Olive Young 商品信息整理为中文展示
- 支持商品搜索、商品详情、购物车和订单流程
- 支持用户注册、登录、找回密码和个人订单查看
- 支持管理员登录、订单查看和状态更新
- 支持后端抓取 Olive Young 页面，并在抓取失败时使用兜底数据

## 技术栈

| 模块 | 技术 |
| --- | --- |
| Frontend | Next.js 14, React 18, TypeScript, Tailwind CSS |
| Backend | FastAPI, Uvicorn, Pydantic |
| Database | Supabase PostgreSQL |
| Crawler | Playwright, BeautifulSoup, httpx |
| Translation | 本地关键词词典 + 可选 OpenAI 翻译 |
| Deployment | Alibaba Cloud ECS, BaoTa Panel, Nginx, PM2 / Supervisor |

## 主要功能

- 商品搜索：中文关键词搜索 Olive Young 商品
- 商品展示：展示品牌、图片、规格、韩币价格和人民币参考价
- 商品详情：提供详情页、源站链接、加入购物车
- 购物车：支持添加、修改数量、删除商品
- 订单：从购物车提交订单，填写收货信息，查看个人订单
- 用户系统：注册、登录、当前用户查询、退出登录、找回密码
- 管理后台：管理员登录、订单列表、订单详情、订单状态管理
- 数据抓取：支持首页同步、搜索抓取、诊断接口和兜底推荐

## 项目结构

```text
k-beauty-proxy-mall/
├─ backend/                  # FastAPI 后端
│  ├─ crawler/               # Olive Young 抓取与解析
│  ├─ services/              # 认证、订单、翻译、价格服务
│  ├─ db/                    # Supabase 客户端
│  ├─ main.py                # API 入口
│  ├─ schemas.py             # Pydantic 数据模型
│  └─ requirements.txt
├─ frontend/                 # Next.js 前端
│  ├─ app/                   # App Router 页面
│  ├─ components/            # 复用组件
│  ├─ lib/                   # API、类型、辅助工具
│  └─ package.json
├─ db/                       # Schema 与迁移 SQL
├─ deploy/baota/             # 宝塔部署模板
└─ docs/                     # 项目文档
```

## 本地运行

### 后端

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

健康检查：

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/health/ready
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

前端地址：

```text
http://localhost:3000
```

## 环境变量

### `backend/.env`

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

APP_ENV=development
LOG_LEVEL=INFO
HOST=127.0.0.1
PORT=8000
PORT_AUTO_FALLBACK=true
UVICORN_RELOAD=true

ALLOWED_ORIGINS=*
TRUSTED_HOSTS=*

OPENAI_API_KEY=
OPENAI_TRANSLATION_MODEL=gpt-4o-mini
```

### `frontend/.env.local`

```env
NEXT_PUBLIC_API_BASE_URL=
API_PROXY_TARGET=http://127.0.0.1:8000
INTERNAL_API_BASE_URL=http://127.0.0.1:8000

NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=your_publishable_key
```

说明：

- 本地开发时，`INTERNAL_API_BASE_URL` 应指向 FastAPI 后端
- 同域部署时，`NEXT_PUBLIC_API_BASE_URL` 可以留空，浏览器会请求当前域名下的 `/api`
- 后端写入 Supabase 需要 `SUPABASE_SERVICE_ROLE_KEY`，不能用 publishable key 替代

## 数据库初始化

在 Supabase SQL Editor 中执行：

```text
db/schema.sql
```

如果项目已经使用过旧版本表结构，再按需执行：

```text
db/supabase_migration_auth.sql
db/supabase_migration_admin_orders_roles.sql
db/supabase_migration_admin.sql
```

主要表：

- `users`
- `auth_sessions`
- `cart_items`
- `orders`
- `order_items`

详细说明见 [docs/SUPABASE_SETUP.md](docs/SUPABASE_SETUP.md)。

## 常用 API

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/health` | 存活检查 |
| GET | `/health/ready` | 就绪检查 |
| POST | `/api/auth/register` | 用户注册 |
| POST | `/api/auth/login` | 用户登录 |
| GET | `/api/auth/me` | 获取当前用户 |
| POST | `/api/auth/logout` | 退出登录 |
| GET | `/api/oliveyoung/search?q=关键词` | 商品搜索 |
| POST | `/api/crawler/oliveyoung/sync` | 同步 Olive Young 数据 |
| GET | `/api/crawler/oliveyoung/diagnostics` | 抓取诊断 |
| POST | `/api/cart/items` | 添加购物车 |
| GET | `/api/cart/items/display` | 获取购物车展示数据 |
| PATCH | `/api/cart/items/{cart_item_id}` | 修改购物车商品 |
| DELETE | `/api/cart/items/{cart_item_id}` | 删除购物车商品 |
| POST | `/api/orders` | 创建订单 |
| GET | `/api/orders` | 获取当前用户订单 |
| GET | `/api/admin/orders` | 管理员订单列表 |
| PATCH | `/api/admin/orders/{order_id}` | 管理员更新订单 |

## 测试与构建

前端构建：

```bash
cd frontend
npm run build
```

后端测试：

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

## 部署

推荐部署方式：

- 前端：Next.js build 后使用 PM2 启动
- 后端：FastAPI 使用 Uvicorn，由 Supervisor 管理
- 反向代理：Nginx
- 数据库：Supabase

宝塔部署模板位于：

```text
deploy/baota/
```

详细文档：

- [docs/BAOTA_DEPLOY.md](docs/BAOTA_DEPLOY.md)
- [docs/BAOTA_RUNTIME_CHECKLIST.md](docs/BAOTA_RUNTIME_CHECKLIST.md)

## 截图

![Home Page](docs/screenshots/home.png)
![Search Page](docs/screenshots/search.png)
![Product Detail Page](docs/screenshots/detail.png)

## 已知限制

- Olive Young 页面可能存在反爬、Cloudflare 或动态加载限制，抓取结果受网络和访问环境影响
- 抓取失败或无结果时，前端会显示备用推荐，备用推荐不等于 Olive Young 实时搜索结果
- 人民币价格是参考价，最终价格、库存、规格和活动以下单前官方页面为准
- 后端对 Supabase 的写入当前依赖 service role key，生产环境需要妥善保管

## 使用的 AI 工具

| 工具 | 用途 |
| --- | --- |
| ChatGPT | 需求整理、方案分析、README 和文档整理 |
| Codex | 前后端代码修改、Bug 修复、结构分析、构建验证 |
