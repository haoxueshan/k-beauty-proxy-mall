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
      <span className={emphasize ? "font-semibold text-coral" : ""}>CNY {value.toFixed(2)}</span>
    </div>
  );
}

export function OrdersClient() {
  const { token, isAuthenticated } = useAuth();
  const [orders, setOrders] = useState<Order[]>([]);
  const [expandedOrderId, setExpandedOrderId] = useState<string | null>(null);
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
      .then(setOrders)
      .catch((requestError) => {
        setError(requestError instanceof Error ? requestError.message : "Order loading failed");
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, [isAuthenticated, token]);

  async function handleDeleteOrder(order: Order) {
    if (!token) {
      return;
    }

    const confirmed = window.confirm(`Delete order ${order.orderNo}? This cannot be undone.`);
    if (!confirmed) {
      return;
    }

    setError("");
    setDeletingId(order.id);
    try {
      await deleteOrder(token, order.id);
      setOrders((current) => current.filter((item) => item.id !== order.id));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Order deletion failed");
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <AuthGate title="Login required" description="Log in to view order details, quotes, and logistics status.">
      {isLoading ? (
        <div className="panel p-8">
          <p className="text-lg font-semibold">Loading orders...</p>
        </div>
      ) : error && orders.length === 0 ? (
        <div className="panel p-8">
          <p className="text-lg font-semibold">Order loading failed</p>
          <p className="subtle mt-2">{error}</p>
        </div>
      ) : orders.length === 0 ? (
        <div className="panel p-8">
          <p className="text-lg font-semibold">No orders yet</p>
          <p className="subtle mt-2">Submitted cart orders will appear here.</p>
        </div>
      ) : (
        <section className="mt-8 space-y-5">
          {error ? <p className="rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p> : null}
          {orders.map((order) => {
            const isExpanded = expandedOrderId === order.id;
            return (
              <article key={order.id} className="panel p-6">
                <div className="flex flex-col gap-4 border-b border-black/10 pb-5 md:flex-row md:items-start md:justify-between">
                  <div className="space-y-2">
                    <p className="text-lg font-semibold">{order.orderNo}</p>
                    <p className="text-sm subtle">Created: {formatDateTime(order.createdAt)}</p>
                    <div className="space-y-1 text-sm">
                      <p>Receiver: {order.receiverName}</p>
                      {order.receiverPhone ? <p>Phone: {order.receiverPhone}</p> : null}
                      {order.receiverAddress ? <p className="subtle">Address: {order.receiverAddress}</p> : null}
                    </div>
                  </div>
                  <div className="flex flex-col items-start gap-3 md:items-end">
                    <OrderStatusBadge status={order.status} />
                    <span className="text-xl font-bold text-coral">CNY {order.totalAmountCny.toFixed(2)}</span>
                    <p className="text-sm subtle">Paid: CNY {order.paidAmountCny.toFixed(2)}</p>
                    <div className="flex flex-wrap gap-2 md:justify-end">
                      <button
                        type="button"
                        className="rounded-full border border-black/10 bg-white px-4 py-2 text-sm font-semibold transition hover:bg-black/[0.03]"
                        onClick={() => setExpandedOrderId(isExpanded ? null : order.id)}
                      >
                        {isExpanded ? "Hide details" : "View details"}
                      </button>
                      <button
                        type="button"
                        className="rounded-full border border-red-200 bg-red-50 px-4 py-2 text-sm font-semibold text-red-700 transition hover:bg-red-100 disabled:cursor-not-allowed disabled:opacity-60"
                        onClick={() => handleDeleteOrder(order)}
                        disabled={deletingId === order.id}
                      >
                        {deletingId === order.id ? "Deleting..." : "Delete order"}
                      </button>
                    </div>
                  </div>
                </div>

                {isExpanded ? (
                  <div className="mt-5 grid gap-6 lg:grid-cols-[1.4fr_0.9fr]">
                    <div>
                      <h3 className="text-base font-semibold">Items</h3>
                      {order.items.length === 0 ? (
                        <p className="subtle mt-3 text-sm">No item details for this order.</p>
                      ) : (
                        <div className="mt-3 space-y-3">
                          {order.items.map((item) => (
                            <div key={item.id} className="rounded-2xl border border-black/10 bg-white/60 p-4">
                              <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
                                <div>
                                  <p className="font-semibold">{item.titleZh}</p>
                                  <p className="subtle text-sm">{item.titleKo}</p>
                                  <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-sm">
                                    <span>Quantity: {item.quantity}</span>
                                    <span>Unit: CNY {item.unitPriceCny.toFixed(2)}</span>
                                    <span>Option: {item.selectedOption || "Default"}</span>
                                    {item.sourceUrl ? (
                                      <a
                                        href={item.sourceUrl}
                                        target="_blank"
                                        rel="noreferrer"
                                        className="font-semibold text-coral underline underline-offset-4"
                                      >
                                        Official link
                                      </a>
                                    ) : null}
                                  </div>
                                  {item.note ? (
                                    <p className="mt-2 rounded-2xl bg-white/70 px-3 py-2 text-sm text-ink">
                                      Item note: {item.note}
                                    </p>
                                  ) : null}
                                </div>
                                <div className="text-sm font-semibold text-coral">
                                  Subtotal CNY {item.subtotalCny.toFixed(2)}
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    <div className="space-y-4">
                      <div className="rounded-2xl border border-black/10 bg-white/60 p-4">
                        <h3 className="text-base font-semibold">Amount</h3>
                        <div className="mt-3 space-y-2">
                          <MoneyRow label="Product amount" value={order.productTotalCny} />
                          <MoneyRow label="Service fee" value={order.serviceFeeCny} />
                          <MoneyRow label="International shipping" value={order.internationalShippingFeeCny} />
                          <MoneyRow label="Packaging fee" value={order.packageFeeCny} />
                          <div className="border-t border-black/10 pt-2">
                            <MoneyRow label="Total" value={order.totalAmountCny} emphasize />
                          </div>
                        </div>
                      </div>

                      {order.userNote ? (
                        <div className="rounded-2xl border border-black/10 bg-white/60 p-4">
                          <h3 className="text-base font-semibold">Order note</h3>
                          <p className="subtle mt-2 text-sm leading-6">{order.userNote}</p>
                        </div>
                      ) : null}

                      {order.adminNote ? (
                        <div className="rounded-2xl border border-black/10 bg-white/60 p-4">
                          <h3 className="text-base font-semibold">Admin note</h3>
                          <p className="subtle mt-2 text-sm leading-6">{order.adminNote}</p>
                        </div>
                      ) : null}
                    </div>
                  </div>
                ) : null}
              </article>
            );
          })}
        </section>
      )}
    </AuthGate>
  );
}
