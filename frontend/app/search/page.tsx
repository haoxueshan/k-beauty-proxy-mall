import { ProductCard } from "@/components/ProductCard";
import { SearchBar } from "@/components/SearchBar";
import { SyncCrawlerButton } from "@/components/SyncCrawlerButton";
import { searchProductResults } from "@/lib/api";

export default async function SearchPage({
  searchParams
}: {
  searchParams?: { keyword?: string };
}) {
  const keyword = searchParams?.keyword ?? "";
  const result = await searchProductResults(keyword);
  const products = result.items;
  const sourceLabels: Record<string, string> = {
    "oliveyoung-search": "Olive Young 实时搜索抓取",
    "oliveyoung-main": "Olive Young 首页实时抓取",
    "oliveyoung-search-empty": "Olive Young 实时搜索无结果",
    "oliveyoung-search-error": "Olive Young 实时搜索失败",
    "oliveyoung-live-error": "Olive Young 实时搜索失败",
    "fallback-seed": "备用种子数据"
  };
  const sourceLabel = sourceLabels[result.source] ?? result.source;

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
          <SyncCrawlerButton keyword={keyword} />
          <div className="text-sm subtle md:text-right">
            <p>后端关键词：{result.keywordKo || keyword || "全部商品"}</p>
            <p>当前展示：{result.count} 个结果</p>
            <p>数据来源：{sourceLabel || "未知"}</p>
          </div>
        </div>
        {result.error ? (
          <p className="mt-4 rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-700">
            抓取接口异常：{result.error}
          </p>
        ) : null}
      </section>

      <section className="mt-8">
        <div className="mb-4 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <h2 className="text-2xl font-semibold">
            {keyword ? `“${keyword}” 的搜索结果` : "同步商品"}
          </h2>
          <p className="subtle">{products.length} 个结果</p>
        </div>
        {products.length === 0 ? (
          <div className="panel p-8">
            <p className="text-lg font-semibold">暂时没有匹配商品</p>
            <p className="subtle mt-2">可以换一个关键词，或确认后端服务和 Olive Young 抓取接口是否正常。</p>
          </div>
        ) : (
          <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
            {products.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
