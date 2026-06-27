from __future__ import annotations

import json
import os
import re
import threading
from pathlib import Path

from services.llm_translate_service import (
    TranslationBatchResult,
    translate_search_keyword_to_korean,
    translate_texts,
)

DEFAULT_KEYWORD_MAPPING = {
    "防晒": "선크림",
    "防晒霜": "선크림",
    "防晒棒": "선스틱",
    "面膜": "마스크팩",
    "洁面": "클렌징폼",
    "洁面泡沫": "클렌징폼",
    "洗面奶": "클렌징폼",
    "卸妆": "클렌징",
    "卸妆油": "클렌징오일",
    "口红": "립스틱",
    "唇釉": "틴트",
    "润唇膏": "립밤",
    "护肤": "스킨케어",
    "底妆": "베이스 메이크업",
    "气垫": "쿠션",
    "补水": "수분",
    "保湿": "보습",
    "爽肤水": "토너",
    "精华": "세럼",
    "眼霜": "아이크림",
    "面霜": "크림",
    "护发": "헤어케어",
    "洗发水": "샴푸",
    "牙膏": "치약",
    "牙刷": "칫솔",
    "漱口水": "가글",
    "口腔护理": "구강케어",
}

BRAND_MAPPING = {
    "라운드랩": "Round Lab",
    "rom&nd": "rom&nd",
    "아누아": "Anua",
    "메디힐": "Mediheal",
    "토리든": "Torriden",
    "메디큐브": "Medicube",
    "뷰티오브조선": "Beauty of Joseon",
    "닥터지": "Dr.G",
    "라로슈포제": "La Roche-Posay",
}

CATEGORY_MAPPING = {
    "선케어": "防晒护理",
    "립메이크업": "唇部彩妆",
    "스킨케어": "护肤",
    "클렌징": "清洁卸妆",
    "헤어케어": "护发",
    "마스크팩": "面膜",
    "베이스 메이크업": "底妆",
}

TITLE_REPLACEMENTS = {
    "[올영최초런칭]": "[Olive Young 首发]",
    "[SNS대란템]": "[SNS 爆款]",
    "[한정기획]": "[限定套装]",
    "[NEW초여름 컬러/6월 올영픽]": "[NEW 初夏色/6月 Olive Young Pick]",
    "[NEW듀유코어/1등唇釉]": "[NEW Dewy Core/1号唇釉]",
    "[NEW 알로하선셋 에디션 출시]": "[NEW 阿罗哈夕阳版上市]",
    "라운드랩": "Round Lab",
    "rom&nd": "rom&nd",
    "롬앤": "rom&nd",
    "아누아": "Anua",
    "메디힐": "Mediheal",
    "토리든": "Torriden",
    "메디큐브": "Medicube",
    "뷰티오브조선": "Beauty of Joseon",
    "닥터지": "Dr.G",
    "라로슈포제": "La Roche-Posay",
    "토니모리": "TONYMOLY",
    "얼터너티브스테레오": "Alternative Stereo",
    "듀유코어": "Dewy Core",
    "알로하선셋": "阿罗哈夕阳",
    "에디션": "版",
    "출시": "上市",
    "자작나무": "白桦树",
    "어성초": "鱼腥草",
    "마데카소사이드": "积雪草苷",
    "수분": "补水",
    "진정": "舒缓",
    "보습": "保湿",
    "미백": "美白",
    "탄력": "紧致",
    "선크림": "防晒霜",
    "선스틱": "防晒棒",
    "포밍": "泡沫",
    "토너": "爽肤水",
    "세럼": "精华",
    "에센스": "精华液",
    "앰플": "安瓶",
    "크림": "面霜",
    "클렌징오일": "卸妆油",
    "클렌징 오일": "卸妆油",
    "클렌저": "洁面乳",
    "클렌징폼": "洁面泡沫",
    "클렌징": "清洁",
    "마스크팩": "面膜",
    "패드": "棉片",
    "쿠션": "气垫",
    "립 포션": "唇部 Potion",
    "립펜슬": "唇线笔",
    "퍼펙트립스": "Perfect Lips",
    "쇼킹립": "Shocking Lip",
    "립밤": "润唇膏",
    "립스": "Lips",
    "립": "唇",
    "래스팅": "持久",
    "쥬시": "Juicy",
    "틴트": "唇釉",
    "립스틱": "口红",
    "쇼킹": "Shocking",
    "퍼펙트": "Perfect",
    "포션": "Potion",
    "카라멜": "焦糖",
    "글레이즈": "Glaze",
    "세트": "套装",
    "리필": "补充装",
    "대용량": "大容量",
    "한정": "限定",
    "기획": "套装",
    "단품": "单品",
    "증정": "赠品",
    "미니": "迷你",
    "올영픽": "Olive Young Pick",
    "초여름": "初夏",
    "컬러": "色",
    "컬러": "色",
    "선택": "选择",
    "택1": "选1",
    "1등": "1号",
}

HANGUL_PATTERN = re.compile(r"[\uac00-\ud7a3]")
EDGE_PUNCTUATION_PATTERN = re.compile(r"^[\s,，、。.!！?？;；:：/\\|]+|[\s,，、。.!！?？;；:：/\\|]+$")
BROKEN_INPUT_PATTERN = re.compile(r"^\?+$")
KEYWORD_DICTIONARY_PATH = Path(
    os.getenv(
        "KEYWORD_DICTIONARY_PATH",
        str(Path(__file__).resolve().parents[1] / "data" / "keyword_dictionary.json"),
    )
)
_keyword_dictionary_lock = threading.Lock()


