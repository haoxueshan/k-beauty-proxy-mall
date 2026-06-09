# 宝塔部署说明（阿里云 ECS）

这份文档对应当前仓库的标准上线方案：`Next.js 前端 + FastAPI 后端 + Supabase + 宝塔 Nginx 反代`。

推荐标准方案：

- 单域名站点：`https://mall.example.com`
- `Nginx` 将 `/` 转发到前端
- `Nginx` 将 `/api`、`/health`、`/health/ready` 转发到后端

项目仍支持前后端分离域名，但标准化上线建议优先使用同域部署，配置更简单，跨域也更少。

## 1. 服务器建议

阿里云 ECS 建议：

- 系统：`Ubuntu 22.04 LTS`
- 配置：至少 `2C2G`
- 带宽：至少 `3Mbps`

宝塔面板建议安装：

- `Nginx`
- `Node.js` 版本管理器
- `Python 项目管理器` 或 `Supervisor 管理器`
- `PM2 管理器`

仓库里已附带宝塔模板文件目录：

```bash
deploy/baota/
```

包含：

- `frontend.ecosystem.config.js`
- `backend.supervisor.conf`
- `nginx.single-domain.conf`
- `nginx.mall.example.com.conf`
- `nginx.api.example.com.conf`
- `bootstrap.sh`
- `smoke-test.sh`

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

标准同域部署时，在 `frontend/.env.local` 中填写：

```env
NEXT_PUBLIC_API_BASE_URL=
API_PROXY_TARGET=http://127.0.0.1:8000
INTERNAL_API_BASE_URL=http://127.0.0.1:8000
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=sb_publishable_xxx
```

重点：

- `NEXT_PUBLIC_API_BASE_URL` 留空时，浏览器会走当前域名下的 `/api`
- `INTERNAL_API_BASE_URL` 供 Next.js 服务端渲染调用后端，必须是绝对地址
- 变更 `NEXT_PUBLIC_*` 变量后，必须重新执行 `npm run build`

如果你坚持使用独立 API 域名，再把 `NEXT_PUBLIC_API_BASE_URL` 改成：

```env
NEXT_PUBLIC_API_BASE_URL=https://api.example.com
```

## 4. 后端环境变量

在 `backend/.env` 中填写：

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=sb_secret_xxx
ALLOWED_ORIGINS=https://mall.example.com,https://www.mall.example.com
TRUSTED_HOSTS=mall.example.com,www.mall.example.com
OPENAI_API_KEY=sk-xxx
APP_ENV=production
LOG_LEVEL=INFO
HOST=127.0.0.1
PORT=8000
PORT_AUTO_FALLBACK=false
UVICORN_RELOAD=false
```

说明：

- `SUPABASE_SERVICE_ROLE_KEY` 必须是真正的服务端密钥，不能用 publishable key
- `ALLOWED_ORIGINS` 支持多个域名，逗号分隔
- `TRUSTED_HOSTS` 用于限制后端接受的 Host 头，线上建议显式填写
- `PORT_AUTO_FALLBACK` 线上保持 `false`，避免端口被占时悄悄切到别的端口
- `UVICORN_RELOAD` 线上保持 `false`

如果你只是临时联调，也可以用：

```env
ALLOWED_ORIGINS=*
TRUSTED_HOSTS=*
PORT_AUTO_FALLBACK=true
```

但不建议在线上长期使用。

## 5. 初始化数据库

数据库不要部署在宝塔本机，继续用 `Supabase` 即可。

上线前在 Supabase 控制台执行：

- `db/schema.sql`
- 如果是从旧版本升级，再执行 `db/supabase_migration_auth.sql`
- 如果需要管理员字段迁移，再执行 `db/supabase_migration_admin.sql`

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

### 方式 A：宝塔 PM2 管理器

标准启动命令：

```bash
npm run start:prod
```

如果使用仓库自带 PM2 配置，执行：

```bash
cd /www/wwwroot/k-beauty-proxy-mall
pm2 start deploy/baota/frontend.ecosystem.config.js
pm2 save
```

### 方式 B：宝塔 Node 项目

如果你使用宝塔的 Node 项目功能：

- 项目目录：`/www/wwwroot/k-beauty-proxy-mall/frontend`
- 启动命令：`npm run start:prod`
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

如果你要在服务器上跑测试，再额外执行：

```bash
pip install -r requirements-dev.txt
```

启动命令建议：

```bash
.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
```

### 方式 A：宝塔 Python 项目

- 项目目录：`/www/wwwroot/k-beauty-proxy-mall/backend`
- 启动命令：`.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000`

### 方式 B：Supervisor

可直接参考：

```bash
deploy/baota/backend.supervisor.conf
```

## 8. Playwright 额外依赖

后端依赖里包含 `playwright`。如果线上爬虫功能要真正运行，部署后还要补浏览器依赖。

建议执行：

```bash
python -m playwright install --with-deps chromium
```

如果失败，再尝试：

```bash
python -m playwright install chromium
python -m playwright install-deps
```

## 9. Nginx 反向代理

### 标准单域名配置

更推荐直接使用：

```bash
deploy/baota/nginx.single-domain.conf
```

这样：

- `/` 走 Next.js 前端
- `/api/*` 走 FastAPI
- `/health` 和 `/health/ready` 直接走后端

### 独立前后端域名配置

如果你坚持分两个域名，可参考：

- `deploy/baota/nginx.mall.example.com.conf`
- `deploy/baota/nginx.api.example.com.conf`

## 10. HTTPS 与安全组

上线时记得：

- 宝塔里申请 SSL
- 阿里云安全组放行 `80` 和 `443`

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
5. 后端能访问 `http://127.0.0.1:8000/health/ready`
6. 前端能访问 `http://127.0.0.1:3000`
7. Nginx 反代后，`https://mall.example.com/health` 正常
8. 执行 `deploy/baota/smoke-test.sh mall.example.com`
9. 首页、搜索、登录、购物车、下单流程逐步测试

## 12. 当前项目的部署建议

结合当前代码，最稳妥的方案是：

- 前端和后端分开跑
- Supabase 继续用云服务
- 宝塔只负责进程守护、Nginx、SSL、日志管理

第一版不建议把数据库、对象存储、爬虫调度都堆到同一台 ECS 上，先把 Web 服务跑稳更重要。
