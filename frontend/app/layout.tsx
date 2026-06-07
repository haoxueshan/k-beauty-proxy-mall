import type { Metadata } from "next";
import Link from "next/link";
import { AuthNav } from "@/components/AuthNav";
import { AuthProvider } from "@/components/AuthProvider";
import "./globals.css";

export const metadata: Metadata = {
  title: "Olive Young 中文代购平台",
  description: "面向中国用户的 Olive Young 中文搜索与代购平台 MVP"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>
        <AuthProvider>
          <div className="grain" />
          <div className="shell">
            <header className="container py-6">
              <div className="panel flex flex-col gap-4 px-6 py-5 md:flex-row md:items-center md:justify-between">
                <Link href="/" className="text-xl font-bold tracking-[0.2em]">
                  OLIVE YOUNG CN
                </Link>
                <div className="flex flex-col gap-3 md:items-end">
                  <nav className="flex flex-wrap gap-3 text-sm">
                    <Link href="/search">搜索</Link>
                    <Link href="/cart">购物车</Link>
                    <Link href="/orders">我的订单</Link>
                    <Link href="/admin/orders">后台</Link>
                  </nav>
                  <AuthNav />
                </div>
              </div>
            </header>
            <main>{children}</main>
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}
