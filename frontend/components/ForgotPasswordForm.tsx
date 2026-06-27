"use client";

import Link from "next/link";
import { useState } from "react";
import { resetPassword } from "@/lib/api";

export function ForgotPasswordForm() {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");
    setError("");
    setIsSubmitting(true);

    const formData = new FormData(event.currentTarget);
    try {
      await resetPassword({
        email: String(formData.get("email") ?? "").trim(),
        phone: String(formData.get("phone") ?? "").trim(),
        verificationCode: String(formData.get("verificationCode") ?? "").trim(),
        newPassword: String(formData.get("newPassword") ?? "").trim()
      });
      setMessage("密码已重置，请返回登录。");
      event.currentTarget.reset();
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "密码重置失败");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="panel mx-auto max-w-xl p-8">
      <p className="eyebrow">Reset Password</p>
      <h1 className="mt-3 text-3xl font-semibold">重置密码</h1>
      <p className="subtle mt-2">测试阶段验证码默认为注册手机号后 4 位。</p>

      <form onSubmit={handleSubmit} className="mt-8 space-y-4">
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

        <label className="block">
          <span className="mb-2 block text-sm">手机号</span>
          <input
            required
            name="phone"
            className="min-h-[52px] w-full rounded-2xl border border-black/10 bg-white/80 px-4 outline-none"
            placeholder="注册时填写的手机号"
          />
        </label>

        <label className="block">
          <span className="mb-2 block text-sm">验证码</span>
          <input
            required
            name="verificationCode"
            inputMode="numeric"
            className="min-h-[52px] w-full rounded-2xl border border-black/10 bg-white/80 px-4 outline-none"
            placeholder="手机号后 4 位"
          />
        </label>

        <label className="block">
          <span className="mb-2 block text-sm">新密码</span>
          <input
            required
            minLength={6}
            name="newPassword"
            type="password"
            className="min-h-[52px] w-full rounded-2xl border border-black/10 bg-white/80 px-4 outline-none"
            placeholder="至少 6 位"
          />
        </label>

        {message ? <p className="rounded-2xl bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{message}</p> : null}
        {error ? <p className="rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p> : null}

        <button type="submit" className="cta w-full" disabled={isSubmitting}>
          {isSubmitting ? "提交中..." : "重置密码"}
        </button>
      </form>

      <p className="subtle mt-6 text-sm">
        想起密码了？{" "}
        <Link href="/login" className="font-semibold text-ink">
          返回登录
        </Link>
      </p>
    </section>
  );
}
