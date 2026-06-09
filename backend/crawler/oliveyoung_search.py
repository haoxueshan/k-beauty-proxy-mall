from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import quote_plus, urljoin

from bs4 import BeautifulSoup

from crawler.parser import normalize_product
from schemas import Product, RawCrawlerProduct, ResultSetMeta, SearchResponse
from services.llm_translate_service import TranslationBatchResult
from services.translate_service import keyword_to_korean, translate_titles_to_chinese

OLIVE_YOUNG_MAIN_URL = "https://www.oliveyoung.co.kr/store/main/main.do?oy=0"
OLIVE_YOUNG_SEARCH_URL = "https://www.oliveyoung.co.kr/store/search/getSearchMain.do"
OLIVE_YOUNG_DETAIL_URL = "https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do"

PRODUCT_LINK_SELECTOR = "a[href*='getGoodsDetail.do'][href*='goodsNo=']"
DETAIL_META_READY_SELECTOR = 'meta[property="eg:itemName"]'
CACHE_TTL_SECONDS = 900
FALLBACK_RECOMMENDATION_LIMIT = 6
DEFAULT_PAGE_SIZE = 24
DEFAULT_SORT = "ranking"
MAX_PAGE_SIZE = 60
PAGE_READY_TIMEOUT_SECONDS = 60
PAGE_READY_POLL_SECONDS = 3

SOURCE_LIVE_SEARCH = "live_search"
SOURCE_LIVE_MAIN = "live_main"
SOURCE_LIVE_DETAIL = "live_detail"
SOURCE_CACHE = "cache"
SOURCE_SEED = "seed"


@dataclass
class CacheEntry:
    source: str
    source_type: str
    cache_layer: str
    fetched_at: datetime
    products: list[RawCrawlerProduct]
    page: int = 1
    page_size: int = DEFAULT_PAGE_SIZE
    sort: str = DEFAULT_SORT
    keyword_ko: str = ""
    oliveyoung_page_url: str | None = None


_home_cache: CacheEntry | None = None
_search_cache: dict[str, CacheEntry] = {}
_detail_cache: dict[str, CacheEntry] = {}
_last_page_fetch_debug: dict[str, object] = {}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _playwright_proxy_config() -> dict[str, str] | None:
    proxy_server = os.getenv("CRAWLER_PROXY_SERVER", "").strip()
    if not proxy_server:
        return None

    proxy: dict[str, str] = {"server": proxy_server}
    proxy_username = os.getenv("CRAWLER_PROXY_USERNAME", "").strip()
    proxy_password = os.getenv("CRAWLER_PROXY_PASSWORD", "").strip()
    if proxy_username:
        proxy["username"] = proxy_username
    if proxy_password:
        proxy["password"] = proxy_password
    return proxy


def _seed_raw_products() -> list[RawCrawlerProduct]:
    return [
        RawCrawlerProduct(
            goods_no="A000000000001",
            title_ko="라운드랩 자작나무 수분 선크림 50ml",
            brand_ko="라운드랩",
            image_url="https://images.unsplash.com/photo-1625772452859-1c03d5bf1137?auto=format&fit=crop&w=900&q=80",
            original_price_krw=26000,
            sale_price_krw=18900,
            category_ko="선케어",
            source_url=_build_detail_url("A000000000001"),
            raw_data={},
        ),
        RawCrawlerProduct(
            goods_no="A000000000002",
            title_ko="롬앤 쥬시 래스팅 틴트 23호",
            brand_ko="rom&nd",
            image_url="https://images.unsplash.com/photo-1586495777744-4413f21062fa?auto=format&fit=crop&w=900&q=80",
            original_price_krw=13000,
            sale_price_krw=9800,
            category_ko="립메이크업",
            source_url=_build_detail_url("A000000000002"),
            raw_data={},
        ),
        RawCrawlerProduct(
            goods_no="A000000000003",
            title_ko="아누아 어성초 77 토너 250ml",
            brand_ko="아누아",
            image_url="https://images.unsplash.com/photo-1556228578-dd6c474e2113?auto=format&fit=crop&w=900&q=80",
            original_price_krw=29000,
            sale_price_krw=21500,
            category_ko="스킨케어",
            source_url=_build_detail_url("A000000000003"),
            raw_data={},
        ),
    ]


def _normalize_page(value: int | None) -> int:
    try:
        page = int(value or 1)
    except (TypeError, ValueError):
        return 1
    return max(page, 1)


