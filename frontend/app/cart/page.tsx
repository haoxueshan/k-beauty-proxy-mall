"use client";

import { CartClient } from "@/components/CartClient";

export default function CartPage() {
  return (
    <div className="container pb-16">
      <section className="panel p-8">
        <p className="eyebrow">Proxy Cart</p>
        <h1 className="mt-3 text-3xl font-semibold">平台代购购物车</h1>
        <p className="subtle mt-2">这里是平台自己的代购购物车，不直接同步 Olive Young 官方购物车。</p>
      </section>
      <CartClient />
    </div>
  );
}
