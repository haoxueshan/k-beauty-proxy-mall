export type ProductMetadata = {
  lastSyncedAt?: string | null;
  sourceType?: string;
  completenessScore?: number;
  priceConfidence?: number;
  translationConfidence?: number;
  sourceRank?: number | null;
  keywordKo?: string | null;
  syncedAt?: string | null;
  rawPriceText?: string | null;
};

export type Product = {
  id: string;
  goodsNo: string;
  titleZh: string;
  titleKo: string;
  brandZh: string;
  brandKo: string;
  imageUrl: string;
  salePriceKrw: number;
  originalPriceKrw: number;
  priceCny: number;
  proxyPriceCny?: number;
  categoryZh: string;
  aiSummary: string;
  riskTips: string[];
  sourceUrl: string;
  metadata?: ProductMetadata;
};

export type OrderItem = {
  id: string;
  productId: string;
  sourceUrl?: string | null;
  titleZh: string;
  titleKo: string;
  selectedOption?: string | null;
  quantity: number;
  unitPriceCny: number;
  subtotalCny: number;
};

export type Order = {
  id: string;
  userId?: string;
  userEmail?: string | null;
  userName?: string | null;
  userPhone?: string | null;
  orderNo: string;
  status: string;
  productTotalCny: number;
  serviceFeeCny: number;
  internationalShippingFeeCny: number;
  packageFeeCny: number;
  totalAmountCny: number;
  paidAmountCny: number;
  receiverName: string;
  receiverPhone?: string | null;
  receiverAddress?: string | null;
  userNote?: string | null;
  adminNote?: string | null;
  items: OrderItem[];
  createdAt: string;
};

export type User = {
  id: string;
  email: string;
  name: string;
  phone?: string | null;
  role?: "user" | "admin" | "super_admin";
  isAdmin?: boolean;
  createdAt: string;
};

export type CartEntry = {
  id: string;
  userId?: string;
  productId: string;
  quantity: number;
  selectedOption?: string | null;
  note?: string | null;
  createdAt?: string;
};

export type CartDisplayItem = CartEntry & {
  product: Product;
};

export const mockProducts: Product[] = [
  {
    id: "oy-1",
    goodsNo: "A000000000001",
    titleZh: "Round Lab 白桦树防晒霜",
    titleKo: "라운드랩 자작나무 수분 선크림",
    brandZh: "Round Lab",
    brandKo: "라운드랩",
    imageUrl: "https://images.unsplash.com/photo-1625772452859-1c03d5bf1137?auto=format&fit=crop&w=900&q=80",
    salePriceKrw: 18900,
    originalPriceKrw: 26000,
    priceCny: 99.6,
    proxyPriceCny: 149.6,
    categoryZh: "防晒",
    aiSummary: "轻薄保湿型防晒，适合日常通勤与春夏使用。",
    riskTips: ["价格会随汇率波动", "下单前请确认规格与保质期"],
    sourceUrl: "https://www.oliveyoung.co.kr/"
  },
  {
    id: "oy-2",
    goodsNo: "A000000000002",
    titleZh: "rom&nd 果汁唇釉 23 Nucadamia",
    titleKo: "롬앤 쥬시 래스팅 틴트 23호",
    brandZh: "rom&nd",
    brandKo: "롬앤",
    imageUrl: "https://images.unsplash.com/photo-1586495777744-4413f21062fa?auto=format&fit=crop&w=900&q=80",
    salePriceKrw: 9800,
    originalPriceKrw: 13000,
    priceCny: 51.7,
    proxyPriceCny: 101.7,
    categoryZh: "唇妆",
    aiSummary: "偏奶咖色调，适合作为日常通勤唇色。",
    riskTips: ["不同屏幕下颜色可能略有差异"],
    sourceUrl: "https://www.oliveyoung.co.kr/"
  },
  {
    id: "oy-3",
    goodsNo: "A000000000003",
    titleZh: "Anua 鱼腥草舒缓爽肤水",
    titleKo: "아누아 어성초 77 토너",
    brandZh: "Anua",
    brandKo: "아누아",
    imageUrl: "https://images.unsplash.com/photo-1556228578-dd6c474e2113?auto=format&fit=crop&w=900&q=80",
    salePriceKrw: 21500,
    originalPriceKrw: 29000,
    priceCny: 113.2,
    proxyPriceCny: 163.2,
    categoryZh: "护肤",
    aiSummary: "偏舒缓路线，适合泛红与轻敏感护理场景。",
    riskTips: ["敏感肌请先做局部测试"],
    sourceUrl: "https://www.oliveyoung.co.kr/"
  }
];

