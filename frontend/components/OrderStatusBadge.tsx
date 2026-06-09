import { getOrderStatusLabel } from "@/lib/order-status";

export function OrderStatusBadge({ status }: { status: string }) {
  return (
    <span className="inline-flex rounded-full border border-black/10 bg-white/80 px-3 py-1 text-sm">
      {getOrderStatusLabel(status)}
    </span>
  );
}
