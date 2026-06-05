"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AuthGate } from "@/components/AuthGate";
import { CartItem } from "@/components/CartItem";
import { useAuth } from "@/components/AuthProvider";
import { deleteCartItem, getCartItems } from "@/lib/api";
import type { CartDisplayItem } from "@/lib/mock-data";

export function CartClient() {
  const { token, isAuthenticated } = useAuth();
  const [items, setItems] = useState<CartDisplayItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [removingId, setRemovingId] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated || !token) {
      setItems([]);
      return;
    }

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

  async function handleRemove(cartItemId: string) {
    if (!token) {
      return;
    }
    setRemovingId(cartItemId);
    try {
      await deleteCartItem(token, cartItemId);
      setItems((current) => current.filter((item) => item.id !== cartItemId));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "删除失败");
    } finally {
      setRemovingId(null);
    }
  }

  const total = items.reduce((sum, item) => sum + item.product.proxyPriceCny * item.quantity, 0);

  return (
    <AuthGate title="登录后使用代购购物车" description="购物车、下单和后续订单追踪需要先绑定到你的账号。">
      {isLoading ? (
        <div className="panel mt-8 p-8">
          <p className="text-lg font-semibold">正在加载购物车…</p>
        </div>
      ) : items.length === 0 ? (
        <div className="panel mt-8 p-8">
          <p className="text-lg font-semibold">购物车还是空的</p>
          <p className="subtle mt-2">先去搜索页挑几个 Olive Young 商品吧。</p>
          <Link href="/search" className="cta mt-6 inline-flex">
            去搜索商品
          </Link>
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
                note={item.note ?? "无"}
                isRemoving={removingId === item.id}
                onRemove={handleRemove}
              />
            ))}
          </div>
          <aside className="panel h-fit p-6">
            <h2 className="text-xl font-semibold">订单预估</h2>
            <div className="mt-6 space-y-3 text-sm">
              <div className="flex justify-between">
                <span>商品预估总额</span>
                <span>¥{total.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span>商品件数</span>
                <span>{items.length} 件</span>
              </div>
              <div className="flex justify-between">
                <span>人工确认后可能调整</span>
                <span>以最终报价为准</span>
              </div>
            </div>
            <Link href="/orders" className="cta mt-6 w-full">
              去查看订单
            </Link>
          </aside>
        </section>
      )}
    </AuthGate>
  );
}
