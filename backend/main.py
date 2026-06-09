import logging
import os
import socket
from datetime import datetime
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from crawler.oliveyoung_product import get_product_detail, get_products_by_ids
from crawler.oliveyoung_search import diagnose_oliveyoung_search, search_products_with_source, sync_oliveyoung_products
from db.supabase_client import get_supabase_settings
from schemas import (
    AdminOrder,
    AuthResponse,
    CartDisplayItem,
    CartItem,
    CartItemCreate,
    CartItemUpdate,
    CartItemResponse,
    CrawlerSyncRequest,
    CrawlerSyncResponse,
    DeleteResponse,
    HealthResponse,
    LoginRequest,
    LogoutResponse,
    OrderCreate,
    OrderResponse,
    ReadinessCheck,
    ReadinessResponse,
    RegisterRequest,
    SearchResponse,
    TranslateRequest,
    TranslateResponse,
    UserPublic,
)
from settings import configure_logging, get_settings
from services.llm_translate_service import translate_texts
from services.auth_service import get_user_by_token, login_user, logout_user, register_user
from services.order_service import (
    add_cart_item,
    create_order,
    delete_cart_item,
    delete_order,
    get_cart_items,
    list_cart_items,
    list_admin_orders,
    list_orders,
    update_cart_item,
)

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)


def _is_port_available(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
        except OSError:
            return False
    return True


def _resolve_run_port(host: str, preferred_port: int, search_limit: int = 20) -> int:
    if _is_port_available(host, preferred_port):
        return preferred_port

    for candidate_port in range(preferred_port + 1, preferred_port + search_limit + 1):
        if _is_port_available(host, candidate_port):
            print(
                f"[startup] Port {preferred_port} is unavailable on {host}, "
                f"falling back to {candidate_port}."
            )
            return candidate_port

    raise RuntimeError(
        f"No available port found from {preferred_port} to {preferred_port + search_limit} on {host}."
    )


app = FastAPI(title=settings.app_name, version=settings.app_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=not settings.allow_all_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

if not settings.allow_all_hosts:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts)


def _build_readiness_response() -> ReadinessResponse:
    supabase = get_supabase_settings()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    checks = [
        ReadinessCheck(
            name="supabase_url",
            status="ok" if bool(supabase["url"]) else "error",
            detail="Configured" if supabase["url"] else "Missing SUPABASE_URL",
        ),
        ReadinessCheck(
            name="supabase_service_role",
            status=(
                "ok"
                if supabase["service_role_key"] and not supabase["service_role_key"].startswith("sb_publishable_")
                else "error"
            ),
            detail=(
                "Configured"
                if supabase["service_role_key"] and not supabase["service_role_key"].startswith("sb_publishable_")
                else "Missing or invalid SUPABASE_SERVICE_ROLE_KEY"
            ),
        ),
        ReadinessCheck(
            name="allowed_origins",
            status="ok" if settings.allowed_origins else "error",
            detail=",".join(settings.allowed_origins) if settings.allowed_origins else "No ALLOWED_ORIGINS configured",
        ),
        ReadinessCheck(
            name="openai_api_key",
            status="ok" if bool(openai_api_key) else "warning",
            detail="Configured" if openai_api_key else "Optional: translation falls back locally",
        ),
    ]
    overall_status = "ok" if all(check.status != "error" for check in checks) else "error"
    return ReadinessResponse(
        status=overall_status,
        service=settings.app_name,
        environment=settings.app_env,
        timestamp=datetime.utcnow(),
        checks=checks,
    )


@app.on_event("startup")
def log_startup_configuration() -> None:
    logger.info(
        "Starting %s env=%s host=%s port=%s reload=%s trusted_hosts=%s allowed_origins=%s",
        settings.app_name,
        settings.app_env,
        settings.host,
        settings.port,
        settings.uvicorn_reload,
        settings.trusted_hosts,
        settings.allowed_origins,
    )


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service=settings.app_name, timestamp=datetime.utcnow())


@app.get("/health/ready", response_model=ReadinessResponse)
def readiness():
    response = _build_readiness_response()
    status_code = 200 if response.status == "ok" else 503
    return JSONResponse(status_code=status_code, content=response.model_dump(mode="json"))


