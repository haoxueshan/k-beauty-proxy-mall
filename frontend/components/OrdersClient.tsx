"use client";

import { useEffect, useState } from "react";
import { AuthGate } from "@/components/AuthGate";
import { useAuth } from "@/components/AuthProvider";
import { OrderStatusBadge } from "@/components/OrderStatusBadge";
import { deleteOrder, getMyOrders } from "@/lib/api";
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

function MoneyRow({ label, value, emphasize = false }: { label: string; value: number; emphasize?: boolean }) {
  return (
    <div className="flex justify-between gap-4 text-sm">
      <span className="subtle">{label}</span>
      <span className={emphasize ? "font-semibold text-coral" : ""}>¥{value.toFixed(2)}</span>
    </div>
  );
}

export function OrdersClient() {
  const { token, isAuthenticated } = useAuth();
  const [orders, setOrders] = useState<Order[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [deletingId, setDeletingId] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated || !token) {
      setOrders([]);
      return;
    }

    setIsLoading(true);
    setError("");
    getMyOrders(token)
      .then((items) => {
        setOrders(items);
      })
      .catch((requestError) => {
        setError(requestError instanceof Error ? requestError.message : "订单加载失败");
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, [isAuthenticated, token]);

  async function handleDeleteOrder(order: Order) {
    if (!token) {
      return;
    }

    const confirmed = window.confirm(`确认删除订单 ${order.orderNo} 吗？删除后无法恢复。`);
    if (!confirmed) {
      return;
    }

    setError("");
    setDeletingId(order.id);
    try {
      await deleteOrder(token, order.id);
      setOrders((current) => current.filter((item) => item.id !== order.id));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "订单删除失败");
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <AuthGate title="登录后查看订单" description="注册或登录后，才能查看你的商品订单、报价状态和物流进度。">
      {isLoading ? (
        <div className="panel p-8">
          <p className="text-lg font-semibold">正在加载订单…</p>
        </div>
      ) : error && orders.length === 0 ? (
        <div className="panel p-8">
          <p className="text-lg font-semibold">订单读取失败</p>
          <p className="subtle mt-2">{error}</p>
        </div>
      ) : orders.length === 0 ? (
        <div className="panel p-8">
          <p className="text-lg font-semibold">你还没有订单</p>
          <p className="subtle mt-2">完成商品加购并提交订单后，订单会出现在这里。</p>
        </div>
      ) : (
        <section className="mt-8 space-y-5">
          {error ? <p className="rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p> : null}
          {orders.map((order) => (
            <article key={order.id} className="panel p-6">
              <div className="flex flex-col gap-4 border-b border-black/10 pb-5 md:flex-row md:items-start md:justify-between">
                <div className="space-y-2">
                  <p className="text-lg font-semibold">{order.orderNo}</p>
                  <p className="text-sm subtle">创建时间：{formatDateTime(order.createdAt)}</p>
                  <div className="space-y-1 text-sm">
                    <p>收件人：{order.receiverName}</p>
                    {order.receiverPhone ? <p>联系电话：{order.receiverPhone}</p> : null}
                    {order.receiverAddress ? <p className="subtle">收货地址：{order.receiverAddress}</p> : null}
                  </div>
                </div>
                <div className="flex flex-col items-start gap-3 md:items-end">
                  <OrderStatusBadge status={order.status} />
                  <span className="text-xl font-bold text-coral">¥{order.totalAmountCny.toFixed(2)}</span>
                  <p className="text-sm subtle">已支付：¥{order.paidAmountCny.toFixed(2)}</p>
                  <button
                    type="button"
                    className="rounded-full border border-red-200 bg-red-50 px-4 py-2 text-sm font-semibold text-red-700 transition hover:bg-red-100 disabled:cursor-not-allowed disabled:opacity-60"
                    onClick={() => handleDeleteOrder(order)}
                    disabled={deletingId === order.id}
                  >
                    {deletingId === order.id ? "删除中..." : "删除订单"}
                  </button>
                </div>
              </div>

              <div className="mt-5 grid gap-6 lg:grid-cols-[1.4fr_0.9fr]">
                <div>
                  <h3 className="text-base font-semibold">商品清单</h3>
                  {order.items.length === 0 ? (
                    <p className="subtle mt-3 text-sm">当前订单还没有可展示的商品明细。</p>
                  ) : (
                    <div className="mt-3 space-y-3">
                      {order.items.map((item) => (
                        <div key={item.id} className="rounded-2xl border border-black/10 bg-white/60 p-4">
                          <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
                            <div>
                              <p className="font-semibold">{item.titleZh}</p>
                              <p className="subtle text-sm">{item.titleKo}</p>
                              <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-sm">
                                <span>数量：{item.quantity}</span>
                                <span>人民币参考单价：¥{item.unitPriceCny.toFixed(2)}</span>
                                <span>规格：{item.selectedOption || "默认规格"}</span>
                              </div>
                            </div>
                            <div className="text-sm font-semibold text-coral">小计 ¥{item.subtotalCny.toFixed(2)}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div className="space-y-4">
                  <div className="rounded-2xl border border-black/10 bg-white/60 p-4">
                    <h3 className="text-base font-semibold">金额明细</h3>
                    <div className="mt-3 space-y-2">
                      <MoneyRow label="商品参考金额" value={order.productTotalCny} />
                      <MoneyRow label="服务费" value={order.serviceFeeCny} />
                      <MoneyRow label="国际运费" value={order.internationalShippingFeeCny} />
                      <MoneyRow label="包装费" value={order.packageFeeCny} />
                      <div className="border-t border-black/10 pt-2">
                        <MoneyRow label="订单总额" value={order.totalAmountCny} emphasize />
                      </div>
                    </div>
                  </div>

                  {order.userNote ? (
                    <div className="rounded-2xl border border-black/10 bg-white/60 p-4">
                      <h3 className="text-base font-semibold">下单备注</h3>
                      <p className="subtle mt-2 text-sm leading-6">{order.userNote}</p>
                    </div>
                  ) : null}

                  {order.adminNote ? (
                    <div className="rounded-2xl border border-black/10 bg-white/60 p-4">
                      <h3 className="text-base font-semibold">客服备注</h3>
                      <p className="subtle mt-2 text-sm leading-6">{order.adminNote}</p>
                    </div>
                  ) : null}
                </div>
              </div>
            </article>
          ))}
        </section>
      )}
    </AuthGate>
  );
}
