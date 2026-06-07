import { AdminOrdersClient } from "@/components/AdminOrdersClient";

export default function AdminOrdersPage() {
  return (
    <div className="container pb-16">
      <section className="panel p-8">
        <p className="eyebrow">Admin / Orders</p>
        <h1 className="mt-3 text-3xl font-semibold">订单管理</h1>
        <p className="subtle mt-2">这里用于查看所有用户提交的订单，方便报价、采购、仓储和物流跟进。</p>
      </section>

      <AdminOrdersClient />
    </div>
  );
}
