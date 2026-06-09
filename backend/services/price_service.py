def calculate_cny_reference(krw_price: int, exchange_rate: float = 0.0053) -> float:
    return round(krw_price * exchange_rate, 2)


def estimate_price_confidence(
    *,
    sale_price_krw: int | None,
    original_price_krw: int | None,
    source_type: str,
) -> float:
    if not sale_price_krw or sale_price_krw <= 0:
        return 0.15

    if source_type == "live_detail":
        return 0.97 if original_price_krw and original_price_krw > 0 else 0.9
    if source_type == "live_search":
        return 0.88 if original_price_krw and original_price_krw > 0 else 0.78
    if source_type == "live_main":
        return 0.82 if original_price_krw and original_price_krw > 0 else 0.72
    if source_type == "cache":
        return 0.76 if original_price_krw and original_price_krw > 0 else 0.68
    if source_type == "seed":
        return 0.35
    return 0.6
