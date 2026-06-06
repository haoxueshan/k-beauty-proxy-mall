from __future__ import annotations

import re
import time
from urllib.parse import quote_plus, urljoin

from bs4 import BeautifulSoup

from crawler.parser import normalize_product
from schemas import Product, RawCrawlerProduct
from services.translate_service import keyword_to_korean, translate_titles_to_chinese

OLIVE_YOUNG_MAIN_URL = "https://www.oliveyoung.co.kr/store/main/main.do?oy=0"
OLIVE_YOUNG_SEARCH_URL = "https://www.oliveyoung.co.kr/store/search/getSearchMain.do"
OLIVE_YOUNG_DETAIL_URL = "https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do"

PRODUCT_LINK_SELECTOR = "a[href*='getGoodsDetail.do'][href*='goodsNo=']"
DETAIL_META_READY_SELECTOR = 'meta[property="eg:itemName"]'
CACHE_TTL_SECONDS = 900

_product_cache: dict[str, object] = {
    "fetched_at": 0.0,
    "products": [],
}
_search_cache: dict[str, dict[str, object]] = {}


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
            raw_data={"source": "fallback-seed"},
        ),
        RawCrawlerProduct(
            goods_no="A000000000002",
            title_ko="rom&nd 쥬시 래스팅 틴트 23호",
            brand_ko="rom&nd",
            image_url="https://images.unsplash.com/photo-1586495777744-4413f21062fa?auto=format&fit=crop&w=900&q=80",
            original_price_krw=13000,
            sale_price_krw=9800,
            category_ko="립메이크업",
            source_url=_build_detail_url("A000000000002"),
            raw_data={"source": "fallback-seed"},
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
            raw_data={"source": "fallback-seed"},
        ),
    ]


def _build_search_url(keyword_ko: str) -> str:
    return f"{OLIVE_YOUNG_SEARCH_URL}?query={quote_plus(keyword_ko)}"


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
    if any(keyword in lowered for keyword in ["선크림", "선스틱", "선케어", "sun", "sunscreen"]):
        return "선케어"
    if any(keyword in lowered for keyword in ["틴트", "립", "글로스", "lip"]):
        return "립메이크업"
    if any(keyword in lowered for keyword in ["클렌징", "클렌저", "폼", "오일", "clean"]):
        return "클렌징"
    if any(keyword in lowered for keyword in ["마스크", "팩", "패드", "mask"]):
        return "마스크팩"
    if any(keyword in lowered for keyword in ["샴푸", "트리트먼트", "헤어", "hair"]):
        return "헤어케어"
    if any(keyword in lowered for keyword in ["쿠션", "파운데이션", "프라이머", "베이스"]):
        return "베이스 메이크업"
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


def _fetch_page_html(url: str, ready_selector: str | None = PRODUCT_LINK_SELECTOR) -> str:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
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

            page.goto(url, wait_until="domcontentloaded", timeout=60000)

            if ready_selector:
                try:
                    page.wait_for_selector(ready_selector, timeout=15000)
                except Exception:
                    page.wait_for_timeout(3000)
            else:
                page.wait_for_timeout(3000)

            for _ in range(3):
                page.mouse.wheel(0, 1200)
                page.wait_for_timeout(800)

            return page.content()
        finally:
            browser.close()


def _fetch_main_page_html() -> str:
    return _fetch_page_html(OLIVE_YOUNG_MAIN_URL)


def _fetch_search_page_html(keyword_ko: str) -> str:
    return _fetch_page_html(_build_search_url(keyword_ko))


def _fetch_detail_page_html(goods_no: str) -> str:
    return _fetch_page_html(
        _build_detail_url(goods_no),
        ready_selector=DETAIL_META_READY_SELECTOR,
    )


def _parse_product_list_page_products(
    html: str,
    page_url: str,
    limit: int = 24,
) -> list[RawCrawlerProduct]:
    soup = BeautifulSoup(html, "html.parser")
    seen_goods_no: set[str] = set()
    parsed_products: list[RawCrawlerProduct] = []
    source = "oliveyoung-search" if page_url.startswith(OLIVE_YOUNG_SEARCH_URL) else "oliveyoung-main"

    for anchor in soup.select(PRODUCT_LINK_SELECTOR):
        href = anchor.get("href") or ""
        goods_no = (
            anchor.get("data-ref-goodsno")
            or anchor.get("data-goods-no")
            or _extract_goods_no(href)
        )
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
                    "source": source,
                    "page_url": page_url,
                    "href": href,
                    "text": container.get_text(" ", strip=True),
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
        raw_data={
            "source": "oliveyoung-detail",
            "goods_no": goods_no,
            "image_url": image_url,
        },
    )


def _parse_main_page_products(html: str, limit: int = 24) -> list[RawCrawlerProduct]:
    return _parse_product_list_page_products(
        html=html,
        page_url=OLIVE_YOUNG_MAIN_URL,
        limit=limit,
    )


