# Supabase Setup

## 1. 创建项目

创建 Supabase 云项目，并准备以下配置项：

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`

## 2. 配置后端环境变量

将 [backend/.env.example](C:/Users/Administrator/Desktop/demo/k-beauty-proxy-mall/backend/.env.example) 复制为 `backend/.env`，并填写项目配置。

后端至少需要：

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`

说明：

- 后端也支持把 `NEXT_PUBLIC_SUPABASE_URL` 作为 URL 兜底值
- 服务端写入仍然必须使用 `SUPABASE_SERVICE_ROLE_KEY`
- 不要把 `sb_publishable_` 开头的 key 填到 `SUPABASE_SERVICE_ROLE_KEY`

## 3. 配置前端环境变量

将 [frontend/.env.local.example](C:/Users/Administrator/Desktop/demo/k-beauty-proxy-mall/frontend/.env.local.example) 复制为 `frontend/.env.local`。

前端常用配置：

- `NEXT_PUBLIC_API_BASE_URL`
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`

## 4. 执行数据库结构

在 Supabase SQL Editor 中执行：

- [db/schema.sql](C:/Users/Administrator/Desktop/demo/k-beauty-proxy-mall/db/schema.sql)

如果项目已经使用过旧版本表结构，再按需执行以下迁移：

- [db/supabase_migration_auth.sql](C:/Users/Administrator/Desktop/demo/k-beauty-proxy-mall/db/supabase_migration_auth.sql)
- [db/supabase_migration_admin_orders_roles.sql](C:/Users/Administrator/Desktop/demo/k-beauty-proxy-mall/db/supabase_migration_admin_orders_roles.sql)

## 5. 当前由 Supabase 托管的数据表

当前后端已将以下核心流程落到 Supabase：

- `users`
- `auth_sessions`
- `cart_items`
- `orders`
- `order_items`

## 6. 当前实现范围

- 商品搜索和商品详情使用后端抓取结果
- 支持首页同步、实时搜索和兜底推荐
- 用户认证、购物车写入和订单持久化已经接入 Supabase
- 当前服务端写入仍依赖 service role key，后续如要改为纯前端受限访问，需要重新设计 RLS 策略
