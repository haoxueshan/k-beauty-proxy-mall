from crawler.oliveyoung_search import get_cached_products, search_products
from schemas import Product


def _matches_product(product: Product, product_id: str) -> bool:
    normalized_id = str(product_id)
    legacy_id = f"oy-{product.goods_no[-3:]}"
    return normalized_id in {str(product.id), str(product.goods_no), f"oy-{product.goods_no}", legacy_id}


def get_product_detail(product_id: str) -> Product | None:
    for product in get_cached_products():
        if _matches_product(product, product_id):
            return product

    _, products = search_products("")
    for product in products:
        if _matches_product(product, product_id):
            return product

    return None
