import type { Product, ProductMetadata } from "@/lib/mock-data";

export const SOURCE_TYPE_LABELS: Record<string, string> = {
  live_search: "实时搜索",
  live_detail: "详情回源",
  live_main: "首页回源",
  cache: "缓存结果",
  seed: "Seed 推荐"
};

export const SOURCE_LABELS: Record<string, string> = {
  "oliveyoung-search": "Olive Young 实时搜索抓取",
  "oliveyoung-main": "Olive Young 首页实时抓取",
  "oliveyoung-search-empty": "Olive Young 实时搜索无结果",
  "oliveyoung-search-error": "Olive Young 实时搜索失败",
  "oliveyoung-live-error": "Olive Young 实时搜索失败",
  "fallback-seed": "备用种子数据"
};

export const CACHE_LAYER_LABELS: Record<string, string> = {
  none: "实时回源",
  memory: "内存热缓存",
  seed: "Seed 兜底"
};

export function getSourceLabel(source?: string | null, sourceType?: string | null) {
  if (source && SOURCE_LABELS[source]) {
    return SOURCE_LABELS[source];
  }
  return getSourceTypeLabel(sourceType) || source || "待确认";
}

export function getSourceTypeLabel(sourceType?: string | null) {
  if (!sourceType) {
    return "待确认";
  }
  return SOURCE_TYPE_LABELS[sourceType] ?? sourceType;
}

export function getCacheLayerLabel(cacheLayer?: string | null) {
  if (!cacheLayer) {
    return "待确认";
  }
  return CACHE_LAYER_LABELS[cacheLayer] ?? cacheLayer;
}

export function formatSyncedAt(value?: string | null) {
  if (!value) {
    return "待确认";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  }).format(date);
}

export function formatConfidence(value?: number | null) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "待确认";
  }
  return `${Math.round(Math.max(0, Math.min(1, value)) * 100)}%`;
}

export function getConfidenceStatus(value?: number | null) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "待确认";
  }
  if (value >= 0.85) {
    return "高";
  }
  if (value >= 0.65) {
    return "中";
  }
  return "低";
}

export function isFallbackSource(sourceType?: string | null) {
  return sourceType === "seed";
}

export function getProductSpec(product: Product) {
  const text = `${product.titleZh || ""} ${product.titleKo || ""}`;
  const match = text.match(/\b\d+(?:\.\d+)?\s?(?:ml|mL|ML|g|G|kg|KG|매|입|개|호|号|片|张|枚|支|瓶)\b/u);
  return match?.[0] ?? null;
}

export function getProductMetadata(product: Product): ProductMetadata {
  return product.metadata ?? {};
}
