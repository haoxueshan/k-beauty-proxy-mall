import { mockCrawlerTasks } from "@/lib/mock-data";

export default function AdminCrawlerPage() {
  return (
    <div className="container pb-16">
      <section className="panel p-8">
        <p className="eyebrow">Admin / Crawler</p>
        <h1 className="mt-3 text-3xl font-semibold">抓取任务管理</h1>
        <p className="subtle mt-2">首版只展示关键词任务、状态和结果数量，真实抓取逻辑后续再接入。</p>
      </section>

      <section className="mt-8 grid gap-4">
        {mockCrawlerTasks.map((task) => (
          <article key={task.id} className="panel flex flex-col gap-3 p-5 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="font-semibold">关键词：{task.keyword}</p>
              <p className="subtle mt-1 text-sm">更新时间：{task.updatedAt}</p>
            </div>
            <div className="flex items-center gap-4 text-sm">
              <span>状态：{task.status}</span>
              <span>结果数：{task.count}</span>
              <button className="cta ghost" type="button">
                重新同步
              </button>
            </div>
          </article>
        ))}
      </section>
    </div>
  );
}
