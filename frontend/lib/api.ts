import { mockCart, mockOrders, mockProducts, type CartDisplayItem, type CartEntry, type Order, type Product, type User } from "@/lib/mock-data";

export const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export type ProductSearchResult = {
  keywordOriginal: string;
  keywordKo: string;
  count: number;
  items: Product[];
};

export type CrawlerSyncResult = {
  taskId: string;
  status: string;
  keyword: string;
  count: number;
  source: string;
};

async function safeFetch<T>(path: string, fallback: T): Promise<T> {
  try {
    const response = await fetch(`${API_BASE}${path}`, {
      cache: "no-store"
    });
    if (!response.ok) {
      return fallback;
    }
    return (await response.json()) as T;
  } catch {
    return fallback;
  }
}

function normalizeProduct(payload: any): Product {
  return {
    id: payload.id,
    goodsNo: payload.goodsNo ?? payload.goods_no,
    titleZh: payload.titleZh ?? payload.title_zh,
    titleKo: payload.titleKo ?? payload.title_ko,
    brandZh: payload.brandZh ?? payload.brand_zh,
    brandKo: payload.brandKo ?? payload.brand_ko,
    imageUrl: payload.imageUrl ?? payload.image_url,
    salePriceKrw: payload.salePriceKrw ?? payload.sale_price_krw,
    originalPriceKrw: payload.originalPriceKrw ?? payload.original_price_krw,
    priceCny: payload.priceCny ?? payload.price_cny,
    proxyPriceCny: payload.proxyPriceCny ?? payload.proxy_price_cny,
    categoryZh: payload.categoryZh ?? payload.category_zh,
    aiSummary: payload.aiSummary ?? payload.ai_summary,
    riskTips: payload.riskTips ?? payload.risk_tips ?? [],
    sourceUrl: payload.sourceUrl ?? payload.source_url
  };
}

function normalizeOrder(payload: any): Order {
  return {
    id: payload.id,
    userId: payload.userId ?? payload.user_id,
    orderNo: payload.orderNo ?? payload.order_no,
    status: payload.status,
    totalAmountCny: payload.totalAmountCny ?? payload.total_amount_cny,
    receiverName: payload.receiverName ?? payload.receiver_name,
    createdAt: payload.createdAt ?? payload.created_at
  };
}

function normalizeUser(payload: any): User {
  return {
    id: payload.id,
    email: payload.email,
    name: payload.name,
    phone: payload.phone ?? null,
    createdAt: payload.createdAt ?? payload.created_at
  };
}

function normalizeCartEntry(payload: any): CartEntry {
  return {
    id: payload.id,
    userId: payload.userId ?? payload.user_id,
    productId: payload.productId ?? payload.product_id,
    quantity: payload.quantity ?? 1,
    selectedOption: payload.selectedOption ?? payload.selected_option ?? null,
    note: payload.note ?? null,
    createdAt: payload.createdAt ?? payload.created_at
  };
}

function normalizeSearchResult(payload: any, fallbackItems: Product[]): ProductSearchResult {
  const items = Array.isArray(payload.items) ? payload.items.map(normalizeProduct) : fallbackItems;
  return {
    keywordOriginal: payload.keywordOriginal ?? payload.keyword_original ?? "",
    keywordKo: payload.keywordKo ?? payload.keyword_ko ?? "",
    count: payload.count ?? items.length,
    items
  };
}

function normalizeCrawlerSyncResult(payload: any): CrawlerSyncResult {
  return {
    taskId: payload.taskId ?? payload.task_id,
    status: payload.status,
    keyword: payload.keyword,
    count: payload.count ?? 0,
    source: payload.source ?? ""
  };
}

export async function searchProductResults(keyword: string): Promise<ProductSearchResult> {
  const normalized = keyword.trim().toLowerCase();
  const fallback = !normalized
    ? mockProducts
    : mockProducts.filter((product) =>
        [product.titleZh, product.titleKo, product.brandZh, product.categoryZh].join(" ").toLowerCase().includes(normalized)
      );

  const data = await safeFetch<any>(
    `/api/products/search?keyword=${encodeURIComponent(keyword)}`,
    {
      keyword_original: keyword,
      keyword_ko: keyword,
      count: fallback.length,
      items: fallback
    }
  );
  return normalizeSearchResult(data, fallback);
}

