"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { AuthGate } from "@/components/AuthGate";
import { useAuth } from "@/components/AuthProvider";
import { CartItem } from "@/components/CartItem";
import { createOrder, deleteCartItem, getCartItems, updateCartItem } from "@/lib/api";
import type { CartDisplayItem } from "@/lib/mock-data";

type OrderFormState = {
  receiverName: string;
  receiverPhone: string;
  receiverAddress: string;
  note: string;
};

export function CartClient() {
  const { token, user, isAuthenticated } = useAuth();
  const [items, setItems] = useState<CartDisplayItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [removingId, setRemovingId] = useState<string | null>(null);
  const [savingId, setSavingId] = useState<string | null>(null);
  const [isSubmittingOrder, setIsSubmittingOrder] = useState(false);
  const [createdOrderNo, setCreatedOrderNo] = useState("");
  const [orderForm, setOrderForm] = useState<OrderFormState>({
    receiverName: "",
    receiverPhone: "",
    receiverAddress: "",
    note: ""
  });

  useEffect(() => {
    if (!user) {
      return;
    }
    // 登录后预填用户资料，不覆盖已手动输入的内容。
    setOrderForm((current) => ({
      receiverName: current.receiverName || user.name || "",
      receiverPhone: current.receiverPhone || user.phone || "",
      receiverAddress: current.receiverAddress,
      note: current.note
    }));
  }, [user]);

  useEffect(() => {
    if (!isAuthenticated || !token) {
      setItems([]);
      return;
    }
    // 使用后端 display 接口一次性获取购物车和商品信息。
    setIsLoading(true);
    setError("");
    getCartItems(token)
      .then((result) => {
        setItems(result);
      })
      .catch((requestError) => {
        setError(requestError instanceof Error ? requestError.message : "购物车加载失败");
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, [isAuthenticated, token]);

  const totalQuantity = useMemo(
    () => items.reduce((sum, item) => sum + item.quantity, 0),
    [items]
  );
  const totalAmount = useMemo(
    // 金额统一按人民币参考价 priceCny 计算。
    () => items.reduce((sum, item) => sum + item.product.priceCny * item.quantity, 0),
    [items]
  );

  function updateOrderField<K extends keyof OrderFormState>(field: K, value: OrderFormState[K]) {
    setOrderForm((current) => ({
      ...current,
      [field]: value
    }));
  }

  async function handleSave(cartItemId: string, payload: { quantity: number; note: string }) {
    if (!token) {
      return;
    }

    setSavingId(cartItemId);
    setError("");
    try {
      const updated = await updateCartItem(token, cartItemId, {
        quantity: payload.quantity,
        note: payload.note || null
      });
      setItems((current) =>
        current.map((item) =>
          item.id === cartItemId
            ? {
                ...item,
                quantity: updated.quantity,
                note: updated.note
              }
            : item
        )
      );
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "购物车更新失败");
    } finally {
      setSavingId(null);
    }
  }

  async function handleRemove(cartItemId: string) {
    if (!token) {
      return;
    }

    setRemovingId(cartItemId);
    setError("");
    try {
      await deleteCartItem(token, cartItemId);
      // 删除成功后本地立即移除，避免整页重新加载。
      setItems((current) => current.filter((item) => item.id !== cartItemId));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "删除失败");
    } finally {
      setRemovingId(null);
    }
  }

  async function handleCreateOrder() {
    if (!token || items.length === 0) {
      return;
    }

    setIsSubmittingOrder(true);
    setError("");
    try {
      const result = await createOrder(token, {
        cartItemIds: items.map((item) => item.id),
        receiverName: orderForm.receiverName.trim(),
        receiverPhone: orderForm.receiverPhone.trim(),
        receiverAddress: orderForm.receiverAddress.trim(),
        note: orderForm.note.trim()
      });
      setCreatedOrderNo(result.orderNo);
      // 下单成功后购物车条目已转入订单，前端同步清空当前列表。
      setItems([]);
      setOrderForm((current) => ({
        ...current,
        note: ""
      }));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "订单提交失败");
    } finally {
      setIsSubmittingOrder(false);
    }
  }

  return (
    <AuthGate title="登录后使用购物车" description="购物车、下单和后续订单追踪需要先绑定到你的账号。">
      {isLoading ? (
        <div className="panel mt-8 flex items-center gap-4 p-8">
          <div className="h-11 w-11 animate-spin rounded-full border-2 border-coral/20 border-t-coral" />
          <div>
            <p className="text-lg font-semibold">正在加载购物车...</p>
            <p className="subtle mt-1 text-sm">正在一次性读取购物车条目和商品展示信息。</p>
          </div>
        </div>
      ) : items.length === 0 ? (
        <div className="panel mt-8 p-8">
          {error ? <p className="rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p> : null}
          {createdOrderNo ? (
            <>
              <p className="mt-4 text-lg font-semibold">订单已生成</p>
              <p className="subtle mt-2">订单号：{createdOrderNo}。购物车商品已转入订单，你可以继续查看订单状态。</p>
              <div className="mt-6 flex flex-wrap gap-3">
                <Link href="/orders" className="cta inline-flex">
                  查看我的订单
                </Link>
                <Link href="/search" className="cta ghost inline-flex">
                  继续选购
                </Link>
              </div>
            </>
          ) : (
            <>
              <p className="mt-4 text-lg font-semibold">购物车还是空的</p>
              <p className="subtle mt-2">先去搜索页同步并挑选几个 Olive Young 商品吧。</p>
              <Link href="/search" className="cta mt-6 inline-flex">
                去搜索商品
              </Link>
            </>
          )}
        </div>
      ) : (
        <section className="mt-8 grid gap-8 md:grid-cols-[1.3fr_0.8fr]">
          <div className="space-y-4">
            {error ? <p className="rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p> : null}
            {items.map((item) => (
              <CartItem
                key={item.id}
                cartItemId={item.id}
                product={item.product}
                quantity={item.quantity}
                selectedOption={item.selectedOption ?? "默认规格"}
                note={item.note ?? ""}
                isRemoving={removingId === item.id}
                isSaving={savingId === item.id}
                onSave={handleSave}
                onRemove={handleRemove}
              />
            ))}
          </div>
          <aside className="panel h-fit p-6">
            <h2 className="text-xl font-semibold">提交商品订单</h2>
            <div className="mt-6 space-y-3 text-sm">
              <div className="flex justify-between">
                <span>商品参考总额</span>
                <span>¥{totalAmount.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span>商品总件数</span>
                <span>{totalQuantity} 件</span>
              </div>
              <div className="flex justify-between">
                <span>订单状态</span>
                <span>提交后进入待报价</span>
              </div>
            </div>
            <div className="mt-6 space-y-4">
              <label className="block space-y-2 text-sm">
                <span className="subtle">收件人</span>
                <input
                  value={orderForm.receiverName}
                  onChange={(event) => updateOrderField("receiverName", event.target.value)}
                  className="min-h-[48px] w-full rounded-2xl border border-black/10 bg-white/80 px-4 outline-none"
                  placeholder="请输入收件人姓名"
                />
              </label>
              <label className="block space-y-2 text-sm">
                <span className="subtle">联系电话</span>
                <input
                  value={orderForm.receiverPhone}
                  onChange={(event) => updateOrderField("receiverPhone", event.target.value)}
                  className="min-h-[48px] w-full rounded-2xl border border-black/10 bg-white/80 px-4 outline-none"
                  placeholder="请输入手机号或微信"
                />
              </label>
              <label className="block space-y-2 text-sm">
                <span className="subtle">收货地址</span>
                <textarea
                  value={orderForm.receiverAddress}
                  onChange={(event) => updateOrderField("receiverAddress", event.target.value)}
                  rows={4}
                  className="w-full rounded-2xl border border-black/10 bg-white/80 px-4 py-3 outline-none"
                  placeholder="请输入详细收货地址"
                />
              </label>
              <label className="block space-y-2 text-sm">
                <span className="subtle">订单备注</span>
                <textarea
                  value={orderForm.note}
                  onChange={(event) => updateOrderField("note", event.target.value)}
                  rows={3}
                  className="w-full rounded-2xl border border-black/10 bg-white/80 px-4 py-3 outline-none"
                  placeholder="例如：希望尽量凑单、优先保质期长的批次"
                />
              </label>
            </div>
            <button
              type="button"
              className="cta mt-6 w-full"
              onClick={handleCreateOrder}
              disabled={
                isSubmittingOrder ||
                !orderForm.receiverName.trim() ||
                !orderForm.receiverPhone.trim() ||
                !orderForm.receiverAddress.trim()
              }
            >
              {isSubmittingOrder ? "提交中..." : "生成订单"}
            </button>
            <p className="subtle mt-3 text-sm">提交后购物车商品会转入订单，后续可在“我的订单”里查看状态。</p>
          </aside>
        </section>
      )}
    </AuthGate>
  );
}


