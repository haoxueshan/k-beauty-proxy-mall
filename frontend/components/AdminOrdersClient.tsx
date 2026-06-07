"use client";

import { useEffect, useState } from "react";
import { AuthGate } from "@/components/AuthGate";
import { useAuth } from "@/components/AuthProvider";
import { OrderStatusBadge } from "@/components/OrderStatusBadge";
import { getAdminOrders } from "@/lib/api";
import type { Order } from "@/lib/mock-data";

function formatDateTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  }).format(date);
}

function formatMoney(value: number) {
  return `¥${value.toFixed(2)}`;
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-3xl border border-black/10 bg-white/70 p-4">
      <p className="subtle text-sm">{label}</p>
      <p className="mt-2 text-2xl font-semibold">{value}</p>
    </div>
  );
}

function DetailBlock({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-2xl border border-black/10 bg-white/60 p-4 text-sm leading-7">
      <p className="font-semibold">{title}</p>
      <div className="mt-2">{children}</div>
    </div>
  );
}

export function AdminOrdersClient() {
  const { token, isAuthenticated } = useAuth();
  const [orders, setOrders] = useState<Order[]>([]);
  const [expandedOrderIds, setExpandedOrderIds] = useState<Set<string>>(new Set());
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!isAuthenticated || !token) {
      setOrders([]);
      setExpandedOrderIds(new Set());
      return;
    }

    setIsLoading(true);
    setError("");
    getAdminOrders(token)
      .then((items) => {
        setOrders(items);
        setExpandedOrderIds(new Set());
      })
      .catch((requestError) => {
        setError(requestError instanceof Error ? requestError.message : "后台订单加载失败");
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, [isAuthenticated, token]);

  const summary = orders.reduce(
    (current, order) => ({
      totalAmount: current.totalAmount + order.totalAmountCny,
      paidAmount: current.paidAmount + order.paidAmountCny,
      pendingCount: current.pendingCount + (order.status === "pending_quote" ? 1 : 0)
    }),
    { totalAmount: 0, paidAmount: 0, pendingCount: 0 }
  );

  function toggleOrder(orderId: string) {
    setExpandedOrderIds((current) => {
      const next = new Set(current);
      if (next.has(orderId)) {
        next.delete(orderId);
      } else {
        next.add(orderId);
      }
      return next;
    });
  }

  function expandAllOrders() {
    setExpandedOrderIds(new Set(orders.map((order) => order.id)));
  }

  function collapseAllOrders() {
    setExpandedOrderIds(new Set());
  }

  return (
    <AuthGate title="登录后查看后台订单" description="后台订单会展示平台内所有用户提交的代购订单。">
      {isLoading ? (
        <div className="panel mt-8 flex items-center gap-3 p-8">
          <span className="mini-spinner" aria-hidden="true" />
          <div>
            <p className="text-lg font-semibold">正在加载全平台订单...</p>
            <p className="subtle mt-1 text-sm">正在从后端同步读取所有用户的订单数据。</p>
          </div>
        </div>
      ) : error && orders.length === 0 ? (
        <div className="panel mt-8 p-8">
          <p className="text-lg font-semibold">后台订单读取失败</p>
          <p className="subtle mt-2">{error}</p>
        </div>
      ) : (
        <section className="mt-8 space-y-6">
          {error ? <p className="rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p> : null}

          <div className="grid gap-4 md:grid-cols-4">
            <StatCard label="订单数量" value={`${orders.length} 单`} />
            <StatCard label="待报价" value={`${summary.pendingCount} 单`} />
            <StatCard label="订单总额" value={formatMoney(summary.totalAmount)} />
            <StatCard label="已支付" value={formatMoney(summary.paidAmount)} />
          </div>

          {orders.length === 0 ? (
            <div className="panel p-8">
              <p className="text-lg font-semibold">当前还没有用户订单</p>
              <p className="subtle mt-2">用户从购物车提交代购单后，会自动出现在这个后台列表里。</p>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <p className="subtle text-sm">订单默认折叠显示，点击任意订单可展开查看完整信息。</p>
                <div className="flex flex-wrap gap-2">
                  <button className="cta ghost px-4 py-2 text-sm" type="button" onClick={expandAllOrders}>
                    全部展开
                  </button>
                  <button className="cta ghost px-4 py-2 text-sm" type="button" onClick={collapseAllOrders}>
                    全部折叠
                  </button>
                </div>
              </div>

              {orders.map((order) => {
                const buyer = order.userName || order.userEmail || order.userId || "未知用户";
                const isExpanded = expandedOrderIds.has(order.id);
                const detailsId = `admin-order-details-${order.id}`;

                return (
                  <article key={order.id} className="panel overflow-hidden p-0">
                    <button
                      type="button"
                      className="w-full p-6 text-left transition hover:bg-white/40"
                      aria-expanded={isExpanded}
                      aria-controls={detailsId}
                      onClick={() => toggleOrder(order.id)}
                    >
                      <div className="grid gap-4 lg:grid-cols-[1fr_0.7fr_0.55fr_auto] lg:items-center">
                        <div className="space-y-2">
                          <div className="flex flex-wrap items-center gap-3">
                            <p className="text-xl font-semibold">{order.orderNo}</p>
                            <OrderStatusBadge status={order.status} />
                          </div>
                          <p className="subtle text-sm">创建时间：{formatDateTime(order.createdAt)}</p>
                        </div>

                        <div className="text-sm leading-6">
                          <p className="font-semibold">下单用户：{buyer}</p>
                          <p className="subtle">收件人：{order.receiverName}</p>
                        </div>

                        <div className="text-sm leading-6 lg:text-right">
                          <p className="text-xl font-bold text-coral">{formatMoney(order.totalAmountCny)}</p>
                          <p className="subtle">商品：{order.items.length} 种</p>
                        </div>

                        <span className="inline-flex items-center justify-center rounded-full border border-black/10 bg-white/80 px-4 py-2 text-sm font-semibold">
                          {isExpanded ? "收起详情" : "展开详情"}
                        </span>
                      </div>
                    </button>

                    {isExpanded ? (
                      <div id={detailsId} className="border-t border-black/10 p-6">
                        <div className="grid gap-4 lg:grid-cols-[1fr_1fr_0.8fr]">
                          <DetailBlock title="下单用户">
                            <p>{buyer}</p>
                            {order.userEmail ? <p>邮箱：{order.userEmail}</p> : null}
                            {order.userPhone ? <p>用户手机：{order.userPhone}</p> : null}
                            {order.userId ? <p className="subtle">用户 ID：{order.userId}</p> : null}
                          </DetailBlock>

                          <DetailBlock title="收货信息">
                            <p>收件人：{order.receiverName}</p>
                            {order.receiverPhone ? <p>联系电话：{order.receiverPhone}</p> : null}
                            {order.receiverAddress ? <p>收货地址：{order.receiverAddress}</p> : null}
                            {order.userNote ? <p className="subtle mt-2">用户备注：{order.userNote}</p> : null}
                          </DetailBlock>

                          <DetailBlock title="金额明细">
                            <p>商品金额：{formatMoney(order.productTotalCny)}</p>
                            <p>服务费：{formatMoney(order.serviceFeeCny)}</p>
                            <p>国际运费：{formatMoney(order.internationalShippingFeeCny)}</p>
                            <p>包装费：{formatMoney(order.packageFeeCny)}</p>
                            <p className="mt-2 font-semibold text-coral">订单总额：{formatMoney(order.totalAmountCny)}</p>
                            <p className="subtle">已支付：{formatMoney(order.paidAmountCny)}</p>
                          </DetailBlock>
                        </div>

                        <div className="mt-5">
                          <p className="font-semibold">商品清单</p>
                          {order.items.length === 0 ? (
                            <p className="subtle mt-2 text-sm">这个订单暂时没有商品明细。</p>
                          ) : (
                            <div className="mt-3 grid gap-3 md:grid-cols-2">
                              {order.items.map((item) => (
                                <div key={item.id} className="rounded-2xl border border-black/10 bg-white/60 p-4">
                                  <p className="font-semibold">{item.titleZh}</p>
                                  <p className="subtle mt-1 text-sm">{item.titleKo}</p>
                                  <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-sm">
                                    <span>数量：{item.quantity}</span>
                                    <span>单价：{formatMoney(item.unitPriceCny)}</span>
                                    <span>小计：{formatMoney(item.subtotalCny)}</span>
                                    <span>规格：{item.selectedOption || "默认规格"}</span>
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    ) : null}
                  </article>
                );
              })}
            </div>
          )}
        </section>
      )}
    </AuthGate>
  );
}
