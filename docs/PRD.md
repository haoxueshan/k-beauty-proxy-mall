# Olive Young 中文代购平台 PRD 摘要

## 产品定位

这是一个面向中国用户的 Olive Young 商品中文代购平台。平台通过抓取公开商品数据，沉淀中文商品库，并支持用户完成搜索、加购、提交代购订单、查看订单进度等流程。

## 核心价值

- 降低韩文页面的理解门槛
- 提供中文商品信息和人民币参考价
- 将代购、报价、采购、物流、售后流程平台化

## 用户角色

- 普通用户：搜索商品、加入购物车、提交订单、查看进度
- 平台管理员：管理商品、订单、报价、物流、抓取任务
- 代购员：查看待采购订单、录入采购信息、上传凭证、更新状态

## MVP 功能范围

### 用户侧

- 中文关键词搜索 Olive Young 商品
- 商品列表页
- 商品详情页
- 平台代购购物车
- 代购订单提交
- 订单状态查看

### 管理后台

- 商品数据查看
- 抓取任务触发与日志查看
- 订单报价和状态更新
- 采购凭证上传入口
- 国际物流信息录入入口

### 数据侧

- Olive Young 商品搜索抓取
- 商品详情抓取
- 中文映射与翻译
- 价格换算和代购报价计算
- 商品数据缓存与去重

## 非目标

- 不接入 Olive Young 官方账号
- 不保存用户 Olive Young 账号密码
- 不直接控制 Olive Young 官方购物车
- 不做自动下单和自动支付
- 不绕过登录、验证码、风控或访问限制

## 关键数据模型

- `products`
- `search_logs`
- `cart_items`
- `orders`
- `order_items`
- `purchase_records`
- `logistics`
- `crawler_tasks`

## 推荐技术栈

- Frontend: Next.js, TypeScript, Tailwind CSS
- Backend: FastAPI, Playwright, BeautifulSoup
- Data: Supabase PostgreSQL, Supabase Storage

## 当前脚手架实现说明

本仓库首版先提供页面与 API 骨架、示例数据、数据库 schema 和价格计算逻辑，方便后续继续接入真实抓取、Supabase、登录鉴权和后台工作流。
