import { OrdersClient } from "@/components/OrdersClient";

export default function OrdersPage() {
  return (
    <div className="container pb-16">
      <section className="panel p-8">
        <p className="eyebrow">Orders</p>
        <h1 className="mt-3 text-3xl font-semibold">我的订单</h1>
        <p className="subtle mt-2">首版状态流覆盖待报价、待付款、采购、仓储、国际物流与签收。</p>
      </section>
      <OrdersClient />
    </div>
  );
}
