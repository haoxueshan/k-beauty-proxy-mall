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


def get_products_by_ids(product_ids: list[str]) -> dict[str, Product]:
    """Resolve product ids in one pass through current crawler cache.

    TODO: For production speed and historical accuracy, save a product snapshot
    when adding to cart and use that snapshot as the primary display source.
    """
    requested_ids = [str(product_id) for product_id in product_ids if product_id]
    resolved: dict[str, Product] = {}
    missing_ids = set(requested_ids)

    cached_products = get_cached_products()
    for product in cached_products:
        matched_ids = {product_id for product_id in missing_ids if _matches_product(product, product_id)}
        for product_id in matched_ids:
            resolved[product_id] = product
        missing_ids -= matched_ids
        if not missing_ids:
            return resolved

    for product_id in list(missing_ids):
        goods_no = _extract_goods_no(product_id)
        if not goods_no:
            continue
        product = get_product_by_goods_no(goods_no)
        if product is not None:
            resolved[product_id] = product
            missing_ids.remove(product_id)

    if missing_ids:
        _, products = search_products("")
        for product in products:
            matched_ids = {product_id for product_id in missing_ids if _matches_product(product, product_id)}
            for product_id in matched_ids:
                resolved[product_id] = product
            missing_ids -= matched_ids
            if not missing_ids:
                break

    return resolved
