import Image from "next/image";
import Link from "next/link";
import { AddToCartButton } from "@/components/AddToCartButton";
import type { Product } from "@/lib/mock-data";

export function ProductCard({ product }: { product: Product }) {
  return (
    <article className="panel overflow-hidden">
      <div className="relative aspect-[4/3]">
        <Image src={product.imageUrl} alt={product.titleZh} fill className="object-cover" />
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
        <div className="flex items-end justify-between gap-4">
          <div>
            <p className="text-sm line-through subtle">KRW {product.originalPriceKrw.toLocaleString()}</p>
            <p className="text-lg font-bold text-coral">代购参考价 ¥{product.proxyPriceCny.toFixed(2)}</p>
          </div>
          <p className="text-sm subtle">韩元价 KRW {product.salePriceKrw.toLocaleString()}</p>
        </div>
        <div className="flex gap-3">
          <Link href={`/products/${product.id}`} className="cta ghost">
            查看详情
          </Link>
          <AddToCartButton productId={product.id} />
        </div>
      </div>
    </article>
  );
}