def _normalize_page_size(value: int | None) -> int:
    try:
        page_size = int(value or DEFAULT_PAGE_SIZE)
    except (TypeError, ValueError):
        return DEFAULT_PAGE_SIZE
    return min(max(page_size, 1), MAX_PAGE_SIZE)


def _normalize_sort(value: str | None) -> str:
    normalized = (value or DEFAULT_SORT).strip()
    return normalized or DEFAULT_SORT


def _build_search_url(keyword_ko: str, *, page: int = 1, sort: str = DEFAULT_SORT) -> str:
    # Assumption: Olive Young accepts pageIdx/sort as URL parameters on the search page.
    # If the site changes or exposes different pagination params, this function is the only place to update.
    query = f"query={quote_plus(keyword_ko)}&pageIdx={_normalize_page(page)}&sort={quote_plus(_normalize_sort(sort))}"
    return f"{OLIVE_YOUNG_SEARCH_URL}?{query}"


def _build_detail_url(goods_no: str) -> str:
    return f"{OLIVE_YOUNG_DETAIL_URL}?goodsNo={goods_no}"


def _extract_goods_no(href: str) -> str | None:
    match = re.search(r"goodsNo=([A-Z0-9]+)", href)
    if match:
        return match.group(1)

    match = re.search(r"(A\d{12})", href)
    return match.group(1) if match else None


def _normalize_goods_no(value: str) -> str | None:
    if not value:
        return None

    match = re.search(r"(A\d{12})", str(value).upper())
    return match.group(1) if match else None


def _parse_price(text: str | None) -> int | None:
    if not text:
        return None
    digits = re.sub(r"[^\d]", "", text)
    return int(digits) if digits else None


def _extract_brand(title_ko: str) -> str:
    cleaned = re.sub(r"^\[[^\]]+\]\s*", "", title_ko).strip()
    if " " in cleaned:
        return cleaned.split(" ", 1)[0]
    return cleaned[:24]


def _infer_category(title_ko: str) -> str:
    lowered = title_ko.lower()
    if any(keyword in lowered for keyword in ["선크림", "선블록", "선케어", "sunscreen", "sun cream"]):
        return "선케어"
    if any(keyword in lowered for keyword in ["립", "틴트", "립밤", "lip", "tint"]):
        return "립메이크업"
    if any(keyword in lowered for keyword in ["클렌징", "클렌저", "폼", "cleansing", "cleanser"]):
        return "클렌징"
    if any(keyword in lowered for keyword in ["마스크", "팩", "mask", "pack"]):
        return "마스크팩"
    if any(keyword in lowered for keyword in ["샴푸", "헤어", "hair", "scalp"]):
        return "헤어케어"
    if any(keyword in lowered for keyword in ["쿠션", "파운데이션", "베이스", "cushion", "foundation"]):
        return "베이스메이크업"
    return "스킨케어"


def _get_image_url(image_node) -> str:
    if not image_node:
        return ""

    for attr in ["src", "data-src", "data-original", "data-lazy-src"]:
        value = image_node.get(attr)
        if value and not value.startswith("data:"):
            return urljoin(OLIVE_YOUNG_MAIN_URL, value)

    return ""


def _find_product_container(anchor):
    node = anchor

    for _ in range(8):
        if not node:
            break
        if hasattr(node, "select_one") and (
            node.select_one(".tx_name")
            or node.select_one(".tx_brand")
            or node.select_one(".prd_price")
        ):
            return node
        node = node.parent

    return anchor


def _stamp_products(
    raw_products: list[RawCrawlerProduct],
    *,
    source: str,
    source_type: str,
    fetched_at: datetime,
    keyword_ko: str = "",
) -> list[RawCrawlerProduct]:
    stamped_products: list[RawCrawlerProduct] = []
    for product in raw_products:
        raw_data = dict(product.raw_data)
        raw_data.update(
            {
                "source": source,
                "origin_source_type": source_type,
                "last_synced_at": fetched_at.isoformat(),
                "synced_at": fetched_at.isoformat(),
                "keyword_ko": raw_data.get("keyword_ko") or keyword_ko or None,
            }
        )
        stamped_products.append(product.model_copy(update={"raw_data": raw_data}))
    return stamped_products


