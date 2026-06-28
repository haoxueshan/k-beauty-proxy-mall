# Olive Young 中文代购平台 PRD 摘要

## 产品定位

这是一个面向中文用户的 Olive Young 商品代购辅助平台。平台通过抓取公开商品数据、整理中文信息和订单流程，帮助用户完成搜索、浏览、加购、下单和订单跟踪。

## 核心价值

- 降低中文用户理解韩文商品页面的门槛
- 提供中文商品信息和人民币参考价格
- 将代购、报价、采购、物流、售后流程平台化

## 用户角色

- 普通用户：搜索商品、加入购物车、提交订单、查看订单进度
- 管理员：管理订单、处理报价、更新状态、跟进物流
- 代购运营：查看待处理订单、录入采购信息、维护订单进度

## MVP 功能范围

### 用户侧

- 中文关键词搜索 Olive Young 商品
- 商品列表页
- 商品详情页
- 购物车
- 订单提交
- 订单状态查看

### 管理后台

- 订单列表与订单详情
- 订单状态更新
- 管理员登录与权限控制
- 抓取任务触发与诊断

### 数据侧

- Olive Young 搜索结果抓取
- 商品详情抓取
- 中文映射与翻译
- 价格换算与代购报价计算
- 商品缓存与兜底推荐

## 非目标

- 不接入 Olive Young 官方账号体系
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

## 当前实现说明

当前仓库已经提供：

- 前端页面与核心交互骨架
- FastAPI 后端接口
- Olive Young 抓取与缓存逻辑
- Supabase 表结构与迁移脚本
- 用户认证、购物车、订单、管理员订单处理流程

后续扩展重点：

- 提升抓取稳定性和字段覆盖率
- 完善管理员报价与采购流程
- 完善物流、售后和异常单处理流程
