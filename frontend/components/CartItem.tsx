import Image from "next/image";
import type { Product } from "@/lib/mock-data";

type Props = {
  cartItemId: string;
  product: Product;
  quantity: number;
  selectedOption: string;
  note: string;
  isRemoving?: boolean;
  onRemove?: (cartItemId: string) => void | Promise<void>;
};

export function CartItem({ cartItemId, product, quantity, selectedOption, note, isRemoving = false, onRemove }: Props) {
  return (
    <div className="panel flex flex-col gap-4 p-4 md:flex-row">
      <div className="relative h-28 w-full overflow-hidden rounded-2xl md:w-28">
        <Image src={product.imageUrl} alt={product.titleZh} fill className="object-cover" />
      </div>
      <div className="flex-1 space-y-2">
        <div>
          <h3 className="text-lg font-semibold">{product.titleZh}</h3>
          <p className="text-sm subtle">{product.titleKo}</p>
        </div>
        <p className="text-sm">规格：{selectedOption}</p>
        <p className="text-sm">数量：{quantity}</p>
        <p className="text-sm subtle">备注：{note}</p>
      </div>
      <div className="flex flex-col justify-between gap-3 md:items-end">
        <p className="text-lg font-bold text-coral">¥{(product.proxyPriceCny * quantity).toFixed(2)}</p>
        <div className="flex gap-2">
          <button className="cta ghost" type="button" disabled>
            暂不支持修改
          </button>
          <button
            className="cta ghost"
            type="button"
            onClick={() => onRemove?.(cartItemId)}
            disabled={isRemoving}
          >
            {isRemoving ? "删除中..." : "删除"}
          </button>
        </div>
      </div>
    </div>
  );
}
