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
  compact?: boolean;
};

export function SyncCrawlerButton({ keyword, limit = 48, page = 1, pageSize = limit, sort = "ranking", compact = false }: Props) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [isSyncing, setIsSyncing] = useState(false);

  async function handleSync() {
    // 只刷新当前关键词、页码和排序对应的数据，避免用户翻页时误刷新全部页面。
    setIsSyncing(true);
    setMessage("");
    setError("");

    try {
      const result = await syncOliveYoungProducts(keyword || "homepage", limit, { page, pageSize, sort });
      if (result.source === "fallback-seed" || result.source.includes("error")) {
        setError(`没有同步到实时 Olive Young 数据，当前来源：${result.source}`);
        return;
      }

      setMessage(`已刷新 ${result.count} 个商品，来源：${result.source || "Olive Young 首页"}`);
      startTransition(() => {
        // 刷新服务端组件数据，同时让按钮保持过渡状态，减少页面突兀闪烁。
        router.refresh();
      });
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "同步失败，请稍后再试");
    } finally {
      setIsSyncing(false);
    }
  }

  return (
    <div className={compact ? "inline-flex flex-col gap-2" : "space-y-2"}>
      <button type="button" className="cta ghost" onClick={handleSync} disabled={isSyncing || isPending}>
        {isSyncing || isPending ? "正在刷新..." : "刷新结果"}
      </button>
      {message ? <p className="text-sm text-emerald-700">{message}</p> : null}
      {error ? <p className="text-sm text-red-700">{error}</p> : null}
    </div>
  );
}
