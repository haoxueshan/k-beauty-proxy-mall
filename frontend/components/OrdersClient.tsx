"use client";

import { useEffect, useState } from "react";
import { AuthGate } from "@/components/AuthGate";
import { OrderStatusBadge } from "@/components/OrderStatusBadge";
import { useAuth } from "@/components/AuthProvider";
import { getMyOrders } from "@/lib/api";
import type { Order } from "@/lib/mock-data";

export function OrdersClient() {
  const { token, isAuthenticated } = useAuth();
  const [orders, setOrders] = useState<Order[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

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

  return (
    <AuthGate title="登录后查看订单" description="注册或登录后，才能查看你的代购订单、报价状态和物流进度。">
      {isLoading ? (
        <div className="panel p-8">
          <p className="text-lg font-semibold">正在加载订单…</p>
        </div>
      ) : error ? (
        <div className="panel p-8">
          <p className="text-lg font-semibold">订单读取失败</p>
          <p className="subtle mt-2">{error}</p>
        </div>
      ) : orders.length === 0 ? (
        <div className="panel p-8">
          <p className="text-lg font-semibold">你还没有订单</p>
          <p className="subtle mt-2">完成商品加购并提交代购单后，订单会出现在这里。</p>
        </div>
      ) : (
        <section className="mt-8 space-y-4">
          {orders.map((order) => (
            <article key={order.id} className="panel p-6">
              <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                <div>
                  <p className="text-lg font-semibold">{order.orderNo}</p>
                  <p className="subtle mt-1 text-sm">
                    收件人：{order.receiverName} · 创建时间：{order.createdAt}
                  </p>
                </div>
                <div className="flex items-center gap-4">
                  <OrderStatusBadge status={order.status} />
                  <span className="text-lg font-bold text-coral">¥{order.totalAmountCny.toFixed(2)}</span>
                </div>
              </div>
            </article>
          ))}
        </section>
      )}
    </AuthGate>
  );
}
