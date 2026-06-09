"use client";

import Image from "next/image";
import { useEffect, useState } from "react";
import type { Product } from "@/lib/mock-data";

type Props = {
  cartItemId: string;
  product: Product;
  quantity: number;
  selectedOption: string;
  note: string;
  isRemoving?: boolean;
  isSaving?: boolean;
  onSave?: (cartItemId: string, payload: { quantity: number; note: string }) => void | Promise<void>;
  onRemove?: (cartItemId: string) => void | Promise<void>;
};

export function CartItem({
  cartItemId,
  product,
  quantity,
  selectedOption,
  note,
  isRemoving = false,
  isSaving = false,
  onSave,
  onRemove
}: Props) {
  const [draftQuantity, setDraftQuantity] = useState(String(quantity));
  const [draftNote, setDraftNote] = useState(note);

  useEffect(() => {
    setDraftQuantity(String(quantity));
  }, [quantity]);

  useEffect(() => {
    setDraftNote(note);
  }, [note]);

  const parsedQuantity = Number(draftQuantity);
  const normalizedQuantity = Number.isFinite(parsedQuantity) && parsedQuantity > 0 ? Math.floor(parsedQuantity) : 0;
  const normalizedNote = draftNote.trim();
  const hasChanges = normalizedQuantity !== quantity || normalizedNote !== note;
  const canSave = hasChanges && normalizedQuantity >= 1 && !isSaving && !isRemoving;

  async function handleSave() {
    if (!canSave) {
      return;
    }
    await onSave?.(cartItemId, {
      quantity: normalizedQuantity,
      note: normalizedNote
    });
  }

  return (
    <div className="panel flex flex-col gap-4 p-4 md:flex-row">
      <div className="relative h-28 w-full overflow-hidden rounded-2xl md:w-28">
        <Image src={product.imageUrl} alt={product.titleZh} fill className="object-cover" />
      </div>
      <div className="flex-1 space-y-3">
        <div>
          <h3 className="text-lg font-semibold">{product.titleZh}</h3>
          <p className="text-sm subtle">{product.titleKo}</p>
        </div>
        <p className="text-sm">规格：{selectedOption}</p>
        <div className="grid gap-3 md:grid-cols-[120px_1fr]">
          <label className="space-y-2 text-sm">
            <span className="subtle">数量</span>
            <input
              type="number"
              min={1}
              step={1}
              value={draftQuantity}
              onChange={(event) => setDraftQuantity(event.target.value)}
              className="min-h-[46px] w-full rounded-2xl border border-black/10 bg-white/80 px-4 outline-none"
            />
          </label>
          <label className="space-y-2 text-sm">
            <span className="subtle">备注</span>
            <textarea
              value={draftNote}
              onChange={(event) => setDraftNote(event.target.value)}
              rows={3}
              placeholder="比如：色号偏暖、缺货先联系我、需要礼盒包装"
              className="w-full rounded-2xl border border-black/10 bg-white/80 px-4 py-3 outline-none"
            />
          </label>
        </div>
      </div>
      <div className="flex flex-col justify-between gap-3 md:w-[180px] md:items-end">
        <div className="text-right">
          <p className="text-lg font-bold text-coral">
            ¥{(product.priceCny * Math.max(normalizedQuantity || quantity, 1)).toFixed(2)}
          </p>
          <p className="text-sm subtle">人民币参考单价 ¥{product.priceCny.toFixed(2)}</p>
        </div>
        <div className="flex flex-wrap gap-2 md:justify-end">
          <button className="cta ghost" type="button" onClick={handleSave} disabled={!canSave}>
            {isSaving ? "保存中..." : "保存修改"}
          </button>
          <button
            className="cta ghost"
            type="button"
            onClick={() => onRemove?.(cartItemId)}
            disabled={isRemoving || isSaving}
          >
            {isRemoving ? "删除中..." : "删除"}
          </button>
        </div>
      </div>
    </div>
  );
}
