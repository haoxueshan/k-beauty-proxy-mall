from dataclasses import dataclass


@dataclass
class PricingRule:
    exchange_rate: float = 0.0053
    service_fee_min: float = 20
    service_fee_ratio: float = 0.10
    international_shipping_fee: float = 25
    package_fee: float = 5


def calculate_cny_reference(krw_price: int, exchange_rate: float = 0.0053) -> float:
    return round(krw_price * exchange_rate, 2)


def calculate_proxy_price(krw_price: int, pricing_rule: PricingRule | None = None) -> float:
    rule = pricing_rule or PricingRule()
    product_cny = calculate_cny_reference(krw_price, rule.exchange_rate)
    service_fee = max(product_cny * rule.service_fee_ratio, rule.service_fee_min)
    total = product_cny + service_fee + rule.international_shipping_fee + rule.package_fee
    return round(total, 2)
