from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ProductMetadata(BaseModel):
    # 单品级元信息：前端用它展示来源、同步时间、可信度和页内排名。
    last_synced_at: datetime | None = None
    source_type: str = "live_search"
    completeness_score: float = 0
    price_confidence: float = 0
    translation_confidence: float = 0
    source_rank: int | None = None
    keyword_ko: str | None = None
    synced_at: datetime | None = None
    raw_price_text: str | None = None


class ResultSetMeta(BaseModel):
    # 结果集级元信息：描述本次搜索整体来源，避免把备用推荐伪装成主结果。
    source: str = "oliveyoung-live"
    source_type: str = "live_search"
    cache_layer: str = "none"
    last_synced_at: datetime | None = None
    item_count: int = 0
    completeness_score: float = 0
    price_confidence: float = 0
    translation_confidence: float = 0


class Product(BaseModel):
    id: str
    source: str = "oliveyoung"
    goods_no: str
    source_url: str
    brand_ko: str
    brand_zh: str
    title_ko: str
    title_zh: str
    image_url: str
    original_price_krw: int
    sale_price_krw: int
    price_cny: float
    proxy_price_cny: float
    category_zh: str
    ai_summary: str
    risk_tips: list[str] = Field(default_factory=list)
    metadata: ProductMetadata = Field(default_factory=ProductMetadata)


class SearchResponse(BaseModel):
    # items 是当前搜索页主结果；fallback_items 是备用推荐，两者必须分开消费。
    keyword_original: str
    keyword_ko: str
    count: int
    items: list[Product]
    source: str = "oliveyoung-live"
    source_type: str = "live_search"
    result_meta: ResultSetMeta = Field(default_factory=ResultSetMeta)
    fallback_count: int = 0
    fallback_items: list[Product] = Field(default_factory=list)
    fallback_meta: ResultSetMeta | None = None
    page: int = 1
    page_size: int = 24
    sort: str = "ranking"
    has_next: bool = False
    next_page: int | None = None
    oliveyoung_page_url: str | None = None
    source_rank_start: int | None = None
    synced_pages: list[int] = Field(default_factory=list)
    error: str | None = None


class CrawlerSyncRequest(BaseModel):
    keyword: str
    limit: int = 30
    page: int = Field(default=1, ge=1)
    page_size: int | None = Field(default=None, ge=1, le=60)
    sort: str = "ranking"


class CrawlerSyncResponse(BaseModel):
    task_id: str
    status: str
    keyword: str
    count: int = 0
    source: str = ""


class CartItemCreate(BaseModel):
    product_id: str
    source_url: str | None = None
    title_zh: str | None = None
    title_ko: str | None = None
    image_url: str | None = None
    sale_price_krw: int | None = None
    price_cny: float | None = None
    brand_ko: str | None = None
    quantity: int = Field(default=1, ge=1)
    selected_option: str | None = None
    note: str | None = None


class CartItemUpdate(BaseModel):
    quantity: int = Field(default=1, ge=1)
    note: str | None = None


class CartItem(BaseModel):
    id: str
    user_id: str
    product_id: str
    source_url: str | None = None
    title_zh: str | None = None
    title_ko: str | None = None
    image_url: str | None = None
    sale_price_krw: int | None = None
    price_cny: float | None = None
    brand_ko: str | None = None
    quantity: int
    selected_option: str | None = None
    note: str | None = None
    created_at: datetime


class CartItemResponse(BaseModel):
    success: bool
    cart_item_id: str


class DeleteResponse(BaseModel):
    success: bool


class OrderCreate(BaseModel):
    cart_item_ids: list[str] = Field(min_length=1)
    receiver_name: str
    receiver_phone: str
    receiver_address: str
    note: str | None = None


class OrderItemSummary(BaseModel):
    id: str
    product_id: str
    source_url: str | None = None
    title_zh: str
    title_ko: str
    selected_option: str | None = None
    note: str | None = None
    quantity: int
    unit_price_cny: float
    subtotal_cny: float


class Order(BaseModel):
    id: str
    user_id: str
    order_no: str
    status: str
    product_total_cny: float = 0
    service_fee_cny: float = 0
    international_shipping_fee_cny: float = 0
    package_fee_cny: float = 0
    total_amount_cny: float
    paid_amount_cny: float = 0
    receiver_name: str
    receiver_phone: str | None = None
    receiver_address: str | None = None
    user_note: str | None = None
    admin_note: str | None = None
    items: list[OrderItemSummary] = Field(default_factory=list)
    created_at: datetime


class CartDisplayItem(CartItem):
    # 购物车展示接口返回购物车条目 + 商品信息，减少前端逐个请求商品详情。
    product: Product


class AdminOrder(Order):
    user_email: str | None = None
    user_name: str | None = None
    user_phone: str | None = None


class OrderResponse(BaseModel):
    order_id: str
    order_no: str
    status: str


class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: datetime


class ReadinessCheck(BaseModel):
    name: str
    status: str
    detail: str | None = None


class ReadinessResponse(BaseModel):
    status: str
    service: str
    environment: str
    timestamp: datetime
    checks: list[ReadinessCheck] = Field(default_factory=list)


class UserPublic(BaseModel):
    id: str
    email: str
    name: str
    phone: str | None = None
    role: Literal["user", "admin", "super_admin"] = "user"
    is_admin: bool = False
    created_at: datetime


class AdminOrderUpdate(BaseModel):
    status: Literal["pending", "quoted", "processing", "completed", "cancelled"]
    admin_note: str | None = None


class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=6)
    name: str = Field(min_length=2)
    phone: str = Field(min_length=4)
    verification_code: str = Field(min_length=4, max_length=8)


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=6)


class PasswordResetRequest(BaseModel):
    email: str
    phone: str = Field(min_length=4)
    verification_code: str = Field(min_length=4, max_length=8)
    new_password: str = Field(min_length=6)


class BasicSuccessResponse(BaseModel):
    success: bool


class AuthResponse(BaseModel):
    token: str
    user: UserPublic


class LogoutResponse(BaseModel):
    success: bool


class TranslateRequest(BaseModel):
    texts: list[str] = Field(min_length=1, max_length=50)
    source_language: str = "Korean"
    target_language: str = "Simplified Chinese"


class TranslateResponse(BaseModel):
    provider: str
    model: str | None = None
    translations: list[str]


class RawCrawlerProduct(BaseModel):
    goods_no: str
    title_ko: str
    brand_ko: str
    image_url: str
    original_price_krw: int
    sale_price_krw: int
    category_ko: str
    source_url: str
    raw_data: dict[str, Any] = Field(default_factory=dict)