def _build_cache_entry(
    *,
    source: str,
    source_type: str,
    fetched_at: datetime,
    products: list[RawCrawlerProduct],
    cache_layer: str = "memory",
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    sort: str = DEFAULT_SORT,
    keyword_ko: str = "",
    oliveyoung_page_url: str | None = None,
) -> CacheEntry:
    return CacheEntry(
        source=source,
        source_type=source_type,
        cache_layer=cache_layer,
        fetched_at=fetched_at,
        products=_stamp_products(
            products,
            source=source,
            source_type=source_type,
            fetched_at=fetched_at,
            keyword_ko=keyword_ko,
        ),
        page=page,
        page_size=page_size,
        sort=sort,
        keyword_ko=keyword_ko,
        oliveyoung_page_url=oliveyoung_page_url,
    )


def _seed_cache_entry(limit: int = FALLBACK_RECOMMENDATION_LIMIT) -> CacheEntry:
    fetched_at = _utcnow()
    return _build_cache_entry(
        source="fallback-seed",
        source_type=SOURCE_SEED,
        fetched_at=fetched_at,
        products=_seed_raw_products()[:limit],
        cache_layer="seed",
    )


def _is_cache_fresh(entry: CacheEntry | None) -> bool:
    if entry is None:
        return False
    return (time.time() - entry.fetched_at.timestamp()) < CACHE_TTL_SECONDS


def _html_has_product_signal(html: str) -> bool:
    signals = (
        "goodsNo",
        "goods_no",
        "data-ref-goodsno",
        "getGoodsDetail.do",
        "prd_price",
        "tx_brand",
        "tx_name",
        "product",
        "goods",
    )
    return any(signal in html for signal in signals)


def _html_is_cloudflare_wait(html: str) -> bool:
    return any(
        signal in html
        for signal in (
            "window._cf_chl_opt",
            "cf_chl_rt_tk",
            "잠시만 기다려 주세요",
        )
    )


def _set_last_page_fetch_debug(**kwargs: object) -> None:
    global _last_page_fetch_debug
    _last_page_fetch_debug = kwargs


def get_last_page_fetch_debug() -> dict[str, object]:
    return dict(_last_page_fetch_debug)


def _fetch_page_html(
    url: str,
    ready_selector: str | None = PRODUCT_LINK_SELECTOR,
    *,
    scroll_steps: int = 3,
) -> str:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        launch_options: dict[str, object] = {
            "headless": True,
            "args": [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
            ],
        }
        proxy = _playwright_proxy_config()
        if proxy:
            launch_options["proxy"] = proxy

        browser = playwright.chromium.launch(**launch_options)
        try:
            page = browser.new_page(
                locale="ko-KR",
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/137.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1440, "height": 2200},
            )

            started_at = time.time()
            page.goto(url, wait_until="domcontentloaded", timeout=60000)

            html = page.content()
            reason = "waiting_for_products"
            while True:
                html = page.content()
                elapsed = time.time() - started_at
                if _html_has_product_signal(html):
                    reason = "product_signals_found"
                    break

                if _html_is_cloudflare_wait(html):
                    reason = "cloudflare_wait"
                else:
                    reason = "waiting_for_products"

                if elapsed >= PAGE_READY_TIMEOUT_SECONDS:
                    reason = "blocked_by_cloudflare" if _html_is_cloudflare_wait(html) else "no_products_after_wait"
                    break

                page.wait_for_timeout(PAGE_READY_POLL_SECONDS * 1000)

            for _ in range(max(scroll_steps, 0)):
                page.mouse.wheel(0, 1200)
                page.wait_for_timeout(800)

            final_html = page.content()
            _set_last_page_fetch_debug(
                reason=reason,
                title=page.title(),
                current_url=page.url,
                wait_seconds=round(time.time() - started_at, 2),
                product_count=final_html.count("goodsNo=") + final_html.count("data-ref-goodsno"),
                blocked_by_cloudflare=reason == "blocked_by_cloudflare",
                url=url,
            )
            return final_html
        finally:
            browser.close()


def _fetch_main_page_html() -> str:
    return _fetch_page_html(OLIVE_YOUNG_MAIN_URL)


def _fetch_search_page_html(
    keyword_ko: str,
    *,
    page: int = 1,
    sort: str = DEFAULT_SORT,
    scroll_steps: int = 3,
) -> str:
    return _fetch_page_html(_build_search_url(keyword_ko, page=page, sort=sort), scroll_steps=scroll_steps)


def _fetch_detail_page_html(goods_no: str) -> str:
    return _fetch_page_html(
        _build_detail_url(goods_no),
        ready_selector=DETAIL_META_READY_SELECTOR,
    )