def get_current_user(authorization: str | None = Header(default=None)) -> UserPublic:
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header is required")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Bearer token is required")
    return get_user_by_token(token)


def require_admin(user: UserPublic = Depends(get_current_user)) -> UserPublic:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin permission is required")
    return user


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
def product_search(
    keyword: str = "",
    page: int = 1,
    page_size: int = 24,
    sort: str = "ranking",
) -> SearchResponse:
    return search_products_with_source(keyword, page=page, page_size=page_size, sort=sort)


@app.get("/api/oliveyoung/search", response_model=SearchResponse)
def oliveyoung_search(
    q: str = "",
    page: int = 1,
    page_size: int = 24,
    sort: str = "ranking",
) -> SearchResponse:
    return search_products_with_source(q, page=page, page_size=page_size, sort=sort)


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
    page_size = payload.page_size or payload.limit
    count, source = sync_oliveyoung_products(
        payload.keyword,
        page=payload.page,
        page_size=page_size,
        sort=payload.sort,
    )
    return CrawlerSyncResponse(
        task_id=str(uuid4()),
        status=f"success:{source}:{count}",
        keyword=payload.keyword,
        count=count,
        source=source,
    )


@app.get("/api/crawler/oliveyoung/diagnostics")
def crawler_diagnostics(keyword: str = "sunscreen"):
    return diagnose_oliveyoung_search(keyword)


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


@app.get("/api/cart/items/display", response_model=list[CartDisplayItem])
def cart_display_items(user: UserPublic = Depends(get_current_user)) -> list[CartDisplayItem]:
    items = list_cart_items(user.id)
    products_by_id = get_products_by_ids([item.product_id for item in items])
    return [
        CartDisplayItem(**item.model_dump(), product=products_by_id[item.product_id])
        for item in items
        if item.product_id in products_by_id
    ]


@app.patch("/api/cart/items/{cart_item_id}", response_model=CartItem)
def patch_cart_item(
    cart_item_id: str,
    payload: CartItemUpdate,
    user: UserPublic = Depends(get_current_user),
) -> CartItem:
    item = update_cart_item(user.id, cart_item_id, payload.quantity, payload.note)
    if item is None:
        raise HTTPException(status_code=404, detail="Cart item not found")
    return item


@app.delete("/api/cart/items/{cart_item_id}", response_model=DeleteResponse)
def remove_cart_item(cart_item_id: str, user: UserPublic = Depends(get_current_user)) -> DeleteResponse:
    deleted = delete_cart_item(user.id, cart_item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Cart item not found")
    return DeleteResponse(success=True)


@app.get("/api/orders")
def orders(user: UserPublic = Depends(get_current_user)):
    return list_orders(user.id)


@app.get("/api/admin/orders", response_model=list[AdminOrder])
def admin_orders(user: UserPublic = Depends(require_admin)) -> list[AdminOrder]:
    _ = user
    return list_admin_orders()


@app.delete("/api/orders/{order_id}", response_model=DeleteResponse)
def remove_order(order_id: str, user: UserPublic = Depends(get_current_user)) -> DeleteResponse:
    deleted = delete_order(user.id, order_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Order not found")
    return DeleteResponse(success=True)


@app.post("/api/orders", response_model=OrderResponse)
def create_proxy_order(payload: OrderCreate, user: UserPublic = Depends(get_current_user)) -> OrderResponse:
    cart_items = get_cart_items(user.id, payload.cart_item_ids)
    if not cart_items:
        raise HTTPException(status_code=400, detail="No valid cart items selected")

    products = []
    for product_id in [item["product_id"] for item in cart_items]:
        product = get_product_detail(product_id)
        if product is not None:
            products.append(product)

    if not products:
        raise HTTPException(status_code=400, detail="Selected cart items could not be resolved to products")

    order = create_order(payload, cart_items, products, user.id)
    return OrderResponse(order_id=order.id, order_no=order.order_no, status=order.status)

if __name__ == "__main__":
    import uvicorn

    host = settings.host
    port = settings.port
    if settings.port_auto_fallback:
        port = _resolve_run_port(host, port)
    elif not _is_port_available(host, port):
        raise RuntimeError(
            f"Configured port {port} is unavailable on {host}. "
            "Set PORT_AUTO_FALLBACK=true only for local debugging."
        )

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=settings.uvicorn_reload,
    )