def _get_search_products(keyword_ko: str, limit: int = 24) -> list[RawCrawlerProduct]:
    search_url = _build_search_url(keyword_ko)
    html = _fetch_search_page_html(keyword_ko)
    return _parse_product_list_page_products(
        html=html,
        page_url=search_url,
        limit=limit,
    )


def _get_cached_search_products(keyword_ko: str, limit: int = 24) -> list[RawCrawlerProduct]:
    now = time.time()
    cache_key = keyword_ko.strip().lower()

    cached = _search_cache.get(cache_key)
    if cached:
        fetched_at = float(cached.get("fetched_at", 0.0))
        products = cached.get("products")
        if products and (now - fetched_at) < CACHE_TTL_SECONDS:
            return products  # type: ignore[return-value]

    products = _get_search_products(keyword_ko, limit=limit)
    if products:
        _search_cache[cache_key] = {
            "fetched_at": now,
            "products": products,
        }

    return products


def _get_live_or_seed_products(limit: int = 24) -> list[RawCrawlerProduct]:
    now = time.time()
    cached_products = _product_cache.get("products")
    fetched_at = float(_product_cache.get("fetched_at", 0.0))
    if cached_products and (now - fetched_at) < CACHE_TTL_SECONDS:
        return cached_products  # type: ignore[return-value]

    try:
        html = _fetch_main_page_html()
        live_products = _parse_main_page_products(html, limit=limit)
        if live_products:
            _product_cache["products"] = live_products
            _product_cache["fetched_at"] = now
            return live_products
    except Exception:
        pass

    fallback_products = _seed_raw_products()
    _product_cache["products"] = fallback_products
    _product_cache["fetched_at"] = now
    return fallback_products


def _normalize_raw_products(raw_products: list[RawCrawlerProduct]) -> list[Product]:
    translation_result = translate_titles_to_chinese([item.title_ko for item in raw_products])
    return [
        normalize_product(item, title_zh)
        for item, title_zh in zip(raw_products, translation_result.translations)
    ]


def _upsert_product_cache(product: RawCrawlerProduct) -> None:
    cached_products = _product_cache.get("products") or []
    deduped_products = [item for item in cached_products if item.goods_no != product.goods_no]
    _product_cache["products"] = [product, *deduped_products]
    _product_cache["fetched_at"] = time.time()


def _raw_products_source(raw_products: list[RawCrawlerProduct], default_source: str) -> str:
    for item in raw_products:
        source = item.raw_data.get("source")
        if isinstance(source, str) and source:
            return source
    return default_source


def get_cached_products() -> list[Product]:
    seen_goods_no: set[str] = set()
    raw_products: list[RawCrawlerProduct] = []

    for item in _product_cache.get("products") or []:
        if item.goods_no not in seen_goods_no:
            raw_products.append(item)
            seen_goods_no.add(item.goods_no)

    for cached in _search_cache.values():
        for item in cached.get("products") or []:
            if item.goods_no not in seen_goods_no:
                raw_products.append(item)
                seen_goods_no.add(item.goods_no)

    return _normalize_raw_products(raw_products)


def get_product_by_goods_no(goods_no: str) -> Product | None:
    normalized_goods_no = _normalize_goods_no(goods_no)
    if not normalized_goods_no:
        return None

    try:
        html = _fetch_detail_page_html(normalized_goods_no)
        raw_product = _parse_detail_page_product(html, normalized_goods_no)
    except Exception:
        return None

    if raw_product is None:
        return None

    _upsert_product_cache(raw_product)
    normalized_products = _normalize_raw_products([raw_product])
    return normalized_products[0] if normalized_products else None


def sync_homepage_products(limit: int = 24) -> tuple[int, str]:
    try:
        html = _fetch_main_page_html()
        live_products = _parse_main_page_products(html, limit=limit)
        if live_products:
            _product_cache["products"] = live_products
            _product_cache["fetched_at"] = time.time()
            return len(live_products), "oliveyoung-main"
    except Exception:
        pass

    fallback_products = _seed_raw_products()
    _product_cache["products"] = fallback_products
    _product_cache["fetched_at"] = time.time()
    return len(fallback_products), "fallback-seed"


def search_products(keyword: str) -> tuple[str, list[Product]]:
    keyword_ko, products, _, _ = search_products_with_source(keyword)
    return keyword_ko, products


def search_products_with_source(keyword: str) -> tuple[str, list[Product], str, str | None]:
    keyword_ko = keyword_to_korean(keyword)
    has_keyword = bool(keyword.strip())

    if has_keyword:
        try:
            raw_products = _get_cached_search_products(keyword_ko, limit=24)
        except Exception as exc:
            return keyword_ko, [], "oliveyoung-search-error", str(exc)

        source = _raw_products_source(raw_products, "oliveyoung-search")
    else:
        raw_products = _get_live_or_seed_products()
        source = _raw_products_source(raw_products, "oliveyoung-main")

    if not raw_products:
        source = "oliveyoung-search-empty" if has_keyword else "oliveyoung-main-empty"

    return keyword_ko, _normalize_raw_products(raw_products), source, None