export async function searchProducts(keyword: string): Promise<Product[]> {
  const result = await searchProductResults(keyword);
  return result.items;
}

export async function syncOliveYoungProducts(keyword: string, limit = 24): Promise<CrawlerSyncResult> {
  const result = await authFetch<any>("/api/crawler/oliveyoung/sync", {
    method: "POST",
    body: JSON.stringify({
      keyword,
      limit
    })
  });
  return normalizeCrawlerSyncResult(result);
}

export async function getProduct(id: string): Promise<Product | null> {
  const fallback = mockProducts.find((product) => product.id === id) ?? null;
  const product = await safeFetch<any | null>(`/api/products/${id}`, fallback);
  return product ? normalizeProduct(product) : null;
}

export async function getOrders(): Promise<Order[]> {
  const orders = await safeFetch<any[]>("/api/orders", mockOrders);
  return orders.map(normalizeOrder);
}

async function authFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    },
    cache: "no-store"
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail ?? "Request failed");
  }
  return payload as T;
}

export async function registerUser(payload: {
  email: string;
  password: string;
  name: string;
  phone?: string;
}): Promise<{ token: string; user: User }> {
  const result = await authFetch<any>("/api/auth/register", {
    method: "POST",
    body: JSON.stringify(payload)
  });
  return { token: result.token, user: normalizeUser(result.user) };
}

export async function loginUser(payload: {
  email: string;
  password: string;
}): Promise<{ token: string; user: User }> {
  const result = await authFetch<any>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify(payload)
  });
  return { token: result.token, user: normalizeUser(result.user) };
}

export async function getCurrentUser(token: string): Promise<User> {
  const result = await authFetch<any>("/api/auth/me", {
    headers: {
      Authorization: `Bearer ${token}`
    }
  });
  return normalizeUser(result);
}

export async function logoutUser(token: string): Promise<void> {
  await authFetch("/api/auth/logout", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`
    }
  });
}

export async function getMyOrders(token: string): Promise<Order[]> {
  const result = await authFetch<any[]>("/api/orders", {
    headers: {
      Authorization: `Bearer ${token}`
    }
  });
  return result.map(normalizeOrder);
}

export async function addCartItem(
  token: string,
  payload: { productId: string; quantity?: number; selectedOption?: string; note?: string }
): Promise<{ success: boolean; cartItemId: string }> {
  const result = await authFetch<any>("/api/cart/items", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify({
      product_id: payload.productId,
      quantity: payload.quantity ?? 1,
      selected_option: payload.selectedOption,
      note: payload.note
    })
  });
  return {
    success: result.success,
    cartItemId: result.cartItemId ?? result.cart_item_id
  };
}

export async function getCartItems(token: string): Promise<CartDisplayItem[]> {
  const result = await authFetch<any[]>("/api/cart/items", {
    headers: {
      Authorization: `Bearer ${token}`
    }
  });

  const entries = result.map(normalizeCartEntry);
  const displayItems = await Promise.all(
    entries.map(async (entry) => {
      const product = await getProduct(entry.productId);
      if (!product) {
        return null;
      }
      return {
        ...entry,
        product
      };
    })
  );

  return displayItems.filter((item): item is CartDisplayItem => item !== null);
}

export async function deleteCartItem(token: string, cartItemId: string): Promise<void> {
  await authFetch(`/api/cart/items/${cartItemId}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`
    }
  });
}

export function getMockCartItems(): CartDisplayItem[] {
  return mockCart.map((entry) => ({
    id: entry.id,
    productId: entry.productId,
    quantity: entry.quantity,
    selectedOption: entry.selectedOption,
    note: entry.note,
    product: entry.product
  }));
}
