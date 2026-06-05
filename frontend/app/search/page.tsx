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

  return (
    <div className="container pb-16">
      <section className="panel p-6 md:p-8">
        <p className="eyebrow">Live Search</p>
        <h1 className="mt-3 text-3xl font-semibold">搜索 Olive Young 商品</h1>
        <p className="subtle mt-2">
          搜索会读取后端同步的 Olive Young 首页商品；需要最新数据时，可以先手动同步再查看结果。
        </p>
        <div className="mt-6">
          <SearchBar defaultValue={keyword} />
        </div>
        <div className="mt-5 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <SyncCrawlerButton keyword={keyword} />
          <div className="text-sm subtle md:text-right">
            <p>后端关键词：{result.keywordKo || keyword || "全部商品"}</p>
            <p>当前展示：{result.count} 个结果</p>
          </div>
        </div>
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
            <p className="subtle mt-2">可以换一个关键词，或点击上方按钮同步最新 Olive Young 首页数据。</p>
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
