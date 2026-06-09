import Link from "next/link";
import { SearchBar } from "@/components/SearchBar";

const categories = ["防晒", "护肤", "面膜", "唇釉", "底妆", "卸妆"];

export default function HomePage() {
  return (
    <div className="container pb-16">
      <section className="grid gap-8 py-8 md:grid-cols-[1.4fr_0.9fr]">
        <div className="panel p-8 md:p-10">
          <p className="eyebrow">Chinese Shopping MVP</p>
          <h1 className="headline mt-4">把 Olive Young 变成更容易下单的中文入口。</h1>
          <p className="subtle mt-6 max-w-2xl text-lg leading-8">
            面向中国用户的韩妆商品平台 MVP。先解决搜索、中文理解、人民币参考价和订单追踪，再逐步接入真实抓取、采购和物流后台。
          </p>
          <div className="mt-8">
            <SearchBar />
          </div>
          <div className="mt-8 flex flex-wrap gap-3">
            {categories.map((item) => (
              <Link
                key={item}
                href={`/search?keyword=${encodeURIComponent(item)}`}
                className="rounded-full border border-black/10 bg-white/70 px-4 py-2 text-sm"
              >
                {item}
              </Link>
            ))}
          </div>
        </div>
        <div className="panel flex flex-col justify-between p-8">
          <div>
            <p className="eyebrow">MVP Focus</p>
            <div className="mt-6 space-y-4 text-sm leading-7">
              <p>1. 中文关键词搜索 Olive Young 商品</p>
              <p>2. 商品详情与人民币参考价展示</p>
              <p>3. 平台购物车与订单提交流程</p>
              <p>4. 后台订单、抓取任务、物流管理骨架</p>
            </div>
          </div>
          <Link href="/search" className="cta mt-8 w-full">
            开始搜索商品
          </Link>
        </div>
      </section>
    </div>
  );
}
