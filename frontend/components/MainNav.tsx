"use client";

import Link from "next/link";

export function MainNav() {
  return (
    <nav className="flex flex-wrap gap-3 text-sm">
      <Link href="/search">搜索</Link>
      <Link href="/cart">购物车</Link>
      <Link href="/orders">我的订单</Link>
      <Link href="/admin/login" className="subtle">
        管理员入口
      </Link>
    </nav>
  );
}
