import { SearchResultsClient } from "@/components/SearchResultsClient";

export default function SearchPage({
  searchParams
}: {
  searchParams?: { keyword?: string; sort?: string };
}) {
  const keyword = searchParams?.keyword ?? "";
  const sort = searchParams?.sort || "ranking";

  return <SearchResultsClient initialKeyword={keyword} initialSort={sort} />;
}
