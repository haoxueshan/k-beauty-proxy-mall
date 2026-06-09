"use client";

import { CartClient } from "@/components/CartClient";

export default function CartPage() {
  return (
    <div className="container pb-16">
      <section className="panel p-8">
        <p className="eyebrow">Shopping Cart</p>
        <h1 className="mt-3 text-3xl font-semibold">平台购物车</h1>
        <p className="subtle mt-2">
          这里展示你从同步商品里加入的商品清单，不会直接修改 Olive Young 官方购物车。
        </p>
      </section>
      <CartClient />
    </div>
  );
}