def _parse_product_list_page_products(
    html: str,
    page_url: str,
    limit: int,
    *,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    keyword_ko: str = "",
    sort: str = DEFAULT_SORT,
    synced_at: datetime | None = None,
) -> list[RawCrawlerProduct]:
    soup = BeautifulSoup(html, "html.parser")
    seen_goods_no: set[str] = set()
    parsed_products: list[RawCrawlerProduct] = []

    for anchor in soup.select(PRODUCT_LINK_SELECTOR):
        href = anchor.get("href") or ""
        goods_no = anchor.get("data-ref-goodsno") or anchor.get("data-goods-no") or _extract_goods_no(href)
        if not goods_no or goods_no in seen_goods_no:
            continue

        container = _find_product_container(anchor)
        title_node = container.select_one(".tx_name")
        brand_node = container.select_one(".tx_brand")
        image_node = container.select_one("img") or anchor.select_one("img")

        title_ko = title_node.get_text(" ", strip=True) if title_node else ""
        if not title_ko and image_node:
            title_ko = (image_node.get("alt") or "").strip()
        if not title_ko:
            continue

        brand_ko = brand_node.get_text(" ", strip=True) if brand_node else _extract_brand(title_ko)
        image_url = _get_image_url(image_node)
        original_price = None
        sale_price = None

        org_node = container.select_one(".tx_org .tx_num")
        cur_node = container.select_one(".tx_cur .tx_num")
        if org_node:
            original_price = _parse_price(org_node.get_text(strip=True))
        if cur_node:
            sale_price = _parse_price(cur_node.get_text(strip=True))

        if sale_price is None:
            all_prices = [_parse_price(node.get_text(strip=True)) for node in container.select(".prd_price .tx_num")]
            all_prices = [price for price in all_prices if price is not None]
            if all_prices:
                original_price = all_prices[0]
                sale_price = all_prices[-1]

        if sale_price is None:
            sale_price = original_price or 0
        if original_price is None:
            original_price = sale_price

        local_rank = len(parsed_products) + 1
        source_rank = ((_normalize_page(page) - 1) * _normalize_page_size(page_size)) + local_rank
        price_node = container.select_one(".prd_price")
        raw_price_text = price_node.get_text(" ", strip=True) if price_node else ""

        parsed_products.append(
            RawCrawlerProduct(
                goods_no=goods_no,
                title_ko=title_ko,
                brand_ko=brand_ko,
                image_url=image_url,
                original_price_krw=original_price,
                sale_price_krw=sale_price,
                category_ko=_infer_category(title_ko),
                source_url=_build_detail_url(goods_no),
                raw_data={
                    "page_url": page_url,
                    "href": href,
                    "text": container.get_text(" ", strip=True),
                    "source_page": _normalize_page(page),
                    "source_rank": source_rank,
                    "keyword_ko": keyword_ko or None,
                    "sort": _normalize_sort(sort),
                    "synced_at": synced_at.isoformat() if synced_at else None,
                    "raw_price_text": raw_price_text or None,
                },
            )
        )
        seen_goods_no.add(goods_no)

        if len(parsed_products) >= limit:
            break

    return parsed_products


def _get_meta_content(soup: BeautifulSoup, property_name: str) -> str:
    node = soup.find("meta", attrs={"property": property_name})
    content = node.get("content") if node else ""
    return content.strip() if isinstance(content, str) else ""


def _clean_detail_title(title: str) -> str:
    return re.sub(r"\s*\|\s*올리브영\s*$", "", title).strip()


def _parse_detail_page_product(html: str, goods_no: str) -> RawCrawlerProduct | None:
    soup = BeautifulSoup(html, "html.parser")

    title_ko = _get_meta_content(soup, "eg:itemName")
    if not title_ko:
        title_ko = _clean_detail_title(_get_meta_content(soup, "og:title"))
    if not title_ko and soup.title and soup.title.string:
        title_ko = _clean_detail_title(soup.title.string)
    if not title_ko:
        return None

    brand_ko = _get_meta_content(soup, "eg:brandName") or _extract_brand(title_ko)
    image_url = _get_meta_content(soup, "og:image")
    original_price = _parse_price(_get_meta_content(soup, "eg:originalPrice"))
    sale_price = _parse_price(_get_meta_content(soup, "eg:salePrice"))

    if sale_price is None:
        return None
    if original_price is None:
        original_price = sale_price

    return RawCrawlerProduct(
        goods_no=goods_no,
        title_ko=title_ko,
        brand_ko=brand_ko,
        image_url=image_url,
        original_price_krw=original_price,
        sale_price_krw=sale_price,
        category_ko=_infer_category(title_ko),
        source_url=_build_detail_url(goods_no),
        raw_data={"goods_no": goods_no},
    )