export const mockCart = [
  {
    id: "cart-1",
    productId: "oy-1",
    product: mockProducts[0],
    quantity: 1,
    selectedOption: "50ml",
    note: "如果缺货请先联系我"
  },
  {
    id: "cart-2",
    productId: "oy-2",
    quantity: 2,
    product: mockProducts[1],
    selectedOption: "23号",
    note: "优先要暖调"
  }
];

export const mockOrders: Order[] = [
  {
    id: "order-1",
    userId: "demo-user",
    orderNo: "OY202606040001",
    status: "pending",
    productTotalCny: 203,
    serviceFeeCny: 0,
    internationalShippingFeeCny: 0,
    packageFeeCny: 0,
    totalAmountCny: 203,
    paidAmountCny: 0,
    receiverName: "张三",
    receiverPhone: "13800000000",
    receiverAddress: "上海市浦东新区世纪大道 100 号 8 楼",
    userNote: "优先保质期长的批次",
    adminNote: null,
    items: [
      {
        id: "order-item-1",
        productId: "oy-1",
        sourceUrl: "https://www.oliveyoung.co.kr/",
        titleZh: "Round Lab 白桦树防晒霜",
        titleKo: "라운드랩 자작나무 수분 선크림",
        selectedOption: "50ml",
        quantity: 1,
        unitPriceCny: 99.6,
        subtotalCny: 99.6
      },
      {
        id: "order-item-2",
        productId: "oy-2",
        sourceUrl: "https://www.oliveyoung.co.kr/",
        titleZh: "rom&nd 果汁唇釉 23 Nucadamia",
        titleKo: "롬앤 쥬시 래스팅 틴트 23호",
        selectedOption: "23号",
        quantity: 2,
        unitPriceCny: 51.7,
        subtotalCny: 103.4
      }
    ],
    createdAt: "2026-06-04 12:30"
  },
  {
    id: "order-2",
    userId: "demo-user",
    orderNo: "OY202606030003",
    status: "processing",
    productTotalCny: 113.2,
    serviceFeeCny: 0,
    internationalShippingFeeCny: 0,
    packageFeeCny: 0,
    totalAmountCny: 113.2,
    paidAmountCny: 113.2,
    receiverName: "李四",
    receiverPhone: "13900000000",
    receiverAddress: "北京市朝阳区建国路 88 号",
    userNote: "暖色优先",
    adminNote: "已完成韩国仓打包",
    items: [
      {
        id: "order-item-3",
        productId: "oy-3",
        sourceUrl: "https://www.oliveyoung.co.kr/",
        titleZh: "Anua 鱼腥草舒缓爽肤水",
        titleKo: "아누아 어성초 77 토너",
        selectedOption: "单瓶",
        quantity: 1,
        unitPriceCny: 113.2,
        subtotalCny: 113.2
      }
    ],
    createdAt: "2026-06-03 19:42"
  }
];

export const mockCrawlerTasks = [
  { id: "task-1", keyword: "防晒", status: "success", count: 20, updatedAt: "2026-06-04 09:20" },
  { id: "task-2", keyword: "唇釉", status: "running", count: 12, updatedAt: "2026-06-04 09:32" }
];

export const mockLogistics = [
  { orderNo: "OY202606030003", carrier: "CJ", trackingNo: "KR123456789", status: "国际运输中" },
  { orderNo: "OY202606010008", carrier: "顺丰", trackingNo: "SF987654321", status: "中国派送中" }
];
