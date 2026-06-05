from crawler.oliveyoung_search import search_products
from schemas import Product


def get_product_detail(product_id: str) -> Product | None:
    _, products = search_products("")
    for product in products:
        if product.id == product_id:
            return product
    return None
