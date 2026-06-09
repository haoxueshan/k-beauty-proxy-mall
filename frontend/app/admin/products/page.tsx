import { mockProducts } from "@/lib/mock-data";

export default function AdminProductsPage() {
  return (
    <div className="container pb-16">
      <section className="panel p-8">
        <p className="eyebrow">Admin / Products</p>
        <h1 className="mt-3 text-3xl font-semibold">商品管理</h1>
        <p className="subtle mt-2">展示已同步的商品基础信息，后续可接入审核、手工改价和风险标记。</p>
      </section>

      <section className="mt-8 overflow-hidden rounded-[24px] border border-black/10 bg-white/75">
        <table className="min-w-full text-left text-sm">
          <thead className="border-b border-black/10">
            <tr>
              <th className="px-4 py-4">商品</th>
              <th className="px-4 py-4">品牌</th>
              <th className="px-4 py-4">韩元价</th>
              <th className="px-4 py-4">人民币参考价</th>
              <th className="px-4 py-4">分类</th>
            </tr>
          </thead>
          <tbody>
            {mockProducts.map((product) => (
              <tr key={product.id} className="border-b border-black/5">
                <td className="px-4 py-4">{product.titleZh}</td>
                <td className="px-4 py-4">{product.brandZh}</td>
                <td className="px-4 py-4">KRW {product.salePriceKrw.toLocaleString()}</td>
                <td className="px-4 py-4">¥{product.priceCny.toFixed(2)}</td>
                <td className="px-4 py-4">{product.categoryZh}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
