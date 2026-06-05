"use client";

import Link from "next/link";
import { useAuth } from "@/components/AuthProvider";

export function AuthGate({
  title,
  description,
  children
}: {
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="panel p-8">
        <h2 className="text-2xl font-semibold">正在验证登录状态</h2>
        <p className="subtle mt-2">请稍候，我们正在确认你的账号信息。</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="panel p-8">
        <h2 className="text-2xl font-semibold">{title}</h2>
        <p className="subtle mt-2">{description}</p>
        <div className="mt-6 flex gap-3">
          <Link href="/login" className="cta">
            去登录
          </Link>
          <Link href="/register" className="cta ghost">
            注册账号
          </Link>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
