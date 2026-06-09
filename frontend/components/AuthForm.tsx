"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useAuth } from "@/components/AuthProvider";

type Mode = "login" | "register";

export function AuthForm({ mode }: { mode: Mode }) {
  const router = useRouter();
  const { login, register } = useAuth();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);

    const formData = new FormData(event.currentTarget);
    const email = String(formData.get("email") ?? "").trim();
    const password = String(formData.get("password") ?? "").trim();

    try {
      if (mode === "login") {
        await login({ email, password });
      } else {
        await register({
          email,
          password,
          name: String(formData.get("name") ?? "").trim(),
          phone: String(formData.get("phone") ?? "").trim()
        });
      }
      router.push("/orders");
      router.refresh();
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "提交失败");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="panel mx-auto max-w-xl p-8">
      <p className="eyebrow">{mode === "login" ? "Sign In" : "Create Account"}</p>
      <h1 className="mt-3 text-3xl font-semibold">{mode === "login" ? "用户登录" : "用户注册"}</h1>
      <p className="subtle mt-2">
        {mode === "login" ? "登录后可以查看你的订单和后续处理进度。" : "注册后即可保存账号状态，继续下单和查看订单。"}
      </p>

      <form onSubmit={handleSubmit} className="mt-8 space-y-4">
        {mode === "register" ? (
          <label className="block">
            <span className="mb-2 block text-sm">姓名</span>
            <input
              required
              name="name"
              className="min-h-[52px] w-full rounded-2xl border border-black/10 bg-white/80 px-4 outline-none"
              placeholder="请输入姓名"
            />
          </label>
        ) : null}

        <label className="block">
          <span className="mb-2 block text-sm">邮箱</span>
          <input
            required
            name="email"
            type="email"
            className="min-h-[52px] w-full rounded-2xl border border-black/10 bg-white/80 px-4 outline-none"
            placeholder="name@example.com"
          />
        </label>

        {mode === "register" ? (
          <label className="block">
            <span className="mb-2 block text-sm">手机号</span>
            <input
              name="phone"
              className="min-h-[52px] w-full rounded-2xl border border-black/10 bg-white/80 px-4 outline-none"
              placeholder="选填"
            />
          </label>
        ) : null}

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

        <button type="submit" className="cta w-full" disabled={isSubmitting}>
          {isSubmitting ? "提交中..." : mode === "login" ? "登录" : "注册并登录"}
        </button>
      </form>

      <p className="subtle mt-6 text-sm">
        {mode === "login" ? "还没有账号？" : "已经有账号？"}{" "}
        <Link href={mode === "login" ? "/register" : "/login"} className="font-semibold text-ink">
          {mode === "login" ? "去注册" : "去登录"}
        </Link>
      </p>
    </section>
  );
}