def _fetch_live_main_entry(limit: int = DEFAULT_PAGE_SIZE) -> CacheEntry:
    fetched_at = _utcnow()
    html = _fetch_main_page_html()
    raw_products = _parse_product_list_page_products(
        html,
        OLIVE_YOUNG_MAIN_URL,
        limit=limit,
        page=1,
        page_size=limit,
        synced_at=fetched_at,
    )
    if not raw_products:
        raise RuntimeError("Olive Young main page returned no products")
    return _build_cache_entry(
        source="oliveyoung-main",
        source_type=SOURCE_LIVE_MAIN,
        fetched_at=fetched_at,
        products=raw_products,
        page=1,
        page_size=limit,
        oliveyoung_page_url=OLIVE_YOUNG_MAIN_URL,
    )


def _fetch_live_search_entry(
    keyword_ko: str,
    *,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    sort: str = DEFAULT_SORT,
) -> CacheEntry:
    page = _normalize_page(page)
    page_size = _normalize_page_size(page_size)
    sort = _normalize_sort(sort)
    fetched_at = _utcnow()
    search_url = _build_search_url(keyword_ko, page=page, sort=sort)
    fetch_limit = page * page_size
    scroll_steps = min(max(3, page + 3), 10)
    html = _fetch_search_page_html(keyword_ko, page=page, sort=sort, scroll_steps=scroll_steps)
    all_products = _parse_product_list_page_products(
        html,
        search_url,
        limit=fetch_limit,
        page=1,
        page_size=page_size,
        keyword_ko=keyword_ko,
        sort=sort,
        synced_at=fetched_at,
    )
    if not all_products:
        debug = get_last_page_fetch_debug()
        reason = str(debug.get("reason") or "no_products_after_wait")
        if reason in {"blocked_by_cloudflare", "no_products_after_wait"}:
            raise RuntimeError(reason)

    offset = (page - 1) * page_size
    raw_products = []
    for product in all_products[offset : offset + page_size]:
        raw_data = dict(product.raw_data)
        raw_data["source_page"] = page
        raw_data["source_rank"] = raw_data.get("source_rank") or (len(raw_products) + offset + 1)
        raw_products.append(product.model_copy(update={"raw_data": raw_data}))
    return _build_cache_entry(
        source="oliveyoung-search",
        source_type=SOURCE_LIVE_SEARCH,
        fetched_at=fetched_at,
        products=raw_products,
        page=page,
        page_size=page_size,
        sort=sort,
        keyword_ko=keyword_ko,
        oliveyoung_page_url=search_url,
    )


def _fetch_live_detail_entry(goods_no: str) -> CacheEntry | None:
    fetched_at = _utcnow()
    html = _fetch_detail_page_html(goods_no)
    raw_product = _parse_detail_page_product(html, goods_no)
    if raw_product is None:
        return None
    return _build_cache_entry(
        source="oliveyoung-detail",
        source_type=SOURCE_LIVE_DETAIL,
        fetched_at=fetched_at,
        products=[raw_product],
    )


def _get_home_entry(limit: int = DEFAULT_PAGE_SIZE) -> tuple[CacheEntry, bool]:
    global _home_cache
    if _is_cache_fresh(_home_cache):
        return _home_cache, True

    try:
        _home_cache = _fetch_live_main_entry(limit=limit)
    except Exception:
        _home_cache = _seed_cache_entry(limit=limit)
    return _home_cache, False


def _get_recommendation_entry(limit: int = FALLBACK_RECOMMENDATION_LIMIT) -> CacheEntry:
    entry, cache_hit = _get_home_entry(limit=limit)
    source_type = SOURCE_CACHE if cache_hit and entry.source_type != SOURCE_SEED else entry.source_type
    cache_layer = "memory" if source_type == SOURCE_CACHE else ("seed" if entry.source_type == SOURCE_SEED else "none")
    if len(entry.products) <= limit:
        return CacheEntry(
            source=entry.source,
            source_type=source_type,
            cache_layer=cache_layer,
            fetched_at=entry.fetched_at,
            products=entry.products,
        )
    return CacheEntry(
        source=entry.source,
        source_type=source_type,
        cache_layer=cache_layer,
        fetched_at=entry.fetched_at,
        products=entry.products[:limit],
    )


