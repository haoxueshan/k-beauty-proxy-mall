"use client";

import Link from "next/link";
import { useAuth } from "@/components/AuthProvider";

export function MainNav() {
  const { user } = useAuth();

  return (
    <nav className="flex flex-wrap gap-3 text-sm">
      <Link href="/search">搜索</Link>
      <Link href="/cart">购物车</Link>
      <Link href="/orders">我的订单</Link>
      {user?.isAdmin ? <Link href="/admin/orders">后台</Link> : null}
    </nav>
  );
}
