"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import { syncOliveYoungProducts } from "@/lib/api";

type Props = {
  keyword: string;
  limit?: number;
  page?: number;
  pageSize?: number;
  sort?: string;
};

export function SyncCrawlerButton({ keyword, limit = 24, page = 1, pageSize = limit, sort = "ranking" }: Props) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [isSyncing, setIsSyncing] = useState(false);

  async function handleSync() {
    setIsSyncing(true);
    setMessage("");
    setError("");

    try {
      const result = await syncOliveYoungProducts(keyword || "homepage", limit, { page, pageSize, sort });
      if (result.source === "fallback-seed" || result.source.includes("error")) {
        setError(`没有同步到实时 Olive Young 数据，当前来源：${result.source}`);
        return;
      }

      setMessage(`已同步第 ${page} 页 ${result.count} 个商品，来源：${result.source || "Olive Young 首页"}`);
      startTransition(() => {
        router.refresh();
      });
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "同步失败，请稍后再试");
    } finally {
      setIsSyncing(false);
    }
  }

  return (
    <div className="space-y-2">
      <button type="button" className="cta ghost" onClick={handleSync} disabled={isSyncing || isPending}>
        {isSyncing || isPending ? "正在同步..." : `同步当前页（第 ${page} 页）`}
      </button>
      {message ? <p className="text-sm text-emerald-700">{message}</p> : null}
      {error ? <p className="text-sm text-red-700">{error}</p> : null}
    </div>
  );
}