def _normalize_keyword(keyword: str) -> str:
    normalized = " ".join(keyword.strip().split())
    return EDGE_PUNCTUATION_PATTERN.sub("", normalized)


def _looks_like_broken_input(keyword: str) -> bool:
    return bool(BROKEN_INPUT_PATTERN.fullmatch(keyword.strip()))


def _find_keyword_mapping(normalized: str, mapping: dict[str, str]) -> str | None:
    exact_match = mapping.get(normalized)
    if exact_match:
        return exact_match

    for source_keyword, target_keyword in sorted(mapping.items(), key=lambda item: len(item[0]), reverse=True):
        if not source_keyword or _looks_like_broken_input(source_keyword):
            continue
        if source_keyword in normalized:
            return target_keyword
    return None


def _normalize_mapping(mapping: dict[str, object]) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for source, target in mapping.items():
        if not isinstance(source, str) or not isinstance(target, str):
            continue
        source_keyword = _normalize_keyword(source)
        target_keyword = _normalize_keyword(target)
        if source_keyword and target_keyword and not _looks_like_broken_input(source_keyword):
            normalized[source_keyword] = target_keyword
    return normalized


def _write_keyword_dictionary(mapping: dict[str, str]) -> None:
    KEYWORD_DICTIONARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    temp_path = KEYWORD_DICTIONARY_PATH.with_suffix(".tmp")
    temp_path.write_text(
        json.dumps(dict(sorted(mapping.items())), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temp_path.replace(KEYWORD_DICTIONARY_PATH)


def _read_keyword_dictionary() -> dict[str, str]:
    if not KEYWORD_DICTIONARY_PATH.exists():
        _write_keyword_dictionary(DEFAULT_KEYWORD_MAPPING)
        return dict(DEFAULT_KEYWORD_MAPPING)

    try:
        payload = json.loads(KEYWORD_DICTIONARY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return dict(DEFAULT_KEYWORD_MAPPING)

    if not isinstance(payload, dict):
        return dict(DEFAULT_KEYWORD_MAPPING)

    merged = dict(DEFAULT_KEYWORD_MAPPING)
    merged.update(_normalize_mapping(payload))
    return merged


def _save_keyword_translation(source_keyword: str, korean_keyword: str) -> None:
    with _keyword_dictionary_lock:
        mapping = _read_keyword_dictionary()
        mapping[source_keyword] = korean_keyword
        _write_keyword_dictionary(mapping)


def keyword_to_korean(keyword: str) -> str:
    normalized = _normalize_keyword(keyword)
    if not normalized:
        return ""

    with _keyword_dictionary_lock:
        mapping = _read_keyword_dictionary()

    if _looks_like_broken_input(normalized):
        return normalized

    mapped_keyword = _find_keyword_mapping(normalized, mapping)
    if mapped_keyword:
        return mapped_keyword

    if HANGUL_PATTERN.search(normalized):
        _save_keyword_translation(normalized, normalized)
        return normalized

    result = translate_search_keyword_to_korean(normalized, fallback_text=normalized)
    translated_keyword = _normalize_keyword(result.translations[0] if result.translations else normalized)
    if result.provider == "deepseek" and HANGUL_PATTERN.search(translated_keyword):
        _save_keyword_translation(normalized, translated_keyword)
        return translated_keyword

    return normalized


def brand_to_chinese(brand_ko: str) -> str:
    return BRAND_MAPPING.get(brand_ko.strip(), brand_ko.strip())


def category_to_chinese(category_ko: str) -> str:
    return CATEGORY_MAPPING.get(category_ko.strip(), category_ko.strip())


def translate_title_with_rules(title_ko: str) -> str:
    translated = title_ko.strip()
    for source, target in sorted(TITLE_REPLACEMENTS.items(), key=lambda item: len(item[0]), reverse=True):
        translated = translated.replace(source, target)
    translated = re.sub(r"[\uac00-\ud7a3]+", "", translated)
    translated = re.sub(r"\s*([/+])\s*", r"\1", translated)
    translated = re.sub(r"\s{2,}", " ", translated)
    return translated.strip()


def translate_title_to_chinese(title_ko: str) -> str:
    return translate_title_with_rules(title_ko)


def translate_titles_to_chinese(titles_ko: list[str]) -> TranslationBatchResult:
    fallback_titles = [translate_title_with_rules(title) for title in titles_ko]
    return translate_texts(
        titles_ko,
        source_language="Korean",
        target_language="Simplified Chinese",
        fallback_texts=fallback_titles,
    )


def summarize_product(title_zh: str, category_zh: str) -> str:
    return f"{title_zh} 属于{category_zh}类目，适合作为当前商品下单与价格参考展示的候选商品。"


def estimate_translation_confidence(
    *,
    provider: str,
    original_text: str,
    translated_text: str,
) -> float:
    normalized_original = " ".join(original_text.strip().split())
    normalized_translated = " ".join(translated_text.strip().split())

    if not normalized_translated:
        return 0.1
    if provider == "deepseek":
        return 0.93
    if provider == "cache":
        return 0.88
    if provider == "fallback":
        if normalized_translated == normalized_original:
            return 0.22
        return 0.58
    if provider == "input":
        return 0.98
    return 0.45
