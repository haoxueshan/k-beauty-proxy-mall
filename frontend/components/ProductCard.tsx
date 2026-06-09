import Image from "next/image";
import Link from "next/link";
import { AddToCartButton } from "@/components/AddToCartButton";
import type { Product } from "@/lib/mock-data";
import {
  formatConfidence,
  formatSyncedAt,
  getConfidenceStatus,
  getProductMetadata,
  getProductSpec,
  getSourceTypeLabel,
  isFallbackSource
} from "@/lib/product-meta";

export function ProductCard({ product }: { product: Product }) {
  const metadata = getProductMetadata(product);
  const spec = getProductSpec(product);
  const sourceLabel = getSourceTypeLabel(metadata.sourceType);
  const fallback = isFallbackSource(metadata.sourceType);
  const priceConfidence = metadata.priceConfidence;

  return (
    <article className="panel overflow-hidden">
      <div className="relative aspect-[4/3]">
        <Image src={product.imageUrl} alt={product.titleZh} fill className="object-cover" />
        <div className="absolute left-4 top-4 rounded-full bg-white/90 px-3 py-1 text-xs font-semibold shadow-sm">
          {fallback ? "Fallback 推荐" : sourceLabel}
        </div>
      </div>
      <div className="space-y-4 p-5">
        <div className="space-y-2">
          <p className="eyebrow">{product.categoryZh}</p>
          <h3 className="text-xl font-semibold">{product.titleZh}</h3>
          <p className="text-sm subtle">{product.titleKo}</p>
          <p className="text-sm subtle">
            {product.brandZh} / {product.brandKo}
          </p>
        </div>
        <div className="grid gap-2 rounded-2xl border border-black/10 bg-white/55 p-3 text-xs md:grid-cols-2">
          <p>
            <span className="subtle">来源：</span>
            <span className="font-semibold">{sourceLabel}</span>
          </p>
          <p>
            <span className="subtle">同步：</span>
            <span className="font-semibold">{formatSyncedAt(metadata.lastSyncedAt)}</span>
          </p>
          <p>
            <span className="subtle">价格可信度：</span>
            <span className="font-semibold">
              {getConfidenceStatus(priceConfidence)} · {formatConfidence(priceConfidence)}
            </span>
          </p>
          <p>
            <span className="subtle">规格：</span>
            <span className="font-semibold">{spec ?? "待确认"}</span>
          </p>
          <p>
            <span className="subtle">源站页：</span>
            <span className="font-semibold">{metadata.sourcePage ? `第 ${metadata.sourcePage} 页` : "待确认"}</span>
          </p>
          <p>
            <span className="subtle">源站排名：</span>
            <span className="font-semibold">{metadata.sourceRank ? `#${metadata.sourceRank}` : "待确认"}</span>
          </p>
        </div>
        <div className="flex items-end justify-between gap-4">
          <div>
            <p className="text-sm line-through subtle">KRW {product.originalPriceKrw.toLocaleString()}</p>
            <p className="text-lg font-bold text-coral">人民币参考价 ¥{product.priceCny.toFixed(2)}</p>
          </div>
          <p className="text-sm subtle">Olive Young 售价 KRW {product.salePriceKrw.toLocaleString()}</p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Link href={`/products/${product.id}`} className="cta ghost">
            查看详情
          </Link>
          <AddToCartButton productId={product.id} />
        </div>
      </div>
    </article>
  );
}
