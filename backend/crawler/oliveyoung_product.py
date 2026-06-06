import re

from crawler.oliveyoung_search import get_cached_products, get_product_by_goods_no, search_products
from schemas import Product


def _matches_product(product: Product, product_id: str) -> bool:
    normalized_id = str(product_id)
    legacy_id = f"oy-{product.goods_no[-3:]}"
    return normalized_id in {str(product.id), str(product.goods_no), f"oy-{product.goods_no}", legacy_id}


def _extract_goods_no(product_id: str) -> str | None:
    match = re.search(r"(A\d{12})", str(product_id).upper())
    return match.group(1) if match else None


def get_product_detail(product_id: str) -> Product | None:
    for product in get_cached_products():
        if _matches_product(product, product_id):
            return product

    goods_no = _extract_goods_no(product_id)
    if goods_no:
        product = get_product_by_goods_no(goods_no)
        if product is not None:
            return product

    _, products = search_products("")
    for product in products:
        if _matches_product(product, product_id):
            return product

    return None
