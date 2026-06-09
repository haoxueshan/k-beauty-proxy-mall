import { AdminOrdersClient } from "@/components/AdminOrdersClient";

export default function AdminOrdersPage() {
  return (
    <div className="container pb-16">
      <section className="panel p-8">
        <p className="eyebrow">Admin / Orders</p>
        <h1 className="mt-3 text-3xl font-semibold">订单管理</h1>
        <p className="subtle mt-2">查看全部用户订单，并在详情弹窗里更新订单状态和管理员备注。</p>
      </section>

      <AdminOrdersClient />
    </div>
  );
}
