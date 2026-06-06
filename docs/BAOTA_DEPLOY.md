# 宝塔部署说明（阿里云 ECS）

本项目适合部署成下面这套结构：

- `frontend/`：`Next.js 14`，用 Node.js 常驻运行
- `backend/`：`FastAPI`，用 `uvicorn` 常驻运行
- 数据库：继续使用 `Supabase` 云数据库
- 网关：宝塔 `Nginx` 反向代理

推荐域名规划：

- 前台站点：`https://mall.example.com`
- API 域名：`https://api.example.com`

如果暂时只有一个域名，也可以把前端挂在 `/`，后端反代到 `/api`，但当前项目前端使用 `NEXT_PUBLIC_API_BASE_URL`，独立二级域名会更省心。

## 1. 服务器建议

阿里云 ECS 建议：

- 系统：`Ubuntu 22.04 LTS`
- 配置：至少 `2C2G`
- 带宽：至少 `3Mbps`

宝塔面板建议安装：

- `Nginx`
- `Node.js` 版本管理器
- `Python 项目管理器` 或 `Supervisor 管理器`
- `PM2 管理器`（如果你想用 PM2 跑前端）

## 2. 代码目录建议

建议在宝塔服务器上放到：

```bash
/www/wwwroot/k-beauty-proxy-mall
```

目录结构保持仓库原样：

```bash
/www/wwwroot/k-beauty-proxy-mall/frontend
/www/wwwroot/k-beauty-proxy-mall/backend
```

## 3. 前端环境变量

在 `frontend/.env.local` 中填写生产值：

```env
NEXT_PUBLIC_API_BASE_URL=https://api.example.com
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=sb_publishable_xxx
```

重点：

- `NEXT_PUBLIC_API_BASE_URL` 不要再写 `127.0.0.1`
- 必须写成你线上 API 域名

## 4. 后端环境变量

在 `backend/.env` 中填写：

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=sb_secret_xxx
ALLOWED_ORIGINS=https://mall.example.com
OPENAI_API_KEY=sk-xxx
```

说明：

- `SUPABASE_SERVICE_ROLE_KEY` 必须是真正的服务端密钥，不能用 publishable key
- `ALLOWED_ORIGINS` 支持多个域名，逗号分隔
- 示例：

```env
ALLOWED_ORIGINS=https://mall.example.com,https://www.mall.example.com
```

如果你只是临时联调，也可以用：

```env
ALLOWED_ORIGINS=*
```

但不建议在线上长期使用。

## 5. 初始化数据库

数据库不要部署在宝塔本机，继续用 `Supabase` 即可。

上线前在 Supabase 控制台执行：

- `db/schema.sql`
- 如果是从旧版本升级，再执行 `db/supabase_migration_auth.sql`

## 6. 部署前端（Next.js）

先进入前端目录：

```bash
cd /www/wwwroot/k-beauty-proxy-mall/frontend
```

安装依赖并构建：

```bash
npm install
npm run build
```

启动方式二选一。

### 方式 A：宝塔 PM2 管理器

启动命令：

```bash
npm run start -- --hostname 127.0.0.1 --port 3000
```

或者直接：

```bash
node node_modules/next/dist/bin/next start --hostname 127.0.0.1 --port 3000
```

建议：

- 监听 `127.0.0.1:3000`
- 由 `Nginx` 反代对外提供服务

### 方式 B：宝塔 Node 项目

如果你使用宝塔的 Node 项目功能：

- 项目目录：`/www/wwwroot/k-beauty-proxy-mall/frontend`
- 启动命令：`npm run start -- --hostname 127.0.0.1 --port 3000`
- 端口：`3000`

注意：务必先执行过 `npm run build`。

## 7. 部署后端（FastAPI）

进入后端目录：

```bash
cd /www/wwwroot/k-beauty-proxy-mall/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

启动命令建议：

```bash
.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
```

### 方式 A：宝塔 Python 项目

如果你使用宝塔 Python 项目管理：

- 项目目录：`/www/wwwroot/k-beauty-proxy-mall/backend`
- 启动命令：`.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000`
- Python 解释器：项目虚拟环境中的 Python

### 方式 B：Supervisor

Supervisor 启动命令可以写成：

```bash
/www/wwwroot/k-beauty-proxy-mall/backend/.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
```

工作目录：

```bash
/www/wwwroot/k-beauty-proxy-mall/backend
```

## 8. Playwright 额外依赖

后端依赖里包含 `playwright`。如果线上爬虫功能要真正运行，部署后还要补浏览器依赖。

在后端虚拟环境中执行：

```bash
playwright install
```

如果安装失败，再执行：

```bash
python -m playwright install
```

如果服务器缺少系统库，Ubuntu 上通常还需要：

```bash
python -m playwright install-deps
```

如果你暂时只想先把站点跑起来，不立刻启用爬虫，至少要确认相关接口失败时不会影响首页核心流程。

## 9. Nginx 反向代理

### 前端站点 `mall.example.com`

宝塔网站中创建站点后，反代到：

```nginx
location / {
    proxy_pass http://127.0.0.1:3000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

### API 站点 `api.example.com`

反代到：

```nginx
location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

健康检查地址：

```text
https://api.example.com/health
```

返回 `status=ok` 就说明 API 正常。

## 10. HTTPS 与安全组

上线时记得：

- 宝塔里给两个域名都申请 SSL
- 阿里云安全组放行：
- `80`
- `443`

不建议直接对公网开放：

- `3000`
- `8000`

这两个端口只监听本机 `127.0.0.1` 即可。

## 11. 首次上线检查顺序

建议按这个顺序验收：

1. Supabase SQL 已执行完成
2. 后端 `.env` 已配置完成
3. 前端 `.env.local` 已配置完成
4. 后端能访问 `http://127.0.0.1:8000/health`
5. 前端能访问 `http://127.0.0.1:3000`
6. Nginx 反代后，`https://api.example.com/health` 正常
7. 首页、搜索、登录、购物车、下单流程逐步测试

## 12. 当前项目的部署建议

结合当前代码，最稳妥的方案是：

- 前端和后端分开跑
- Supabase 继续用云服务
- 宝塔只负责：
- 进程守护
- Nginx 反代
- SSL
- 日志管理

不建议第一版就把数据库、对象存储、爬虫调度都堆到同一台 ECS 上，先把 Web 服务跑稳更重要。
