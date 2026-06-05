from schemas import Product, RawCrawlerProduct
from services.price_service import calculate_cny_reference, calculate_proxy_price
from services.translate_service import brand_to_chinese, category_to_chinese, summarize_product


def normalize_product(raw: RawCrawlerProduct, title_zh: str) -> Product:
    numeric_suffix = int(raw.goods_no[-3:])
    category_zh = category_to_chinese(raw.category_ko)
    return Product(
        id=f"oy-{numeric_suffix}",
        goods_no=raw.goods_no,
        source_url=raw.source_url,
        brand_ko=raw.brand_ko,
        brand_zh=brand_to_chinese(raw.brand_ko),
        title_ko=raw.title_ko,
        title_zh=title_zh,
        image_url=raw.image_url,
        original_price_krw=raw.original_price_krw,
        sale_price_krw=raw.sale_price_krw,
        price_cny=calculate_cny_reference(raw.sale_price_krw),
        proxy_price_cny=calculate_proxy_price(raw.sale_price_krw),
        category_zh=category_zh,
        ai_summary=summarize_product(title_zh, category_zh),
        risk_tips=["价格与库存以最近一次同步结果为准", "最终代购成交金额需人工复核确认"],
    )