def _get_search_entry(
    keyword_ko: str,
    *,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    sort: str = DEFAULT_SORT,
) -> tuple[CacheEntry, bool]:
    page = _normalize_page(page)
    page_size = _normalize_page_size(page_size)
    sort = _normalize_sort(sort)
    cache_key = f"{keyword_ko.strip().lower()}|page={page}|size={page_size}|sort={sort}"
    cached_entry = _search_cache.get(cache_key)
    if _is_cache_fresh(cached_entry):
        return cached_entry, True

    live_entry = _fetch_live_search_entry(keyword_ko, page=page, page_size=page_size, sort=sort)
    _search_cache[cache_key] = live_entry
    return live_entry, False


def _normalize_raw_products(
    raw_products: list[RawCrawlerProduct],
    *,
    served_source_type: str,
    last_synced_at: datetime | None,
) -> list[Product]:
    if not raw_products:
        return []

    translation_result = translate_titles_to_chinese([item.title_ko for item in raw_products])
    return [
        normalize_product(
            item,
            title_zh,
            translation_result=TranslationBatchResult(
                translations=[title_zh],
                provider=translation_result.provider,
                model=translation_result.model,
            ),
            source_type=served_source_type,
            last_synced_at=last_synced_at,
        )
        for item, title_zh in zip(raw_products, translation_result.translations)
    ]


def _build_result_meta(
    *,
    products: list[Product],
    source: str,
    source_type: str,
    cache_layer: str,
    last_synced_at: datetime | None,
) -> ResultSetMeta:
    if not products:
        return ResultSetMeta(
            source=source,
            source_type=source_type,
            cache_layer=cache_layer,
            last_synced_at=last_synced_at,
            item_count=0,
            completeness_score=0,
            price_confidence=0,
            translation_confidence=0,
        )

    item_count = len(products)
    return ResultSetMeta(
        source=source,
        source_type=source_type,
        cache_layer=cache_layer,
        last_synced_at=last_synced_at,
        item_count=item_count,
        completeness_score=round(sum(item.metadata.completeness_score for item in products) / item_count, 2),
        price_confidence=round(sum(item.metadata.price_confidence for item in products) / item_count, 2),
        translation_confidence=round(sum(item.metadata.translation_confidence for item in products) / item_count, 2),
    )


def _build_search_response(
    *,
    keyword_original: str,
    keyword_ko: str,
    page: int,
    page_size: int,
    sort: str,
    oliveyoung_page_url: str | None,
    primary_products: list[RawCrawlerProduct],
    primary_source: str,
    primary_source_type: str,
    primary_cache_layer: str,
    primary_last_synced_at: datetime | None,
    fallback_products: list[RawCrawlerProduct] | None = None,
    fallback_source: str | None = None,
    fallback_source_type: str | None = None,
    fallback_cache_layer: str = "none",
    fallback_last_synced_at: datetime | None = None,
    error: str | None = None,
) -> SearchResponse:
    items = _normalize_raw_products(
        primary_products,
        served_source_type=primary_source_type,
        last_synced_at=primary_last_synced_at,
    )
    fallback_items = _normalize_raw_products(
        fallback_products or [],
        served_source_type=fallback_source_type or SOURCE_SEED,
        last_synced_at=fallback_last_synced_at,
    )
    has_next = len(items) >= page_size and primary_source_type != SOURCE_SEED
    source_rank_start = ((page - 1) * page_size) + 1 if items else None

    return SearchResponse(
        keyword_original=keyword_original,
        keyword_ko=keyword_ko,
        count=len(items),
        items=items,
        source=primary_source,
        source_type=primary_source_type,
        result_meta=_build_result_meta(
            products=items,
            source=primary_source,
            source_type=primary_source_type,
            cache_layer=primary_cache_layer,
            last_synced_at=primary_last_synced_at,
        ),
        fallback_count=len(fallback_items),
        fallback_items=fallback_items,
        fallback_meta=(
            _build_result_meta(
                products=fallback_items,
                source=fallback_source or "fallback-seed",
                source_type=fallback_source_type or SOURCE_SEED,
                cache_layer=fallback_cache_layer,
                last_synced_at=fallback_last_synced_at,
            )
            if fallback_items
            else None
        ),
        page=page,
        page_size=page_size,
        sort=sort,
        has_next=has_next,
        next_page=page + 1 if has_next else None,
        oliveyoung_page_url=oliveyoung_page_url,
        source_rank_start=source_rank_start,
        synced_pages=[page] if items else [],
        error=error,
    )


