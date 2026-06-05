import { mockLogistics } from "@/lib/mock-data";

export default function AdminLogisticsPage() {
  return (
    <div className="container pb-16">
      <section className="panel p-8">
        <p className="eyebrow">Admin / Logistics</p>
        <h1 className="mt-3 text-3xl font-semibold">物流管理</h1>
        <p className="subtle mt-2">用于录入国际物流单号、承运商和异常状态，连接订单追踪链路。</p>
      </section>

      <section className="mt-8 overflow-hidden rounded-[24px] border border-black/10 bg-white/75">
        <table className="min-w-full text-left text-sm">
          <thead className="border-b border-black/10">
            <tr>
              <th className="px-4 py-4">订单号</th>
              <th className="px-4 py-4">承运商</th>
              <th className="px-4 py-4">物流单号</th>
              <th className="px-4 py-4">状态</th>
            </tr>
          </thead>
          <tbody>
            {mockLogistics.map((item) => (
              <tr key={item.trackingNo} className="border-b border-black/5">
                <td className="px-4 py-4">{item.orderNo}</td>
                <td className="px-4 py-4">{item.carrier}</td>
                <td className="px-4 py-4">{item.trackingNo}</td>
                <td className="px-4 py-4">{item.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
