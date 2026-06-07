# BaoTa Runtime Checklist

Use this checklist when the site works locally but fails after uploading to Alibaba Cloud BaoTa.

## 1. Recommended Port Layout

- Frontend Next.js: `127.0.0.1:3000`
- Backend FastAPI: `127.0.0.1:8000`
- Public access: only `80` and `443`
- Nginx should proxy `/` to frontend and `/api/` to backend.

Do not expose `3000` or `8000` directly to the public internet.

## 2. Frontend API Address

For same-domain deployment, leave this empty before building:

```env
NEXT_PUBLIC_API_BASE_URL=
API_PROXY_TARGET=http://127.0.0.1:8000
INTERNAL_API_BASE_URL=http://127.0.0.1:8000
```

Then browser requests will use the current domain:

```text
https://your-domain.com/api/...
```

For separate API domain deployment, set this before `npm run build`:

```env
NEXT_PUBLIC_API_BASE_URL=https://api.your-domain.com
```

Important: `NEXT_PUBLIC_*` variables are baked into the frontend during `npm run build`.
If you changed them after building, run `npm run build` again and restart PM2.
`INTERNAL_API_BASE_URL` is used by Next.js server-side rendering and must be an absolute URL.

## 3. Backend Environment

Backend `.env` should include:

```env
HOST=127.0.0.1
PORT=8000
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=sb_secret_xxx
ALLOWED_ORIGINS=https://your-domain.com
OPENAI_API_KEY=sk-xxx
```

If Olive Young blocks the Alibaba Cloud outbound IP, add a proxy:

```env
CRAWLER_PROXY_SERVER=http://proxy.example.com:8080
CRAWLER_PROXY_USERNAME=
CRAWLER_PROXY_PASSWORD=
```

## 4. Playwright On Linux

Run these inside `backend/.venv`:

```bash
python -m playwright install --with-deps chromium
```

If BaoTa cannot install system dependencies automatically, run:

```bash
python -m playwright install-deps
python -m playwright install chromium
```

## 5. Smoke Tests On The Server

Run from the ECS server:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:3000
curl https://your-domain.com/health
curl "https://your-domain.com/api/oliveyoung/search?q=牙膏"
curl "https://your-domain.com/api/crawler/oliveyoung/diagnostics?keyword=牙膏"
```

Expected:

- `/health` returns `status: ok`.
- `/api/oliveyoung/search` returns `source` and `items`.
- `/api/crawler/oliveyoung/diagnostics` returns `ok: true` and `product_count > 0`.

If diagnostics returns `ok: false`, read `error` and `hints`. It is usually one of:

- Playwright Chromium is not installed.
- Linux system libraries are missing.
- The backend process user cannot access the Playwright browser cache.
- Alibaba Cloud outbound IP cannot access Olive Young reliably and needs a proxy.

## 6. Restart Order

After changing environment variables:

```bash
cd /www/wwwroot/k-beauty-proxy-mall/frontend
npm run build
pm2 restart k-beauty-frontend

supervisorctl restart k-beauty-backend
nginx -t
systemctl reload nginx
```
