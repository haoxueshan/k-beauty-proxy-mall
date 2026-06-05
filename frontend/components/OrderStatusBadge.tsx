const labels: Record<string, string> = {
  pending_quote: "待报价",
  quoted: "已报价",
  pending_payment: "待付款",
  paid: "已付款",
  pending_purchase: "待采购",
  purchasing: "采购中",
  purchased: "已采购",
  warehouse_received: "韩国仓已收货",
  shipping: "国际运输中",
  china_delivery: "中国派送中",
  delivered: "已签收",
  completed: "订单完成"
};

export function OrderStatusBadge({ status }: { status: string }) {
  return (
    <span className="inline-flex rounded-full border border-black/10 bg-white/80 px-3 py-1 text-sm">
      {labels[status] ?? status}
    </span>
  );
}
