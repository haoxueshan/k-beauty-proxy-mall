"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/AuthProvider";

export function AuthNav() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading, logout } = useAuth();

  async function handleLogout() {
    await logout();
    router.push("/");
    router.refresh();
  }

  if (isLoading) {
    return <span className="text-sm subtle">正在加载账号…</span>;
  }

  if (!isAuthenticated || !user) {
    return (
      <div className="flex flex-wrap gap-3 text-sm">
        <Link href="/login">登录</Link>
        <Link href="/register">注册</Link>
      </div>
    );
  }

  return (
    <div className="flex flex-wrap items-center gap-3 text-sm">
      <span className="subtle">你好，{user.name}</span>
      <button type="button" onClick={handleLogout} className="rounded-full border border-black/10 px-3 py-1">
        退出登录
      </button>
    </div>
  );
}
