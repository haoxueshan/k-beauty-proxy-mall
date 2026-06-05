from datetime import datetime
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from crawler.oliveyoung_product import get_product_detail
from crawler.oliveyoung_search import search_products, sync_homepage_products
from schemas import (
    AuthResponse,
    CartItem,
    CartItemCreate,
    CartItemResponse,
    CrawlerSyncRequest,
    CrawlerSyncResponse,
    DeleteResponse,
    HealthResponse,
    LoginRequest,
    LogoutResponse,
    OrderCreate,
    OrderResponse,
    RegisterRequest,
    SearchResponse,
    TranslateRequest,
    TranslateResponse,
    UserPublic,
)
from services.llm_translate_service import translate_texts
from services.auth_service import get_user_by_token, login_user, logout_user, register_user
from services.order_service import add_cart_item, create_order, delete_cart_item, get_cart_items, list_cart_items, list_orders

app = FastAPI(title="Olive Young Proxy Shopping API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="olive-young-proxy-api", timestamp=datetime.utcnow())


def get_current_user(authorization: str | None = Header(default=None)) -> UserPublic:
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header is required")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Bearer token is required")
    return get_user_by_token(token)


@app.post("/api/auth/register", response_model=AuthResponse)
def auth_register(payload: RegisterRequest) -> AuthResponse:
    token, user = register_user(payload)
    return AuthResponse(token=token, user=user)


@app.post("/api/auth/login", response_model=AuthResponse)
def auth_login(payload: LoginRequest) -> AuthResponse:
    token, user = login_user(payload)
    return AuthResponse(token=token, user=user)


@app.get("/api/auth/me", response_model=UserPublic)
def auth_me(user: UserPublic = Depends(get_current_user)) -> UserPublic:
    return user


@app.post("/api/auth/logout", response_model=LogoutResponse)
def auth_logout(
    authorization: str | None = Header(default=None),
    user: UserPublic = Depends(get_current_user),
) -> LogoutResponse:
    _ = user
    if authorization is None:
        raise HTTPException(status_code=401, detail="Authorization header is required")
    _, _, token = authorization.partition(" ")
    logout_user(token)
    return LogoutResponse(success=True)


@app.get("/api/products/search", response_model=SearchResponse)
def product_search(keyword: str = "") -> SearchResponse:
    keyword_ko, items = search_products(keyword)
    return SearchResponse(
        keyword_original=keyword,
        keyword_ko=keyword_ko,
        count=len(items),
        items=items,
    )


@app.get("/api/products/{product_id}")
def product_detail(product_id: str):
    product = get_product_detail(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.post("/api/translate", response_model=TranslateResponse)
def translate_api(payload: TranslateRequest) -> TranslateResponse:
    result = translate_texts(
        payload.texts,
        source_language=payload.source_language,
        target_language=payload.target_language,
        fallback_texts=payload.texts,
    )
    return TranslateResponse(
        provider=result.provider,
        model=result.model,
        translations=result.translations,
    )


@app.post("/api/crawler/oliveyoung/sync", response_model=CrawlerSyncResponse)
def crawler_sync(payload: CrawlerSyncRequest) -> CrawlerSyncResponse:
    count, source = sync_homepage_products(payload.limit)
    return CrawlerSyncResponse(
        task_id=str(uuid4()),
        status=f"success:{source}:{count}",
        keyword=payload.keyword,
    )


@app.post("/api/cart/items", response_model=CartItemResponse)
def create_cart_item(payload: CartItemCreate, user: UserPublic = Depends(get_current_user)) -> CartItemResponse:
    cart_item_id = add_cart_item(
        user.id,
        payload.product_id,
        payload.quantity,
        payload.selected_option,
        payload.note,
    )
    return CartItemResponse(success=True, cart_item_id=cart_item_id)


@app.get("/api/cart/items", response_model=list[CartItem])
def cart_items(user: UserPublic = Depends(get_current_user)) -> list[CartItem]:
    return list_cart_items(user.id)


@app.delete("/api/cart/items/{cart_item_id}", response_model=DeleteResponse)
def remove_cart_item(cart_item_id: str, user: UserPublic = Depends(get_current_user)) -> DeleteResponse:
    deleted = delete_cart_item(user.id, cart_item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Cart item not found")
    return DeleteResponse(success=True)


@app.get("/api/orders")
def orders(user: UserPublic = Depends(get_current_user)):
    return list_orders(user.id)


@app.post("/api/orders", response_model=OrderResponse)
def create_proxy_order(payload: OrderCreate, user: UserPublic = Depends(get_current_user)) -> OrderResponse:
    cart_items = get_cart_items(user.id, payload.cart_item_ids)

    products = []
    for product_id in [item["product_id"] for item in cart_items]:
        product = get_product_detail(product_id)
        if product is not None:
            products.append(product)

    if not products:
        # For the scaffold we allow a fallback order body when the cart is mock-only.
        fallback = get_product_detail("oy-1")
        if fallback is not None:
            products.append(fallback)

    order = create_order(payload, cart_items, products, user.id)
    return OrderResponse(order_id=order.id, order_no=order.order_no, status=order.status)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
