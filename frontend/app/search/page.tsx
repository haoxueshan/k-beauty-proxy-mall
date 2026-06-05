import { ProductCard } from "@/components/ProductCard";
import { SearchBar } from "@/components/SearchBar";
import { searchProducts } from "@/lib/api";

export default async function SearchPage({
  searchParams
}: {
  searchParams?: { keyword?: string };
}) {
  const keyword = searchParams?.keyword ?? "";
  const products = await searchProducts(keyword);

  return (
    <div className="container pb-16">
      <section className="panel p-6 md:p-8">
        <p className="eyebrow">Search</p>
        <h1 className="mt-3 text-3xl font-semibold">搜索 Olive Young 商品</h1>
        <p className="subtle mt-2">支持中文关键词作为入口，当前优先演示本地 mock + 后端 API 结构。</p>
        <div className="mt-6">
          <SearchBar defaultValue={keyword} />
        </div>
      </section>

      <section className="mt-8">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-2xl font-semibold">{keyword ? `“${keyword}” 的搜索结果` : "推荐商品"}</h2>
          <p className="subtle">{products.length} 个结果</p>
        </div>
        <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
          {products.map((product) => (
            <ProductCard key={product.id} product={product} />
          ))}
        </div>
      </section>
    </div>
  );
}
