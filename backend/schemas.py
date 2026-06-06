from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


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


class SearchResponse(BaseModel):
    keyword_original: str
    keyword_ko: str
    count: int
    items: list[Product]
    source: str = "oliveyoung-live"
    error: str | None = None


class CrawlerSyncRequest(BaseModel):
    keyword: str
    limit: int = 30


class CrawlerSyncResponse(BaseModel):
    task_id: str
    status: str
    keyword: str
    count: int = 0
    source: str = ""


class CartItemCreate(BaseModel):
    product_id: str
    quantity: int = 1
    selected_option: str | None = None
    note: str | None = None


class CartItem(BaseModel):
    id: str
    user_id: str
    product_id: str
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
    cart_item_ids: list[str]
    receiver_name: str
    receiver_phone: str
    receiver_address: str
    note: str | None = None


class Order(BaseModel):
    id: str
    user_id: str
    order_no: str
    status: str
    total_amount_cny: float
    receiver_name: str
    created_at: datetime


class OrderResponse(BaseModel):
    order_id: str
    order_no: str
    status: str


class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: datetime


class UserPublic(BaseModel):
    id: str
    email: str
    name: str
    phone: str | None = None
    created_at: datetime


class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=6)
    name: str = Field(min_length=2)
    phone: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=6)


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
