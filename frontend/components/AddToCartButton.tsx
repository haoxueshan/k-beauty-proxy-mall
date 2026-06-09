"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useAuth } from "@/components/AuthProvider";
import { addCartItem } from "@/lib/api";

type Props = {
  productId: string;
  className?: string;
};

export function AddToCartButton({ productId, className = "cta" }: Props) {
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
      await addCartItem(token, { productId, quantity: 1 });
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
        {status === "saving" ? "加入中..." : status === "saved" ? "已加入购物车" : "加入购物车"}
      </button>
      {error ? <p className="text-sm text-red-700">{error}</p> : null}
    </div>
  );
}
