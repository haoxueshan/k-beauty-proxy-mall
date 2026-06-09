const skeletonCards = ["one", "two", "three"];

export default function SearchLoading() {
  return (
    <div className="container pb-16">
      <section className="panel overflow-hidden p-6 md:p-8">
        <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="eyebrow">Live Search</p>
            <h1 className="mt-3 text-3xl font-semibold">正在抓取 Olive Young 数据</h1>
            <p className="subtle mt-2">
              已收到搜索请求，正在连接后端爬虫、翻译商品标题并计算人民币参考价，请稍等片刻。
            </p>
          </div>
          <div className="loading-orbit" aria-hidden="true">
            <span />
          </div>
        </div>
        <div className="mt-6 rounded-3xl border border-black/10 bg-white/55 p-4">
          <div className="loading-steps">
            <span>发送搜索请求</span>
            <span>抓取 Olive Young</span>
            <span>整理商品结果</span>
          </div>
        </div>
      </section>

      <section className="mt-8">
        <div className="mb-4 flex items-center justify-between">
          <div className="shimmer-line h-7 w-52" />
          <div className="shimmer-line h-5 w-24" />
        </div>
        <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
          {skeletonCards.map((item) => (
            <article key={item} className="panel overflow-hidden">
              <div className="shimmer-block aspect-[4/3]" />
              <div className="space-y-4 p-5">
                <div className="shimmer-line h-4 w-24" />
                <div className="shimmer-line h-7 w-4/5" />
                <div className="shimmer-line h-4 w-full" />
                <div className="shimmer-line h-4 w-2/3" />
                <div className="flex gap-3 pt-2">
                  <div className="shimmer-pill h-11 w-24" />
                  <div className="shimmer-pill h-11 w-28" />
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
