from __future__ import annotations

from datetime import datetime

from schemas import Product, ProductMetadata, RawCrawlerProduct
from services.llm_translate_service import TranslationBatchResult
from services.price_service import calculate_cny_reference, estimate_price_confidence
from services.translate_service import (
    brand_to_chinese,
    category_to_chinese,
    estimate_translation_confidence,
    summarize_product,
)


def _coerce_datetime(value: object) -> datetime | None:
    # 后端和 Supabase 可能返回 datetime 或 ISO 字符串，这里统一转成模型可用的时间。
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str) or not value:
        return None

    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def _coerce_int(value: object) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _calculate_completeness_score(raw: RawCrawlerProduct, *, title_zh: str, brand_zh: str, category_zh: str) -> float:
    # 完整度不是业务价格依据，只用于前端提示“这条商品数据是否足够完整”。
    score = 0.0
    checks = (
        (bool(raw.goods_no), 0.08),
        (bool(raw.title_ko), 0.2),
        (bool(title_zh), 0.16),
        (bool(raw.brand_ko), 0.08),
        (bool(brand_zh), 0.08),
        (bool(raw.image_url), 0.1),
        (bool(raw.source_url), 0.08),
        (bool(raw.sale_price_krw and raw.sale_price_krw > 0), 0.12),
        (bool(raw.original_price_krw and raw.original_price_krw > 0), 0.05),
        (bool(raw.category_ko), 0.03),
        (bool(category_zh), 0.02),
    )
    for passed, weight in checks:
        if passed:
            score += weight
    return round(min(score, 1.0), 2)


def normalize_product(
    raw: RawCrawlerProduct,
    title_zh: str,
    *,
    translation_result: TranslationBatchResult,
    source_type: str,
    last_synced_at: datetime | None,
) -> Product:
    # 把爬虫原始字段规范化为前端统一消费的 Product，所有可信度元信息都在这里汇总。
    category_zh = category_to_chinese(raw.category_ko)
    brand_zh = brand_to_chinese(raw.brand_ko)
    completeness_score = _calculate_completeness_score(
        raw,
        title_zh=title_zh,
        brand_zh=brand_zh,
        category_zh=category_zh,
    )
    price_confidence = estimate_price_confidence(
        sale_price_krw=raw.sale_price_krw,
        original_price_krw=raw.original_price_krw,
        source_type=source_type,
    )
    translation_confidence = estimate_translation_confidence(
        provider=translation_result.provider,
        original_text=raw.title_ko,
        translated_text=title_zh,
    )

    # 当前金额统一使用 Olive Young 韩元售价折算人民币参考价，不再使用代购加价字段参与计算。
    price_cny = calculate_cny_reference(raw.sale_price_krw)

    return Product(
        id=f"oy-{raw.goods_no}",
        goods_no=raw.goods_no,
        source_url=raw.source_url,
        brand_ko=raw.brand_ko,
        brand_zh=brand_zh,
        title_ko=raw.title_ko,
        title_zh=title_zh,
        image_url=raw.image_url,
        original_price_krw=raw.original_price_krw,
        sale_price_krw=raw.sale_price_krw,
        price_cny=price_cny,
        proxy_price_cny=price_cny,
        category_zh=category_zh,
        ai_summary=summarize_product(title_zh, category_zh),
        risk_tips=["价格与库存以最近一次同步结果为准", "最终成交金额需人工复核确认"],
        metadata=ProductMetadata(
            last_synced_at=last_synced_at or _coerce_datetime(raw.raw_data.get("last_synced_at")),
            source_type=source_type,
            completeness_score=completeness_score,
            price_confidence=price_confidence,
            translation_confidence=translation_confidence,
            source_rank=_coerce_int(raw.raw_data.get("source_rank")),
            keyword_ko=raw.raw_data.get("keyword_ko"),
            synced_at=_coerce_datetime(raw.raw_data.get("synced_at") or raw.raw_data.get("last_synced_at")),
            raw_price_text=raw.raw_data.get("raw_price_text"),
        ),
    )
