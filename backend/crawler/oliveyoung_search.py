from __future__ import annotations

import re
import time
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from crawler.parser import normalize_product
from schemas import Product, RawCrawlerProduct
from services.translate_service import keyword_to_korean, translate_titles_to_chinese

OLIVE_YOUNG_MAIN_URL = "https://www.oliveyoung.co.kr/store/main/main.do?oy=0"
PRODUCT_LINK_SELECTOR = "a.item.a_detail[href*='getGoodsDetail.do?goodsNo=']"
CACHE_TTL_SECONDS = 900

_product_cache: dict[str, object] = {
    "fetched_at": 0.0,
    "products": [],
}


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
            source_url=OLIVE_YOUNG_MAIN_URL,
        ),
        RawCrawlerProduct(
            goods_no="A000000000002",
            title_ko="rom&nd 쥬시 래스팅 틴트 23호",
            brand_ko="rom&nd",
            image_url="https://images.unsplash.com/photo-1586495777744-4413f21062fa?auto=format&fit=crop&w=900&q=80",
            original_price_krw=13000,
            sale_price_krw=9800,
            category_ko="립메이크업",
            source_url=OLIVE_YOUNG_MAIN_URL,
        ),
        RawCrawlerProduct(
            goods_no="A000000000003",
            title_ko="아누아 어성초 77 토너 250ml",
            brand_ko="아누아",
            image_url="https://images.unsplash.com/photo-1556228578-dd6c474e2113?auto=format&fit=crop&w=900&q=80",
            original_price_krw=29000,
            sale_price_krw=21500,
            category_ko="스킨케어",
            source_url=OLIVE_YOUNG_MAIN_URL,
        ),
    ]


def _extract_goods_no(href: str) -> str | None:
    match = re.search(r"goodsNo=([A-Z0-9]+)", href)
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
    if any(keyword in lowered for keyword in ["선크림", "선스틱", "선케어"]):
        return "선케어"
    if any(keyword in lowered for keyword in ["틴트", "립", "글로스"]):
        return "립메이크업"
    if any(keyword in lowered for keyword in ["클렌징", "클렌저", "폼", "오일"]):
        return "클렌징"
    if any(keyword in lowered for keyword in ["마스크", "팩", "패드"]):
        return "마스크팩"
    if any(keyword in lowered for keyword in ["샴푸", "트리트먼트", "헤어"]):
        return "헤어케어"
    if any(keyword in lowered for keyword in ["쿠션", "파운데이션", "베이스"]):
        return "베이스 메이크업"
    return "스킨케어"


def _fetch_main_page_html() -> str:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(
            locale="ko-KR",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1440, "height": 2200},
        )
        page.goto(OLIVE_YOUNG_MAIN_URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(2500)
        html = page.content()
        browser.close()
        return html


def _parse_main_page_products(html: str, limit: int = 24) -> list[RawCrawlerProduct]:
    soup = BeautifulSoup(html, "html.parser")
    seen_goods_no: set[str] = set()
    parsed_products: list[RawCrawlerProduct] = []

    for anchor in soup.select(PRODUCT_LINK_SELECTOR):
        href = anchor.get("href") or ""
        goods_no = anchor.get("data-ref-goodsno") or _extract_goods_no(href)
        if not goods_no or goods_no in seen_goods_no:
            continue

        title_node = anchor.select_one(".tx_name")
        title_ko = title_node.get_text(" ", strip=True) if title_node else ""
        if not title_ko:
            image_node = anchor.select_one("img")
            title_ko = (image_node.get("alt") or "").strip() if image_node else ""
        if not title_ko:
            continue

        image_node = anchor.select_one("img")
        image_url = urljoin(OLIVE_YOUNG_MAIN_URL, image_node.get("src", "")) if image_node else ""
        original_price = _parse_price(
            anchor.select_one(".tx_org .tx_num").get_text(strip=True) if anchor.select_one(".tx_org .tx_num") else None
        )
        sale_price = _parse_price(
            anchor.select_one(".tx_cur .tx_num").get_text(strip=True) if anchor.select_one(".tx_cur .tx_num") else None
        )
        if sale_price is None:
            all_prices = [_parse_price(node.get_text(strip=True)) for node in anchor.select(".prd_price .tx_num")]
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
                brand_ko=_extract_brand(title_ko),
                image_url=image_url,
                original_price_krw=original_price,
                sale_price_krw=sale_price,
                category_ko=_infer_category(title_ko),
                source_url=urljoin(OLIVE_YOUNG_MAIN_URL, href),
                raw_data={
                    "source": "oliveyoung-main",
                    "href": href,
                    "text": anchor.get_text(" ", strip=True),
                },
            )
        )
        seen_goods_no.add(goods_no)

        if len(parsed_products) >= limit:
            break

    return parsed_products


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
    keyword_ko = keyword_to_korean(keyword)
    raw_products = _get_live_or_seed_products()
    translation_result = translate_titles_to_chinese([item.title_ko for item in raw_products])
    products = [
        normalize_product(item, title_zh)
        for item, title_zh in zip(raw_products, translation_result.translations)
    ]

    lowered = keyword.strip().lower()
    if not lowered:
        return keyword_ko, products

    filtered = [
        product
        for product in products
        if lowered in product.title_zh.lower()
        or lowered in product.title_ko.lower()
        or lowered in product.brand_zh.lower()
        or lowered in product.brand_ko.lower()
        or lowered in product.category_zh.lower()
        or keyword_ko.lower() in product.title_ko.lower()
        or keyword_ko.lower() in product.title_zh.lower()
    ]
    return keyword_ko, filtered
