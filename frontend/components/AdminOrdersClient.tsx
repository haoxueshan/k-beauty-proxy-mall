"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { OrderStatusBadge } from "@/components/OrderStatusBadge";
import { useAuth } from "@/components/AuthProvider";
import { getAdminOrder, getAdminOrders, updateAdminOrder } from "@/lib/api";
import { ORDER_STATUS_OPTIONS, type AdminOrderStatus, getOrderStatusLabel } from "@/lib/order-status";
import type { Order } from "@/lib/mock-data";

type FilterStatus = "all" | AdminOrderStatus;

function isAdminRole(role?: string | null) {
  return role === "admin" || role === "super_admin";
}

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

function getBuyerLabel(order: Order) {
  return order.userName || order.userEmail || order.userId || "-";
}

function getItemCount(order: Order) {
  return order.items.reduce((count, item) => count + item.quantity, 0);
}

export function AdminOrdersClient() {
  const { user, token, isLoading: isAuthLoading, isAuthenticated } = useAuth();
  const [orders, setOrders] = useState<Order[]>([]);
  const [filterStatus, setFilterStatus] = useState<FilterStatus>("all");
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isDetailLoading, setIsDetailLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState("");
  const [detailError, setDetailError] = useState("");

  useEffect(() => {
    if (isAuthLoading || !isAuthenticated || !token || !isAdminRole(user?.role)) {
      if (!isAuthenticated) {
        setOrders([]);
      }
      return;
    }

    setIsLoading(true);
    setError("");
    getAdminOrders(token)
      .then((items) => {
        setOrders(items);
      })
      .catch((requestError) => {
        setError(requestError instanceof Error ? requestError.message : "订单加载失败");
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, [isAuthLoading, isAuthenticated, token, user?.role]);

  async function handleOpenOrder(orderId: string) {
    if (!token) {
      return;
    }

    const existingOrder = orders.find((item) => item.id === orderId) ?? null;
    setSelectedOrder(existingOrder);
    setDetailError("");
    setIsDetailLoading(true);

    try {
      const detail = await getAdminOrder(token, orderId);
      setSelectedOrder(detail);
    } catch (requestError) {
      setDetailError(requestError instanceof Error ? requestError.message : "订单详情加载失败");
    } finally {
      setIsDetailLoading(false);
    }
  }

  async function handleSave() {
    if (!token || !selectedOrder) {
      return;
    }

    setIsSaving(true);
    setDetailError("");
    try {
      const updatedOrder = await updateAdminOrder(token, selectedOrder.id, {
        status: selectedOrder.status as AdminOrderStatus,
        adminNote: selectedOrder.adminNote?.trim() ? selectedOrder.adminNote.trim() : null
      });
      setSelectedOrder(updatedOrder);
      setOrders((current) => current.map((item) => (item.id === updatedOrder.id ? updatedOrder : item)));
    } catch (requestError) {
      setDetailError(requestError instanceof Error ? requestError.message : "订单保存失败");
    } finally {
      setIsSaving(false);
    }
  }

  const visibleOrders =
    filterStatus === "all" ? orders : orders.filter((order) => order.status === filterStatus);

  if (isAuthLoading) {
    return (
      <section className="panel mt-8 p-8">
        <p className="text-lg font-semibold">正在验证管理员身份</p>
        <p className="subtle mt-2">请稍候，我们正在检查当前登录状态。</p>
      </section>
    );
  }

  if (!isAuthenticated) {
    return (
      <section className="panel mt-8 p-8">
        <p className="text-lg font-semibold">请先登录管理员账号</p>
        <p className="subtle mt-2">登录后才能查看全部用户订单并处理状态与备注。</p>
        <div className="mt-6 flex gap-3">
          <Link href="/admin/login" className="cta">
            去管理员登录
          </Link>
          <Link href="/" className="cta ghost">
            返回首页
          </Link>
        </div>
      </section>
    );
  }

  if (!isAdminRole(user?.role)) {
    return (
      <section className="panel mt-8 p-8">
        <p className="text-lg font-semibold">无后台访问权限</p>
        <p className="subtle mt-2">当前账号 role 为普通用户，不能访问管理员订单页。</p>
      </section>
    );
  }

  return (
    <>
      <section className="panel mt-8 p-6">
        <div className="flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={() => setFilterStatus("all")}
            className={`rounded-full px-4 py-2 text-sm ${filterStatus === "all" ? "bg-ink text-white" : "border border-black/10 bg-white/80"}`}
          >
            全部
          </button>
          {ORDER_STATUS_OPTIONS.map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => setFilterStatus(option.value)}
              className={`rounded-full px-4 py-2 text-sm ${
                filterStatus === option.value ? "bg-ink text-white" : "border border-black/10 bg-white/80"
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>
      </section>

      <section className="panel mt-6 overflow-hidden p-0">
        {isLoading ? (
          <div className="p-8">
            <p className="text-lg font-semibold">正在加载订单...</p>
          </div>
        ) : error ? (
          <div className="p-8">
            <p className="text-lg font-semibold">订单加载失败</p>
            <p className="subtle mt-2">{error}</p>
          </div>
        ) : visibleOrders.length === 0 ? (
          <div className="p-8">
            <p className="text-lg font-semibold">当前筛选下没有订单</p>
            <p className="subtle mt-2">你可以切换状态筛选查看其他订单。</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="bg-black/[0.03] text-left">
                <tr>
                  <th className="px-6 py-4 font-semibold">订单号</th>
                  <th className="px-6 py-4 font-semibold">用户</th>
                  <th className="px-6 py-4 font-semibold">商品数</th>
                  <th className="px-6 py-4 font-semibold">订单金额</th>
                  <th className="px-6 py-4 font-semibold">状态</th>
                  <th className="px-6 py-4 font-semibold">创建时间</th>
                  <th className="px-6 py-4 font-semibold">操作</th>
                </tr>
              </thead>
              <tbody>
                {visibleOrders.map((order) => (
                  <tr key={order.id} className="border-t border-black/10">
                    <td className="px-6 py-4 font-semibold">{order.orderNo}</td>
                    <td className="px-6 py-4">{getBuyerLabel(order)}</td>
                    <td className="px-6 py-4">{getItemCount(order)}</td>
                    <td className="px-6 py-4">{formatMoney(order.totalAmountCny)}</td>
                    <td className="px-6 py-4">
                      <OrderStatusBadge status={order.status} />
                    </td>
                    <td className="px-6 py-4">{formatDateTime(order.createdAt)}</td>
                    <td className="px-6 py-4">
                      <button
                        type="button"
                        onClick={() => handleOpenOrder(order.id)}
                        className="rounded-full border border-black/10 bg-white px-4 py-2 font-semibold"
                      >
                        查看/处理
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {selectedOrder ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 px-4 py-8">
          <div className="panel max-h-[90vh] w-full max-w-4xl overflow-y-auto p-0">
            <div className="flex items-start justify-between gap-4 border-b border-black/10 px-6 py-5">
              <div>
                <p className="eyebrow">Order Detail</p>
                <h2 className="mt-2 text-2xl font-semibold">{selectedOrder.orderNo}</h2>
              </div>
              <button
                type="button"
                onClick={() => setSelectedOrder(null)}
                className="rounded-full border border-black/10 px-3 py-1 text-sm"
              >
                关闭
              </button>
            </div>

            <div className="p-6">
              {isDetailLoading ? <p className="text-sm">正在加载订单详情...</p> : null}
              {detailError ? <p className="rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-700">{detailError}</p> : null}

              <div className="grid gap-4 md:grid-cols-2">
                <div className="rounded-2xl border border-black/10 bg-white/70 p-4">
                  <p className="font-semibold">用户信息</p>
                  <div className="subtle mt-2 space-y-1 text-sm">
                    <p>用户：{getBuyerLabel(selectedOrder)}</p>
                    {selectedOrder.userEmail ? <p>邮箱：{selectedOrder.userEmail}</p> : null}
                    {selectedOrder.userPhone ? <p>电话：{selectedOrder.userPhone}</p> : null}
                    {selectedOrder.userId ? <p>用户 ID：{selectedOrder.userId}</p> : null}
                  </div>
                </div>

                <div className="rounded-2xl border border-black/10 bg-white/70 p-4">
                  <p className="font-semibold">收货地址</p>
                  <div className="subtle mt-2 space-y-1 text-sm">
                    <p>收货人：{selectedOrder.receiverName}</p>
                    {selectedOrder.receiverPhone ? <p>电话：{selectedOrder.receiverPhone}</p> : null}
                    {selectedOrder.receiverAddress ? <p>地址：{selectedOrder.receiverAddress}</p> : null}
                    {selectedOrder.userNote ? <p>用户备注：{selectedOrder.userNote}</p> : null}
                  </div>
                </div>
              </div>

              <div className="mt-4 rounded-2xl border border-black/10 bg-white/70 p-4">
                <p className="font-semibold">商品列表</p>
                <div className="mt-3 space-y-3">
                  {selectedOrder.items.map((item) => (
                    <div key={item.id} className="rounded-2xl border border-black/10 bg-white p-4">
                      <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
                        <div>
                          <p className="font-semibold">{item.titleZh}</p>
                          <p className="subtle text-sm">{item.titleKo}</p>
                          <p className="subtle mt-2 text-sm">
                            数量：{item.quantity}
                            {item.selectedOption ? ` / 规格：${item.selectedOption}` : ""}
                          </p>
                        </div>
                        <p className="font-semibold">{formatMoney(item.subtotalCny)}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="mt-4 grid gap-4 md:grid-cols-[0.8fr_1.2fr]">
                <div className="rounded-2xl border border-black/10 bg-white/70 p-4">
                  <p className="font-semibold">订单金额</p>
                  <div className="subtle mt-2 space-y-1 text-sm">
                    <p>商品金额：{formatMoney(selectedOrder.productTotalCny)}</p>
                    <p>服务费：{formatMoney(selectedOrder.serviceFeeCny)}</p>
                    <p>国际运费：{formatMoney(selectedOrder.internationalShippingFeeCny)}</p>
                    <p>包装费：{formatMoney(selectedOrder.packageFeeCny)}</p>
                    <p className="font-semibold text-ink">订单金额：{formatMoney(selectedOrder.totalAmountCny)}</p>
                  </div>
                </div>

                <div className="rounded-2xl border border-black/10 bg-white/70 p-4">
                  <p className="font-semibold">处理信息</p>
                  <div className="mt-3 space-y-4">
                    <label className="block">
                      <span className="mb-2 block text-sm">状态</span>
                      <select
                        value={selectedOrder.status}
                        onChange={(event) =>
                          setSelectedOrder((current) =>
                            current ? { ...current, status: event.target.value as AdminOrderStatus } : current
                          )
                        }
                        className="min-h-[48px] w-full rounded-2xl border border-black/10 bg-white px-4 outline-none"
                      >
                        {ORDER_STATUS_OPTIONS.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                    </label>

                    <label className="block">
                      <span className="mb-2 block text-sm">管理员备注</span>
                      <textarea
                        value={selectedOrder.adminNote ?? ""}
                        onChange={(event) =>
                          setSelectedOrder((current) =>
                            current ? { ...current, adminNote: event.target.value } : current
                          )
                        }
                        rows={5}
                        className="w-full rounded-2xl border border-black/10 bg-white px-4 py-3 outline-none"
                        placeholder="输入内部处理备注"
                      />
                    </label>

                    <div className="flex items-center justify-between gap-3">
                      <p className="subtle text-sm">当前状态：{getOrderStatusLabel(selectedOrder.status)}</p>
                      <button type="button" onClick={handleSave} className="cta" disabled={isSaving || isDetailLoading}>
                        {isSaving ? "保存中..." : "保存"}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}
