import Link from "next/link";
import { AddToCartButton } from "@/components/AddToCartButton";
import { getProduct } from "@/lib/api";

export default async function ProductDetailPage({ params }: { params: { id: string } }) {
  const product = await getProduct(params.id);

  if (!product) {
    return (
      <div className="container pb-16">
        <div className="panel p-8">
          <h1 className="text-2xl font-semibold">商品不存在</h1>
          <p className="subtle mt-2">请返回搜索页重新同步或选择其他商品。</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container pb-16">
      <section className="grid gap-8 md:grid-cols-[1fr_1.05fr]">
        <div
          className="panel min-h-[420px] bg-cover bg-center"
          style={{ backgroundImage: `url(${product.imageUrl})` }}
        />
        <div className="panel p-8">
          <p className="eyebrow">{product.categoryZh}</p>
          <h1 className="mt-3 text-4xl font-semibold">{product.titleZh}</h1>
          <p className="subtle mt-3 text-lg">{product.titleKo}</p>
          <p className="mt-2 text-sm subtle">
            品牌：{product.brandZh} / {product.brandKo}
          </p>

          <div className="mt-8 grid gap-4 rounded-3xl border border-black/10 bg-white/60 p-5 md:grid-cols-2">
            <div>
              <p className="text-sm subtle">韩元折扣价</p>
              <p className="text-2xl font-bold">KRW {product.salePriceKrw.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-sm subtle">代购参考价</p>
              <p className="text-2xl font-bold text-coral">¥{product.proxyPriceCny.toFixed(2)}</p>
            </div>
          </div>

          <div className="mt-8 space-y-4">
            <div>
              <h2 className="text-lg font-semibold">商品摘要</h2>
              <p className="subtle mt-2 leading-7">{product.aiSummary}</p>
            </div>
            <div>
              <h2 className="text-lg font-semibold">购买提示</h2>
              <ul className="mt-2 space-y-2 subtle">
                {product.riskTips.map((tip) => (
                  <li key={tip}>{tip}</li>
                ))}
              </ul>
            </div>
          </div>

          <div className="mt-8 flex flex-wrap gap-3">
            <AddToCartButton productId={product.id} />
            <Link href="/cart" className="cta ghost">
              查看购物车
            </Link>
            <a href={product.sourceUrl} target="_blank" className="cta ghost" rel="noreferrer">
              查看原链接
            </a>
          </div>
        </div>
      </section>
    </div>
  );
}