def get_cached_products() -> list[Product]:
    seen_goods_no: set[str] = set()
    cached_products: list[RawCrawlerProduct] = []
    cache_entries = [entry for entry in [_detail_cache.get(key) for key in sorted(_detail_cache.keys())] if entry]

    if _home_cache is not None:
        cache_entries.append(_home_cache)
    cache_entries.extend(_search_cache.values())

    freshest_synced_at: datetime | None = None
    for entry in cache_entries:
        freshest_synced_at = max(freshest_synced_at, entry.fetched_at) if freshest_synced_at else entry.fetched_at
        for product in entry.products:
            if product.goods_no in seen_goods_no:
                continue
            cached_products.append(product)
            seen_goods_no.add(product.goods_no)

    return _normalize_raw_products(
        cached_products,
        served_source_type=SOURCE_CACHE,
        last_synced_at=freshest_synced_at,
    )


def get_product_by_goods_no(goods_no: str) -> Product | None:
    normalized_goods_no = _normalize_goods_no(goods_no)
    if not normalized_goods_no:
        return None

    cached_entry = _detail_cache.get(normalized_goods_no)
    if _is_cache_fresh(cached_entry) and cached_entry is not None:
        products = _normalize_raw_products(
            cached_entry.products,
            served_source_type=SOURCE_CACHE,
            last_synced_at=cached_entry.fetched_at,
        )
        return products[0] if products else None

    try:
        live_entry = _fetch_live_detail_entry(normalized_goods_no)
    except Exception:
        return None

    if live_entry is None:
        return None

    _detail_cache[normalized_goods_no] = live_entry
    products = _normalize_raw_products(
        live_entry.products,
        served_source_type=SOURCE_LIVE_DETAIL,
        last_synced_at=live_entry.fetched_at,
    )
    return products[0] if products else None


def sync_homepage_products(limit: int = DEFAULT_PAGE_SIZE) -> tuple[int, str]:
    global _home_cache
    try:
        _home_cache = _fetch_live_main_entry(limit=limit)
    except Exception:
        _home_cache = _seed_cache_entry(limit=limit)
    return len(_home_cache.products), _home_cache.source


def sync_oliveyoung_products(
    keyword: str,
    *,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    sort: str = DEFAULT_SORT,
) -> tuple[int, str]:
    normalized_keyword = keyword.strip()
    if not normalized_keyword or normalized_keyword.lower() == "homepage":
        return sync_homepage_products(limit=page_size)

    keyword_ko = keyword_to_korean(keyword)
    entry = _fetch_live_search_entry(keyword_ko, page=page, page_size=page_size, sort=sort)
    cache_key = f"{keyword_ko.strip().lower()}|page={entry.page}|size={entry.page_size}|sort={entry.sort}"
    _search_cache[cache_key] = entry
    return len(entry.products), entry.source


def search_products(keyword: str) -> tuple[str, list[Product]]:
    response = search_products_with_source(keyword)
    return response.keyword_ko, response.items


