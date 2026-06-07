"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";

type Props = {
  defaultValue?: string;
};

export function SearchBar({ defaultValue = "" }: Props) {
  const router = useRouter();
  const [keyword, setKeyword] = useState(defaultValue);
  const [isPending, startTransition] = useTransition();

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    startTransition(() => {
      router.push(`/search?keyword=${encodeURIComponent(keyword.trim())}`);
    });
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3 md:flex-row" aria-busy={isPending}>
      <input
        value={keyword}
        onChange={(event) => setKeyword(event.target.value)}
        placeholder="请输入商品关键词，例如：防晒、面膜、唇釉、卸妆油"
        className="min-h-[54px] flex-1 rounded-full border border-black/10 bg-white/80 px-5 text-base outline-none transition focus:border-black/30"
      />
      <button type="submit" className="cta min-w-[112px]" disabled={isPending}>
        {isPending ? <span className="mini-spinner" aria-hidden="true" /> : null}
        {isPending ? "搜索中..." : "搜索商品"}
      </button>
    </form>
  );
}
