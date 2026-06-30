"use client";

import { useEffect, useRef, useState } from "react";
import { ProductCard } from "@/components/ProductCard";
import { SearchBar } from "@/components/SearchBar";
import { SyncCrawlerButton } from "@/components/SyncCrawlerButton";
import { searchProductResults, type ProductSearchResult } from "@/lib/api";
import {
  formatConfidence,
  formatSyncedAt,
  getCacheLayerLabel,
  getSourceLabel,
  getSourceTypeLabel,
  isFallbackSource
} from "@/lib/product-meta";

type Props = {
  initialKeyword: string;
  initialSort: string;
};

const skeletonCards = ["one", "two", "three", "four", "five", "six"];

export function SearchResultsClient({ initialKeyword, initialSort }: Props) {
  const [result, setResult] = useState<ProductSearchResult | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const autoRefreshKeyRef = useRef("");

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    setError("");
    setResult(null);

    searchProductResults(initialKeyword, { sort: initialSort })
      .then((data) => {
        if (!cancelled) {
          setResult(data);
          setError(data.error ?? "");
        }
      })
      .catch((requestError) => {
        if (!cancelled) {
          setError(requestError instanceof Error ? requestError.message : "搜索请求失败");
        }
      })
      .finally(() => {
        if (!cancelled) {
          setIsLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [initialKeyword, initialSort]);

  useEffect(() => {
    if (!result || isLoading || !shouldRefreshTranslations(result)) {
      return;
    }

    const refreshKey = `${initialKeyword}|${initialSort}|${result.page}|${result.pageSize}`;
    if (autoRefreshKeyRef.current === refreshKey) {
      return;
    }
    autoRefreshKeyRef.current = refreshKey;

    let cancelled = false;
    const timer = window.setTimeout(() => {
      searchProductResults(initialKeyword, {
        page: result.page,
        pageSize: result.pageSize,
        sort: result.sort
      })
        .then((data) => {
          if (!cancelled) {
            setResult(data);
            setError(data.error ?? "");
          }
        })
        .catch(() => {
          // Keep the first visible result; translation refresh is a best-effort improvement.
        });
    }, 4500);

    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [initialKeyword, initialSort, isLoading, result]);

  const products = result?.items ?? [];
  const fallbackProducts = result?.fallbackItems ?? [];
  const primaryMeta = result?.resultMeta;
  const fallbackMeta = result?.fallbackMeta;
  const primaryIsFallback = result ? isFallbackSource(result.sourceType) : false;
  const displayKeyword = result?.keywordOriginal || initialKeyword || "全部商品";
  const resultSourceText = primaryMeta?.cacheLayer === "memory" ? "缓存结果" : "实时结果";

  return (
    <div className="container pb-16">
      <section className="panel p-5 md:p-6">
        <div className="flex flex-col gap-4">
          <div>
            <p className="eyebrow">Olive Young Search</p>
            <h1 className="mt-2 text-2xl font-semibold md:text-3xl">中文 Olive Young 商品搜索</h1>
            <p className="subtle mt-2 text-sm">页面先打开，再渐进加载 Olive Young 实时数据。</p>
          </div>
          <SearchBar defaultValue={initialKeyword} />
          <div className="grid gap-3 md:grid-cols-4">
            <Stat label="搜索关键词" value={displayKeyword} />
            <Stat label="结果数量" value={isLoading ? "加载中" : `${products.length} 个商品`} />
            <Stat label="数据更新时间" value={formatSyncedAt(primaryMeta?.lastSyncedAt)} />
            <Stat label="当前排序" value={getSortLabel(result?.sort ?? initialSort)} />
          </div>
          <div className="flex flex-col gap-3 rounded-3xl border border-black/10 bg-white/45 p-4 md:flex-row md:items-center md:justify-between">
            <div className="space-y-1">
              <p className="font-semibold">筛选：全部商品 · 有官网价 · 可加入购物车</p>
              <div className="flex flex-wrap gap-2 text-sm">
                <span className="rounded-full bg-white/80 px-3 py-1">{isLoading ? "正在抓取" : resultSourceText}</span>
                <span className="rounded-full bg-white/80 px-3 py-1">{result?.sort ?? initialSort} 排序</span>
                {result?.keywordKo ? <span className="rounded-full bg-white/80 px-3 py-1">韩文回源：{result.keywordKo}</span> : null}
                {fallbackProducts.length ? (
                  <span className="rounded-full bg-amber-100 px-3 py-1 text-amber-900">
                    {fallbackProducts.length} 个备用推荐
                  </span>
                ) : null}
              </div>
            </div>
            <div className="flex flex-wrap gap-2 md:justify-end">
              <SyncCrawlerButton keyword={initialKeyword} sort={result?.sort ?? initialSort} compact />
              {result?.oliveyoungPageUrl ? (
                <a href={result.oliveyoungPageUrl} target="_blank" rel="noreferrer" className="cta ghost">
                  打开 Olive Young 官方页面
                </a>
              ) : null}
            </div>
          </div>
          {primaryMeta ? (
            <details className="rounded-3xl border border-black/10 bg-white/35 px-4 py-3 text-sm">
              <summary className="cursor-pointer font-semibold">数据详情与可信度</summary>
              <div className="mt-3 grid gap-2 text-sm md:grid-cols-3">
                <p><span className="subtle">来源：</span><span className="font-semibold">{getSourceLabel(result?.source ?? "", result?.sourceType ?? "")}</span></p>
                <p><span className="subtle">结果类型：</span><span className="font-semibold">{getSourceTypeLabel(result?.sourceType ?? "")}</span></p>
                <p><span className="subtle">缓存层：</span><span className="font-semibold">{getCacheLayerLabel(primaryMeta.cacheLayer)}</span></p>
                <p><span className="subtle">价格可信度：</span><span className="font-semibold">{formatConfidence(primaryMeta.priceConfidence)}</span></p>
                <p><span className="subtle">翻译可信度：</span><span className="font-semibold">{formatConfidence(primaryMeta.translationConfidence)}</span></p>
              </div>
            </details>
          ) : null}
        </div>
      </section>

      <section className="mt-7">
        <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-2xl font-semibold">
              {initialKeyword ? `"${initialKeyword}" 的 Olive Young 商品` : "Olive Young 商品"}
            </h2>
            <p className="subtle mt-1 text-sm">{isLoading ? "正在后台抓取并整理结果。" : `${products.length} 个主搜索结果。`}</p>
          </div>
        </div>

        {isLoading ? (
          <SearchSkeleton />
        ) : products.length ? (
          <>
            {error ? <p className="mb-4 rounded-2xl bg-amber-50 px-4 py-3 text-sm text-amber-800">{error}</p> : null}
            <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
              {products.map((product, index) => (
                <ProductCard key={product.id} product={product} priority={index < 6} />
              ))}
            </div>
          </>
        ) : (
          <EmptySearchState keyword={initialKeyword} error={error} oliveyoungPageUrl={result?.oliveyoungPageUrl} />
        )}

        {primaryIsFallback ? (
          <p className="mt-4 rounded-2xl bg-amber-50 px-4 py-3 text-sm text-amber-800">
            当前主列表来自备用数据，不代表 Olive Young 当前搜索页。
          </p>
        ) : null}
      </section>

      {!isLoading && fallbackProducts.length ? (
        <section className="mt-10 rounded-[28px] border border-amber-200 bg-amber-50/45 p-5 md:p-6">
          <div className="mb-4 flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="eyebrow">Backup Picks</p>
              <h2 className="mt-2 text-2xl font-semibold">备用推荐</h2>
              <p className="subtle mt-1 text-sm">这些商品不属于当前主搜索结果，仅用于抓取失败或无结果时继续浏览。</p>
            </div>
            <div className="text-sm subtle md:text-right">
              <p>{fallbackProducts.length} 个备用商品</p>
              <p>同步：{formatSyncedAt(fallbackMeta?.lastSyncedAt)}</p>
            </div>
          </div>
          <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
            {fallbackProducts.map((product, index) => (
              <ProductCard key={product.id} product={product} variant="fallback" priority={index < 3} />
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-3xl border border-black/10 bg-white/65 p-4">
      <p className="text-xs subtle">{label}</p>
      <p className="mt-1 text-lg font-semibold">{value}</p>
    </div>
  );
}

function SearchSkeleton() {
  return (
    <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
      {skeletonCards.map((item) => (
        <article key={item} className="panel overflow-hidden">
          <div className="shimmer-block aspect-[4/3]" />
          <div className="space-y-4 p-5">
            <div className="shimmer-line h-4 w-24" />
            <div className="shimmer-line h-7 w-4/5" />
            <div className="shimmer-line h-4 w-full" />
            <div className="shimmer-line h-4 w-2/3" />
            <div className="flex gap-3 pt-2">
              <div className="shimmer-pill h-11 w-24" />
              <div className="shimmer-pill h-11 w-28" />
            </div>
          </div>
        </article>
      ))}
    </div>
  );
}

function EmptySearchState({
  keyword,
  error,
  oliveyoungPageUrl
}: {
  keyword: string;
  error?: string;
  oliveyoungPageUrl?: string | null;
}) {
  return (
    <div className={`panel p-7 ${error ? "border-red-200 bg-red-50/55" : ""}`}>
      <p className="text-xl font-semibold">{error ? "Olive Young 抓取失败" : "没有抓取到 Olive Young 商品"}</p>
      <p className="subtle mt-2">可以刷新结果重试，或打开 Olive Young 官方页面核对。</p>
      {error ? <p className="mt-3 rounded-2xl bg-white/70 px-4 py-3 text-sm text-red-700">错误信息：{error}</p> : null}
      <div className="mt-6 flex flex-wrap gap-3">
        <SyncCrawlerButton keyword={keyword} compact />
        {oliveyoungPageUrl ? (
          <a href={oliveyoungPageUrl} target="_blank" rel="noreferrer" className="cta ghost">
            打开官方页面
          </a>
        ) : null}
      </div>
    </div>
  );
}

function getSortLabel(sort: string) {
  if (sort === "ranking") {
    return "综合排名";
  }
  if (sort === "sale") {
    return "销量优先";
  }
  if (sort === "recent") {
    return "新品优先";
  }
  return sort;
}

function shouldRefreshTranslations(result: ProductSearchResult) {
  const confidence = result.resultMeta.translationConfidence ?? 0;
  return confidence < 0.9 || result.items.some((product) => hasHangul(product.titleZh));
}

function hasHangul(value: string) {
  return /[\u1100-\u11ff\u3130-\u318f\uac00-\ud7af]/.test(value);
}
