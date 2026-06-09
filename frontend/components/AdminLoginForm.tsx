"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useAuth } from "@/components/AuthProvider";

function isAdminRole(role?: string | null) {
  return role === "admin" || role === "super_admin";
}

export function AdminLoginForm() {
  const router = useRouter();
  const { user, isLoading, isAuthenticated, login } = useAuth();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (isLoading || !isAuthenticated || !user) {
      return;
    }
    if (isAdminRole(user.role)) {
      router.replace("/admin/orders");
      router.refresh();
      return;
    }
    setError("无后台访问权限");
  }, [isAuthenticated, isLoading, router, user]);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);

    const formData = new FormData(event.currentTarget);
    const email = String(formData.get("email") ?? "").trim();
    const password = String(formData.get("password") ?? "").trim();

    try {
      const nextUser = await login({ email, password });
      if (isAdminRole(nextUser.role)) {
        router.push("/admin/orders");
        router.refresh();
        return;
      }
      setError("无后台访问权限");
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "登录失败");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="panel mx-auto max-w-xl p-8">
      <p className="eyebrow">Admin Access</p>
      <h1 className="mt-3 text-3xl font-semibold">管理员登录</h1>
      <p className="subtle mt-2">登录后会根据当前账号的 role 自动判断是否可以进入订单管理页。</p>

      <form onSubmit={handleSubmit} className="mt-8 space-y-4">
        <label className="block">
          <span className="mb-2 block text-sm">账号或邮箱</span>
          <input
            required
            name="email"
            type="text"
            className="min-h-[52px] w-full rounded-2xl border border-black/10 bg-white/80 px-4 outline-none"
            placeholder="haoxueshan5@gmail.com"
          />
        </label>

        <label className="block">
          <span className="mb-2 block text-sm">密码</span>
          <input
            required
            minLength={6}
            name="password"
            type="password"
            className="min-h-[52px] w-full rounded-2xl border border-black/10 bg-white/80 px-4 outline-none"
            placeholder="至少 6 位"
          />
        </label>

        {error ? <p className="rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p> : null}

        <button type="submit" className="cta w-full" disabled={isSubmitting || isLoading}>
          {isSubmitting ? "登录中..." : "进入后台"}
        </button>
      </form>

      <p className="subtle mt-6 text-sm">
        普通用户登录后无法进入后台。
        <Link href="/login" className="ml-2 font-semibold text-ink">
          用户登录
        </Link>
      </p>
    </section>
  );
}
