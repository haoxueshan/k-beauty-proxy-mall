import Image from "next/image";
import { AddToCartButton } from "@/components/AddToCartButton";
import type { Product } from "@/lib/mock-data";
import {
  getProductMetadata,
  getProductSpec,
  isFallbackSource
} from "@/lib/product-meta";

type Props = {
  product: Product;
  variant?: "primary" | "fallback";
  priority?: boolean;
};

export function ProductCard({ product, variant = "primary", priority = false }: Props) {
  // 商品卡片面向中文用户：中文标题为主，韩文标题用于核对。
  const metadata = getProductMetadata(product);
  const spec = getProductSpec(product);
  const fallback = variant === "fallback" || isFallbackSource(metadata.sourceType);
  const sourceLabel = getCardSourceLabel(metadata.sourceType, fallback);
  const title = getDisplayTitle(product);

  return (
    <article className="overflow-hidden rounded-[28px] border border-black/10 bg-white shadow-[0_18px_44px_rgba(29,28,26,0.10)] transition duration-200 hover:-translate-y-1 hover:shadow-[0_24px_54px_rgba(29,28,26,0.14)]">
      <div className="relative aspect-[4/3]">
        <Image
          src={product.imageUrl}
          alt={title.zh}
          fill
          sizes="(min-width: 1280px) 33vw, (min-width: 768px) 50vw, 100vw"
          className="object-cover"
          unoptimized
          priority={priority}
          loading={priority ? undefined : "lazy"}
        />
        <div className="absolute left-4 top-4 flex flex-wrap gap-2">
          <span className="rounded-full bg-white/95 px-3 py-1 text-xs font-semibold shadow-sm">{sourceLabel}</span>
          <span className="rounded-full bg-coral/90 px-3 py-1 text-xs font-semibold text-white shadow-sm">
            {product.categoryZh}
          </span>
          {fallback ? (
            <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-900 shadow-sm">
              澶囩敤鎺ㄨ崘
            </span>
          ) : null}
        </div>
      </div>

      <div className="space-y-4 p-5">
        <div className="space-y-2">
          <h3 className="text-sm font-semibold leading-relaxed text-black/85">{title.zh}</h3>
          {title.ko ? <p className="text-xs leading-relaxed text-black/45">{title.ko}</p> : null}
          <p className="text-sm">
            <span className="subtle">品牌：</span>
            <span className="font-semibold">{product.brandZh || product.brandKo}</span>
            {product.brandKo && product.brandKo !== product.brandZh ? (
              <span className="subtle"> / {product.brandKo}</span>
            ) : null}
          </p>
        </div>

        <div className="grid gap-2 rounded-2xl border border-black/10 bg-[#fffaf3] p-3 text-xs md:grid-cols-2">
          <p>
            <span className="subtle">Olive Young 排名：</span>
            <span className="font-semibold">
              {!fallback && metadata.sourceRank ? `第 ${metadata.sourceRank} 位` : fallback ? "备用推荐" : "待确认"}
            </span>
          </p>
          <p>
            <span className="subtle">规格：</span>
            <span className="font-semibold">{spec ?? "待确认"}</span>
          </p>
        </div>

        <div className="rounded-3xl bg-[#fff8ef] p-4">
          <div>
            <p className="text-xs subtle">人民币参考价</p>
            <p className="text-2xl font-bold text-coral">¥{product.priceCny.toFixed(2)}</p>
          </div>
          <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm">
            <p className="font-semibold">韩元官网价 KRW {product.salePriceKrw.toLocaleString()}</p>
            {product.originalPriceKrw > product.salePriceKrw ? (
              <p className="line-through subtle">原价 KRW {product.originalPriceKrw.toLocaleString()}</p>
            ) : null}
          </div>
        </div>

        <div className="grid gap-2 sm:grid-cols-[1.2fr_1fr]">
          <AddToCartButton product={product} className="cta w-full" />
          {product.sourceUrl ? (
            <a href={product.sourceUrl} target="_blank" rel="noreferrer" className="cta ghost w-full">
              官方链接
            </a>
          ) : null}
        </div>
      </div>
    </article>
  );
}

function getCardSourceLabel(sourceType?: string, fallback = false) {
  // 用用户能理解的来源标签，避免直接暴露技术字段。
  if (fallback) {
    return "备用推荐";
  }
  if (sourceType === "cache") {
    return "缓存";
  }
  return "实时结果";
}

function getDisplayTitle(product: Product) {
  const titleZh = product.titleZh?.trim();
  const titleKo = product.titleKo?.trim();

  return {
    zh: titleZh || "翻译中",
    ko: titleKo || null
  };
}
