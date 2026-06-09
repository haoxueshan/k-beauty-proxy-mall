export const ORDER_STATUS_OPTIONS = [
  { value: "pending", label: "待处理" },
  { value: "quoted", label: "已报价" },
  { value: "processing", label: "处理中" },
  { value: "completed", label: "已完成" },
  { value: "cancelled", label: "已取消" }
] as const;

export type AdminOrderStatus = (typeof ORDER_STATUS_OPTIONS)[number]["value"];

export const ORDER_STATUS_LABELS: Record<string, string> = {
  pending: "待处理",
  quoted: "已报价",
  processing: "处理中",
  completed: "已完成",
  cancelled: "已取消",
  pending_quote: "待处理",
  pending_payment: "处理中",
  paid: "处理中",
  pending_purchase: "处理中",
  purchasing: "处理中",
  purchased: "处理中",
  warehouse_received: "处理中",
  shipping: "处理中",
  china_delivery: "处理中",
  delivered: "已完成"
};

export function getOrderStatusLabel(status: string) {
  return ORDER_STATUS_LABELS[status] ?? status;
}
