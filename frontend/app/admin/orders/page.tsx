import { OrderStatusBadge } from "@/components/OrderStatusBadge";
import { mockOrders } from "@/lib/mock-data";

export default function AdminOrdersPage() {
  return (
    <div className="container pb-16">
      <section className="panel p-8">
        <p className="eyebrow">Admin / Orders</p>
        <h1 className="mt-3 text-3xl font-semibold">订单管理</h1>
        <p className="subtle mt-2">可作为报价、采购状态推进、售后处理和异常订单排查的起点页面。</p>
      </section>

      <section className="mt-8 space-y-4">
        {mockOrders.map((order) => (
          <article key={order.id} className="panel p-6">
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <div>
                <p className="text-lg font-semibold">{order.orderNo}</p>
                <p className="subtle mt-1 text-sm">收件人：{order.receiverName}</p>
              </div>
              <div className="flex items-center gap-4">
                <OrderStatusBadge status={order.status} />
                <button className="cta ghost" type="button">
                  修改报价
                </button>
              </div>
            </div>
          </article>
        ))}
      </section>
    </div>
  );
}
