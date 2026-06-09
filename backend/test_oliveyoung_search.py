import sys

from crawler.oliveyoung_search import search_products_with_source


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


TEST_KEYWORDS = [
    "\u9632\u6652\u971c",
    "\u53e3\u7ea2",
    "\u6d01\u9762\u6ce1\u6cab",
    "\u6d17\u9762\u5976",
]


def _show_search_result(keyword: str):
    response = search_products_with_source(keyword)
    keyword_ko = response.keyword_ko
    products = response.items
    source = response.source
    error = response.error

    print("=" * 80)
    print("Keyword:", keyword)
    print("Korean keyword:", keyword_ko)
    print("Source:", source)
    print("Error:", error or "")
    print("Product count:", len(products))

    for product in products[:5]:
        print("-" * 40)
        print("ID:", product.id)
        print("Goods No:", product.goods_no)
        print("Brand:", product.brand_ko, "/", product.brand_zh)
        print("Korean title:", product.title_ko)
        print("Chinese title:", product.title_zh)
        print("KRW price:", product.sale_price_krw)
        print("CNY reference price:", product.price_cny)
        print("Link:", product.source_url)
        print("Meta:", product.metadata.model_dump())

    return response


def test_oliveyoung_search_returns_products() -> None:
    for keyword in TEST_KEYWORDS:
        response = _show_search_result(keyword)

        assert response.keyword_ko
        assert response.error is None
        assert response.source != "fallback-seed"
        assert response.items, f"No Olive Young products returned for keyword: {keyword}"
        assert not response.fallback_items
        assert response.items[0].id.startswith("oy-")
        assert response.items[0].goods_no
        assert response.items[0].source_url


def main() -> None:
    for keyword in TEST_KEYWORDS:
        _show_search_result(keyword)


if __name__ == "__main__":
    main()
