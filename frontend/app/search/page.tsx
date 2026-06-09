import { ProductCard } from "@/components/ProductCard";
import { SearchBar } from "@/components/SearchBar";
import { SyncCrawlerButton } from "@/components/SyncCrawlerButton";
import { searchProductResults } from "@/lib/api";
import {
  formatConfidence,
  formatSyncedAt,
  getCacheLayerLabel,
  getConfidenceStatus,
  getSourceLabel,
  getSourceTypeLabel,
  isFallbackSource
} from "@/lib/product-meta";

export default async function SearchPage({
  searchParams
}: {
  searchParams?: { keyword?: string; page?: string; page_size?: string; sort?: string };
}) {
  const keyword = searchParams?.keyword ?? "";
  const page = Math.max(Number(searchParams?.page ?? 1) || 1, 1);
  const pageSize = Math.min(Math.max(Number(searchParams?.page_size ?? 24) || 24, 1), 60);
  const sort = searchParams?.sort || "ranking";
  const result = await searchProductResults(keyword, { page, pageSize, sort });
  const products = result.items;
  const fallbackProducts = result.fallbackItems;
  const primaryMeta = result.resultMeta;
  const fallbackMeta = result.fallbackMeta;
  const sourceLabel = getSourceLabel(result.source, result.sourceType);
  const sourceTypeLabel = getSourceTypeLabel(result.sourceType);
  const hasFallbackRecommendations = fallbackProducts.length > 0;
  const primaryIsFallback = isFallbackSource(result.sourceType);
  const previousPageHref = buildSearchHref(keyword, Math.max(result.page - 1, 1), result.pageSize, result.sort);
  const nextPageHref = buildSearchHref(keyword, result.nextPage ?? result.page + 1, result.pageSize, result.sort);

  return (
    <div className="container pb-16">
      <section className="panel p-6 md:p-8">
        <p className="eyebrow">Live Search</p>
        <h1 className="mt-3 text-3xl font-semibold">搜索 Olive Young 商品</h1>
        <p className="subtle mt-2">
          搜索会实时调用后端 Olive Young 抓取模块，并把抓取到的商品直接展示在页面。
        </p>
        <div className="mt-6">
          <SearchBar defaultValue={keyword} />
        </div>
        <div className="mt-5 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <SyncCrawlerButton keyword={keyword} page={result.page} pageSize={result.pageSize} sort={result.sort} />
          <div className="grid gap-2 text-sm md:min-w-[360px] md:grid-cols-2 md:text-right">
            <p className="rounded-2xl border border-black/10 bg-white/50 px-3 py-2">
              <span className="subtle">原始关键词：</span>
              <span className="font-semibold">{result.keywordOriginal || keyword || "全部商品"}</span>
            </p>
            <p className="rounded-2xl border border-black/10 bg-white/50 px-3 py-2">
              <span className="subtle">回源韩文：</span>
              <span className="font-semibold">{result.keywordKo || "待确认"}</span>
            </p>
            <p className="rounded-2xl border border-black/10 bg-white/50 px-3 py-2">
              <span className="subtle">来源：</span>
              <span className="font-semibold">{sourceLabel}</span>
            </p>
            <p className="rounded-2xl border border-black/10 bg-white/50 px-3 py-2">
              <span className="subtle">类型：</span>
              <span className="font-semibold">{sourceTypeLabel}</span>
            </p>
            <p className="rounded-2xl border border-black/10 bg-white/50 px-3 py-2">
              <span className="subtle">缓存层：</span>
              <span className="font-semibold">{getCacheLayerLabel(primaryMeta.cacheLayer)}</span>
            </p>
            <p className="rounded-2xl border border-black/10 bg-white/50 px-3 py-2">
              <span className="subtle">最近同步：</span>
              <span className="font-semibold">{formatSyncedAt(primaryMeta.lastSyncedAt)}</span>
            </p>
            <p className="rounded-2xl border border-black/10 bg-white/50 px-3 py-2">
              <span className="subtle">原站页码：</span>
              <span className="font-semibold">第 {result.page} 页</span>
            </p>
            <p className="rounded-2xl border border-black/10 bg-white/50 px-3 py-2">
              <span className="subtle">排序：</span>
              <span className="font-semibold">{result.sort}</span>
            </p>
          </div>
        </div>
        <div className="mt-5 grid gap-3 rounded-3xl border border-black/10 bg-white/45 p-4 text-sm md:grid-cols-4">
          <p>
            <span className="subtle">主结果：</span>
            <span className="font-semibold">{products.length} 个</span>
          </p>
          <p>
            <span className="subtle">fallback 推荐：</span>
            <span className="font-semibold">
              {hasFallbackRecommendations ? `${result.fallbackCount} 个，独立展示` : "无"}
            </span>
          </p>
          <p>
            <span className="subtle">价格可信度：</span>
            <span className="font-semibold">
              {getConfidenceStatus(primaryMeta.priceConfidence)} · {formatConfidence(primaryMeta.priceConfidence)}
            </span>
          </p>
          <p>
            <span className="subtle">翻译可信度：</span>
            <span className="font-semibold">{formatConfidence(primaryMeta.translationConfidence)}</span>
          </p>
          <p>
            <span className="subtle">源站排名：</span>
            <span className="font-semibold">{result.sourceRankStart ? `#${result.sourceRankStart} 起` : "待确认"}</span>
          </p>
          <p>
            <span className="subtle">已同步页：</span>
            <span className="font-semibold">{result.syncedPages.length ? result.syncedPages.join(", ") : "待确认"}</span>
          </p>
          <p className="md:col-span-2">
            <span className="subtle">原站对照：</span>
            {result.oliveyoungPageUrl ? (
              <a
                href={result.oliveyoungPageUrl}
                target="_blank"
                className="font-semibold text-coral underline underline-offset-4"
                rel="noreferrer"
              >
                打开 Olive Young 第 {result.page} 页
              </a>
            ) : (
              <span className="font-semibold">待确认</span>
            )}
          </p>
        </div>
        {primaryIsFallback ? (
          <p className="mt-4 rounded-2xl bg-amber-50 px-4 py-3 text-sm text-amber-800">
            当前主列表来自 fallback/seed 数据，不代表 Olive Young 实时搜索结果。
          </p>
        ) : null}
        {result.error ? (
          <p className="mt-4 rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-700">
            抓取接口异常：{result.error}
          </p>
        ) : null}
      </section>

      <section className="mt-8">
        <div className="mb-4 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <h2 className="text-2xl font-semibold">
            {keyword ? `“${keyword}” 的${sourceTypeLabel}结果` : "同步商品"}
          </h2>
          <div className="flex flex-wrap items-center gap-3 text-sm">
            <p className="subtle">第 {result.page} 页 · {products.length} 个主结果</p>
            {result.page > 1 ? (
              <a href={previousPageHref} className="cta ghost min-h-0 px-4 py-2">
                上一页
              </a>
            ) : null}
            {result.hasNext ? (
              <a href={nextPageHref} className="cta ghost min-h-0 px-4 py-2">
                下一页
              </a>
            ) : null}
          </div>
        </div>
        {products.length === 0 && !hasFallbackRecommendations ? (
          <div className="panel p-8">
            <p className="text-lg font-semibold">暂时没有匹配商品</p>
            <p className="subtle mt-2">可以换一个关键词，或确认后端服务和 Olive Young 抓取接口是否正常。</p>
          </div>
        ) : products.length > 0 ? (
          <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
            {products.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        ) : (
          <div className="panel p-8">
            <p className="text-lg font-semibold">实时/缓存搜索暂时没有匹配商品</p>
            <p className="subtle mt-2">下面单独展示 fallback 推荐，不会计入主搜索结果。</p>
          </div>
        )}
      </section>

      {hasFallbackRecommendations ? (
        <section className="mt-10">
          <div className="mb-4 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="eyebrow">Fallback Recommendations</p>
              <h2 className="mt-2 text-2xl font-semibold">备选推荐数据</h2>
            </div>
            <div className="text-sm subtle md:text-right">
              <p>来源：{getSourceLabel(fallbackMeta?.source, fallbackMeta?.sourceType)}</p>
              <p>同步：{formatSyncedAt(fallbackMeta?.lastSyncedAt)}</p>
              <p>说明：非当前关键词实时搜索结果</p>
            </div>
          </div>
          <div className="mb-4 rounded-2xl border border-amber-200 bg-amber-50/70 px-4 py-3 text-sm text-amber-900">
            主搜索没有稳定返回时才展示这些推荐。它们可用于继续浏览或测试加购，但需要在下单前重新确认原站价格、库存和规格。
          </div>
          <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
            {fallbackProducts.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}

function buildSearchHref(keyword: string, page: number, pageSize: number, sort: string) {
  const params = new URLSearchParams();
  if (keyword) {
    params.set("keyword", keyword);
  }
  params.set("page", String(page));
  params.set("page_size", String(pageSize));
  params.set("sort", sort);
  return `/search?${params.toString()}`;
}
