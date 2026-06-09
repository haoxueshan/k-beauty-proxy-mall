import Link from "next/link";
import { AddToCartButton } from "@/components/AddToCartButton";
import { getProduct } from "@/lib/api";
import {
  formatConfidence,
  formatSyncedAt,
  getConfidenceStatus,
  getProductMetadata,
  getProductSpec,
  getSourceTypeLabel
} from "@/lib/product-meta";

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

  const metadata = getProductMetadata(product);
  const spec = getProductSpec(product);
  const pendingChecks = [
    spec ? null : "规格/容量需要按原站详情再次确认",
    metadata.lastSyncedAt ? null : "最近同步时间待确认",
    metadata.priceConfidence && metadata.priceConfidence >= 0.85 ? null : "价格可信度未达到高，需要下单前复核",
    product.sourceUrl ? null : "原站链接待确认",
    "库存、限购、活动券和最终国际物流费用待人工确认"
  ].filter((item): item is string => Boolean(item));

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

          <div className="mt-6 grid gap-3 rounded-3xl border border-black/10 bg-white/60 p-5 text-sm md:grid-cols-2">
            <p>
              <span className="subtle">数据来源：</span>
              <span className="font-semibold">{getSourceTypeLabel(metadata.sourceType)}</span>
            </p>
            <p>
              <span className="subtle">最新同步：</span>
              <span className="font-semibold">{formatSyncedAt(metadata.lastSyncedAt)}</span>
            </p>
            <p>
              <span className="subtle">规格/容量：</span>
              <span className="font-semibold">{spec ?? "待确认"}</span>
            </p>
            <p>
              <span className="subtle">翻译可信度：</span>
              <span className="font-semibold">{formatConfidence(metadata.translationConfidence)}</span>
            </p>
          </div>

          <div className="mt-5 grid gap-4 rounded-3xl border border-black/10 bg-white/60 p-5 md:grid-cols-2">
            <div>
              <p className="text-sm subtle">韩元售价</p>
              <p className="text-2xl font-bold">KRW {product.salePriceKrw.toLocaleString()}</p>
              <p className="mt-1 text-sm line-through subtle">原价 KRW {product.originalPriceKrw.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-sm subtle">人民币参考价</p>
              <p className="text-2xl font-bold text-coral">¥{product.priceCny.toFixed(2)}</p>
              <p className="mt-1 text-sm subtle">按当前汇率折算，仅供参考</p>
            </div>
            <div>
              <p className="text-sm subtle">价格口径</p>
              <p className="text-xl font-semibold">¥{product.priceCny.toFixed(2)}</p>
            </div>
            <div>
              <p className="text-sm subtle">价格可信度</p>
              <p className="text-xl font-semibold">
                {getConfidenceStatus(metadata.priceConfidence)} · {formatConfidence(metadata.priceConfidence)}
              </p>
            </div>
          </div>

          <div className="mt-8 space-y-4">
            <div>
              <h2 className="text-lg font-semibold">原站与下单判断</h2>
              <div className="mt-3 rounded-3xl border border-black/10 bg-white/50 p-4 text-sm">
                {product.sourceUrl ? (
                  <a
                    href={product.sourceUrl}
                    target="_blank"
                    className="font-semibold text-coral underline underline-offset-4"
                    rel="noreferrer"
                  >
                    打开 Olive Young 原站链接
                  </a>
                ) : (
                  <p className="font-semibold">原站链接待确认</p>
                )}
                <p className="subtle mt-2">
                  建议下单前核对原站价格、规格、库存和活动条件；当前页面用于商品价格初筛。
                </p>
              </div>
            </div>
            <div>
              <h2 className="text-lg font-semibold">商品摘要</h2>
              <p className="subtle mt-2 leading-7">{product.aiSummary || "待确认"}</p>
            </div>
            <div>
              <h2 className="text-lg font-semibold">风险提示 / 待确认信息</h2>
              <ul className="mt-2 space-y-2 subtle">
                {pendingChecks.map((tip) => (
                  <li key={tip}>{tip}</li>
                ))}
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
