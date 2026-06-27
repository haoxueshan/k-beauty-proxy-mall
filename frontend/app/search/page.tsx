import { ProductCard } from "@/components/ProductCard";
import { SearchBar } from "@/components/SearchBar";
import { SyncCrawlerButton } from "@/components/SyncCrawlerButton";
import { searchProductResults } from "@/lib/api";
import {
  formatConfidence,
  formatSyncedAt,
  getCacheLayerLabel,
  getSourceLabel,
  getSourceTypeLabel,
  isFallbackSource
} from "@/lib/product-meta";

export default async function SearchPage({
  searchParams
}: {
  searchParams?: { keyword?: string; sort?: string };
}) {
  // 搜索页是服务端组件：首屏直接等待后端搜索结果，避免客户端二次闪烁加载。
  const keyword = searchParams?.keyword ?? "";
  const sort = searchParams?.sort || "ranking";
  const result = await searchProductResults(keyword, { sort });
  const products = result.items;
  const fallbackProducts = result.fallbackItems;
  const primaryMeta = result.resultMeta;
  const fallbackMeta = result.fallbackMeta;
  // 主搜索结果和备用推荐分区展示，备用推荐不计入主结果数量。
  const hasFallbackRecommendations = fallbackProducts.length > 0;
  const primaryIsFallback = isFallbackSource(result.sourceType);
  const hasPrimaryResults = products.length > 0;
  const displayKeyword = result.keywordOriginal || keyword || "全部商品";
  const resultSourceText = primaryMeta.cacheLayer === "memory" ? "缓存结果" : "实时结果";
  const syncedAtText = formatSyncedAt(primaryMeta.lastSyncedAt);

  return (
    <div className="container pb-16">
      <section className="panel p-5 md:p-6">
        <div className="flex flex-col gap-4">
          <div>
            <p className="eyebrow">Olive Young Search</p>
            <h1 className="mt-2 text-2xl font-semibold md:text-3xl">中文 Olive Young 商品搜索</h1>
            <p className="subtle mt-2 text-sm">输入中文关键词，优先展示中文商品名、人民币参考价和官网韩元价。</p>
          </div>
          <SearchBar defaultValue={keyword} />
          <div className="grid gap-3 md:grid-cols-4">
            <div className="rounded-3xl border border-black/10 bg-white/65 p-4">
              <p className="text-xs subtle">搜索关键词</p>
              <p className="mt-1 text-lg font-semibold">{displayKeyword}</p>
            </div>
            <div className="rounded-3xl border border-black/10 bg-white/65 p-4">
              <p className="text-xs subtle">结果数量</p>
              <p className="mt-1 text-lg font-semibold">{products.length} 个商品</p>
            </div>
            <div className="rounded-3xl border border-black/10 bg-white/65 p-4">
              <p className="text-xs subtle">数据更新时间</p>
              <p className="mt-1 text-lg font-semibold">{syncedAtText}</p>
            </div>
            <div className="rounded-3xl border border-black/10 bg-white/65 p-4">
              <p className="text-xs subtle">当前排序</p>
              <p className="mt-1 text-lg font-semibold">{getSortLabel(result.sort)}</p>
            </div>
          </div>
          <div className="flex flex-col gap-3 rounded-3xl border border-black/10 bg-white/45 p-4 md:flex-row md:items-center md:justify-between">
            <div className="space-y-1">
              <p className="font-semibold">筛选：全部商品 · 有官网价 · 可加入购物车</p>
              <div className="flex flex-wrap gap-2 text-sm">
                <span className="rounded-full bg-white/80 px-3 py-1">{resultSourceText}</span>
                <span className="rounded-full bg-white/80 px-3 py-1">{result.sort} 排序</span>
                {result.keywordKo ? <span className="rounded-full bg-white/80 px-3 py-1">韩文回源：{result.keywordKo}</span> : null}
                {hasFallbackRecommendations ? (
                  <span className="rounded-full bg-amber-100 px-3 py-1 text-amber-900">
                    {result.fallbackCount} 个备用推荐
                  </span>
                ) : null}
              </div>
            </div>
            <div className="flex flex-wrap gap-2 md:justify-end">
              <SyncCrawlerButton keyword={keyword} sort={result.sort} compact />
              {result.oliveyoungPageUrl ? (
                <a href={result.oliveyoungPageUrl} target="_blank" rel="noreferrer" className="cta ghost">
                  打开 Olive Young 官方页面
                </a>
              ) : null}
            </div>
          </div>
          <details className="rounded-3xl border border-black/10 bg-white/35 px-4 py-3 text-sm">
            <summary className="cursor-pointer font-semibold">数据详情与可信度</summary>
            <div className="mt-3 grid gap-2 text-sm md:grid-cols-3">
              <p>
                <span className="subtle">来源：</span>
                <span className="font-semibold">{getSourceLabel(result.source, result.sourceType)}</span>
              </p>
              <p>
                <span className="subtle">结果类型：</span>
                <span className="font-semibold">{getSourceTypeLabel(result.sourceType)}</span>
              </p>
              <p>
                <span className="subtle">缓存层：</span>
                <span className="font-semibold">{getCacheLayerLabel(primaryMeta.cacheLayer)}</span>
              </p>
              <p>
                <span className="subtle">价格可信度：</span>
                <span className="font-semibold">{formatConfidence(primaryMeta.priceConfidence)}</span>
              </p>
              <p>
                <span className="subtle">翻译可信度：</span>
                <span className="font-semibold">{formatConfidence(primaryMeta.translationConfidence)}</span>
              </p>
            </div>
          </details>
        </div>
      </section>

      <section className="mt-7">
        <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-2xl font-semibold">
              {keyword ? `“${keyword}” 的 Olive Young 商品` : "Olive Young 商品"}
            </h2>
            <p className="subtle mt-1 text-sm">{products.length} 个主搜索结果，备用推荐不计入这里。</p>
          </div>
        </div>

        {hasPrimaryResults ? (
          <>
            {result.error ? (
              <p className="mb-4 rounded-2xl bg-amber-50 px-4 py-3 text-sm text-amber-800">{result.error}</p>
            ) : null}
            <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
              {products.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
          </>
        ) : (
          <EmptySearchState
            keyword={keyword}
            error={result.error}
            oliveyoungPageUrl={result.oliveyoungPageUrl}
          />
        )}

        {primaryIsFallback ? (
          <p className="mt-4 rounded-2xl bg-amber-50 px-4 py-3 text-sm text-amber-800">
            当前主列表来自备用数据，不代表 Olive Young 当前页面的实时搜索结果。
          </p>
        ) : null}
      </section>

      {hasFallbackRecommendations ? (
        <section className="mt-10 rounded-[28px] border border-amber-200 bg-amber-50/45 p-5 md:p-6">
          <div className="mb-4 flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="eyebrow">Backup Picks</p>
              <h2 className="mt-2 text-2xl font-semibold">备用推荐</h2>
              <p className="subtle mt-1 text-sm">
                这些商品不属于当前 Olive Young 搜索结果，仅用于搜索失败或无结果时继续浏览。
              </p>
            </div>
            <div className="text-sm subtle md:text-right">
              <p>{fallbackProducts.length} 个备用商品</p>
              <p>同步：{formatSyncedAt(fallbackMeta?.lastSyncedAt)}</p>
            </div>
          </div>
          <div className="mb-5 rounded-2xl border border-amber-200 bg-white/65 px-4 py-3 text-sm text-amber-900">
            备用推荐不参与主搜索结果计数。下单前请打开官方链接重新确认价格、库存和规格。
          </div>
          <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
            {fallbackProducts.map((product) => (
              <ProductCard key={product.id} product={product} variant="fallback" />
            ))}
          </div>
        </section>
      ) : null}
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
  // 空状态用用户语言提示下一步操作，而不是只展示后端错误或 0 条结果。
  const title = error ? "Olive Young 抓取失败" : "没有抓取到 Olive Young 商品";
  const description = error
    ? "可以刷新结果重试，或先查看下方备用推荐。"
    : "你可以刷新结果，或打开 Olive Young 官方页面核对。";

  return (
    <div className={`panel p-7 ${error ? "border-red-200 bg-red-50/55" : ""}`}>
      <p className="text-xl font-semibold">{title}</p>
      <p className="subtle mt-2">{description}</p>
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
