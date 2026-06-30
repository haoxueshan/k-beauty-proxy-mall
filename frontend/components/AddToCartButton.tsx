"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useAuth } from "@/components/AuthProvider";
import { addCartItem } from "@/lib/api";
import type { Product } from "@/lib/mock-data";

type Props = {
  product: Product;
  className?: string;
};

export function AddToCartButton({ product, className = "cta" }: Props) {
  const router = useRouter();
  const { token, isAuthenticated } = useAuth();
  const [status, setStatus] = useState<"idle" | "saving" | "saved">("idle");
  const [error, setError] = useState("");

  async function handleAdd() {
    if (!isAuthenticated || !token) {
      router.push("/login");
      return;
    }

    setError("");
    setStatus("saving");
    try {
      await addCartItem(token, {
        productId: product.id,
        sourceUrl: product.sourceUrl,
        titleZh: product.titleZh,
        titleKo: product.titleKo,
        imageUrl: product.imageUrl,
        salePriceKrw: product.salePriceKrw,
        priceCny: product.priceCny,
        brandKo: product.brandKo,
        quantity: 1
      });
      setStatus("saved");
      router.refresh();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "加入购物车失败");
      setStatus("idle");
      return;
    }

    window.setTimeout(() => {
      setStatus("idle");
    }, 1800);
  }

  return (
    <div className="space-y-2">
      <button type="button" className={className} onClick={handleAdd} disabled={status === "saving"}>
        {status === "saving" ? "正在加入..." : status === "saved" ? "已加入购物车" : "加入购物车"}
      </button>
      {error ? <p className="text-sm text-red-700">{error}</p> : null}
    </div>
  );
}