def search_products_with_source(
    keyword: str,
    *,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    sort: str = DEFAULT_SORT,
) -> SearchResponse:
    normalized_keyword = keyword.strip()
    keyword_ko = keyword_to_korean(keyword)
    has_keyword = bool(normalized_keyword)
    page = _normalize_page(page)
    page_size = _normalize_page_size(page_size)
    sort = _normalize_sort(sort)

    if has_keyword:
        try:
            search_entry, cache_hit = _get_search_entry(keyword_ko, page=page, page_size=page_size, sort=sort)
        except Exception as exc:
            recommendation_entry = _get_recommendation_entry()
            return _build_search_response(
                keyword_original=keyword,
                keyword_ko=keyword_ko,
                page=page,
                page_size=page_size,
                sort=sort,
                oliveyoung_page_url=_build_search_url(keyword_ko, page=page, sort=sort),
                primary_products=[],
                primary_source="oliveyoung-search-error",
                primary_source_type=SOURCE_LIVE_SEARCH,
                primary_cache_layer="none",
                primary_last_synced_at=None,
                fallback_products=recommendation_entry.products,
                fallback_source=recommendation_entry.source,
                fallback_source_type=recommendation_entry.source_type,
                fallback_cache_layer=recommendation_entry.cache_layer,
                fallback_last_synced_at=recommendation_entry.fetched_at,
                error=str(exc),
            )

        primary_source_type = SOURCE_CACHE if cache_hit else SOURCE_LIVE_SEARCH
        primary_cache_layer = search_entry.cache_layer if cache_hit else "none"
        primary_source = search_entry.source if search_entry.products else "oliveyoung-search-empty"

        if search_entry.products:
            return _build_search_response(
                keyword_original=keyword,
                keyword_ko=keyword_ko,
                page=page,
                page_size=page_size,
                sort=sort,
                oliveyoung_page_url=search_entry.oliveyoung_page_url,
                primary_products=search_entry.products,
                primary_source=primary_source,
                primary_source_type=primary_source_type,
                primary_cache_layer=primary_cache_layer,
                primary_last_synced_at=search_entry.fetched_at,
            )

        recommendation_entry = _get_recommendation_entry()
        return _build_search_response(
            keyword_original=keyword,
            keyword_ko=keyword_ko,
            page=page,
            page_size=page_size,
            sort=sort,
            oliveyoung_page_url=search_entry.oliveyoung_page_url,
            primary_products=[],
            primary_source="oliveyoung-search-empty",
            primary_source_type=SOURCE_LIVE_SEARCH,
            primary_cache_layer="none",
            primary_last_synced_at=search_entry.fetched_at,
            fallback_products=recommendation_entry.products,
            fallback_source=recommendation_entry.source,
            fallback_source_type=recommendation_entry.source_type,
            fallback_cache_layer=recommendation_entry.cache_layer,
            fallback_last_synced_at=recommendation_entry.fetched_at,
        )

    home_entry, cache_hit = _get_home_entry(limit=page_size)
    primary_source_type = SOURCE_CACHE if cache_hit and home_entry.source_type != SOURCE_SEED else home_entry.source_type
    primary_cache_layer = "memory" if primary_source_type == SOURCE_CACHE else ("seed" if home_entry.source_type == SOURCE_SEED else "none")
    return _build_search_response(
        keyword_original=keyword,
        keyword_ko=keyword_ko,
        page=1,
        page_size=page_size,
        sort=sort,
        oliveyoung_page_url=home_entry.oliveyoung_page_url or OLIVE_YOUNG_MAIN_URL,
        primary_products=home_entry.products,
        primary_source=home_entry.source,
        primary_source_type=primary_source_type,
        primary_cache_layer=primary_cache_layer,
        primary_last_synced_at=home_entry.fetched_at,
    )


def diagnose_oliveyoung_search(keyword: str = "sunscreen", limit: int = 3) -> dict[str, object]:
    started_at = time.time()
    response = search_products_with_source(keyword, page_size=max(limit, 1))
    fetch_debug = get_last_page_fetch_debug()
    ok = bool(response.items)
    reason = "ok" if ok else (response.error or fetch_debug.get("reason") or "no_products_after_wait")
    return {
        "ok": ok,
        "reason": reason,
        "title": fetch_debug.get("title"),
        "current_url": fetch_debug.get("current_url"),
        "wait_seconds": fetch_debug.get("wait_seconds"),
        "product_count": response.count,
        "keyword_original": response.keyword_original,
        "keyword_ko": response.keyword_ko,
        "source": response.source,
        "source_type": response.source_type,
        "count": response.count,
        "fallback_count": response.fallback_count,
        "last_synced_at": response.result_meta.last_synced_at.isoformat() if response.result_meta.last_synced_at else None,
        "first_goods_no": response.items[0].goods_no if response.items else None,
        "elapsed_seconds": round(time.time() - started_at, 2),
        "proxy_enabled": bool(_playwright_proxy_config()),
        "error": response.error,
        "fallback_source": response.fallback_meta.source if response.fallback_meta else None,
        "fallback_source_type": response.fallback_meta.source_type if response.fallback_meta else None,
        "items_preview": [
            {
                "goods_no": product.goods_no,
                "source_type": product.metadata.source_type,
                "completeness_score": product.metadata.completeness_score,
                "price_confidence": product.metadata.price_confidence,
                "translation_confidence": product.metadata.translation_confidence,
            }
            for product in response.items[:limit]
        ],
    }
