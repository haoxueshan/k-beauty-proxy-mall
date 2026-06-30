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
    translate_texts_fast,
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
CJK_PATTERN = re.compile(r"[\u4e00-\u9fff]")
EDGE_PUNCTUATION_PATTERN = re.compile(r"^[\s,，、。.!！?？;；:：/\\|]+|[\s,，、。.!！?？;；:：/\\|]+$")
BROKEN_INPUT_PATTERN = re.compile(r"^\?+$")
KEYWORD_DICTIONARY_PATH = Path(
    os.getenv(
        "KEYWORD_DICTIONARY_PATH",
        str(Path(__file__).resolve().parents[1] / "data" / "keyword_dictionary.json"),
    )
)
_keyword_dictionary_lock = threading.Lock()


# Search responses return immediately, so this rule fallback must be readable
# before the background LLM cache finishes. Keep unknown Korean instead of
# deleting it; losing product terms is worse than showing a mixed title.
TITLE_TOKEN_REPLACEMENTS = {
    "올리브영": "Olive Young",
    "올영": "Olive Young",
    "올픽": "Olive Young Pick",
    "증정": "赠品",
    "사은품": "赠品",
    "기획": "企划套装",
    "기획세트": "企划套装",
    "세트": "套装",
    "단품": "单品",
    "본품": "正装",
    "리필": "替换装",
    "대용량": "大容量",
    "한정": "限定",
    "품절대란": "断货热卖",
    "단종템부활": "停产款回归",
    "신상": "新品",
    "미니브러쉬": "迷你刷",
    "미니브러시": "迷你刷",
    "미니브": "迷你刷",
    "브러쉬": "刷子",
    "브러시": "刷子",
    "페이스": "面部",
    "아이": "眼部",
    "립": "唇部",
    "치크": "脸颊",
    "블러셔": "腮红",
    "블러쉬": "腮红",
    "파우더": "粉",
    "리퀴드": "液体",
    "크림": "霜",
    "젤": "凝胶",
    "밤": "膏",
    "스틱": "棒",
    "팔레트": "盘",
    "쿠션": "气垫",
    "파운데이션": "粉底液",
    "컨실러": "遮瑕",
    "베이스": "妆前",
    "선크림": "防晒霜",
    "선케어": "防晒护理",
    "선스틱": "防晒棒",
    "토너": "爽肤水",
    "패드": "棉片",
    "앰플": "安瓶",
    "세럼": "精华",
    "에센스": "精华",
    "로션": "乳液",
    "마스크팩": "面膜",
    "마스크": "面膜",
    "팩": "面膜",
    "클렌징": "清洁",
    "클렌저": "洁面",
    "폼": "泡沫",
    "오일": "油",
    "워터": "水",
    "샴푸": "洗发水",
    "트리트먼트": "护理",
    "바디": "身体",
    "핸드": "手部",
    "향수": "香水",
    "무드레시피": "Mood Recipe",
    "플러피": "蓬蓬",
    "페탈": "花瓣",
    "드롭": "水滴",
    "글로우": "光泽",
    "매트": "哑光",
    "촉촉": "水润",
    "진정": "舒缓",
    "수분": "补水",
    "보습": "保湿",
    "미백": "美白",
    "탄력": "弹力",
    "저자극": "低刺激",
    "과일스퀴시": "水果捏捏乐",
    "네이밍": "NAMING",
}

TITLE_PHRASE_REPLACEMENTS = {
    "페이스 블러쉬": "面部腮红",
    "파우더 블러쉬": "粉质腮红",
    "파우더 블러셔": "粉质腮红",
    "리퀴드 블러셔": "液体腮红",
    "페탈 드롭 리퀴드 블러셔": "花瓣水滴液体腮红",
    "플러피 파우더 블러쉬": "蓬蓬粉质腮红",
    "무드레시피 페이스 블러쉬": "Mood Recipe 面部腮红",
    "미니브증정기획": "迷你刷赠品企划",
    "미니브러쉬증정기획": "迷你刷赠品企划",
}


CLEAN_TITLE_PHRASE_REPLACEMENTS = {
    "\uc62c\ub9ac\ube0c\uc601\ud53d": "Olive Young Pick",
    "\uc62c\uc601\ud53d": "Olive Young Pick",
    "\uc62c\ud53d": "Olive Young Pick",
    "\ud55c\uc815\uae30\ud68d\uc138\ud2b8": "\u9650\u5b9a\u4f01\u5212\u5957\u88c5",
    "\ud55c\uc815\uae30\ud68d": "\u9650\u5b9a\u4f01\u5212",
    "\uae30\ud68d\uc138\ud2b8": "\u4f01\u5212\u5957\u88c5",
    "\ub2e8\ub3c5\uae30\ud68d": "\u72ec\u5bb6\u4f01\u5212",
    "\ud488\uc808\ub300\ub780": "\u65ad\u8d27\u70ed\u5356",
    "\ub2e8\uc885\ud15c\ubd80\ud65c": "\u505c\u4ea7\u6b3e\u56de\u5f52",
    "\ubbf8\ub2c8\ube0c\ub7ec\uc26c\uc99d\uc815\uae30\ud68d": "\u8ff7\u4f60\u5237\u8d60\u54c1\u4f01\u5212",
    "\ubbf8\ub2c8\ube0c\uc99d\uc815\uae30\ud68d": "\u8ff7\u4f60\u5237\u8d60\u54c1\u4f01\u5212",
    "\ubb34\ub4dc\ub808\uc2dc\ud53c \ud398\uc774\uc2a4 \ube14\ub7ec\uc26c": "Mood Recipe \u9762\u90e8\u816e\u7ea2",
    "\ud398\uc774\uc2a4 \ube14\ub7ec\uc26c": "\u9762\u90e8\u816e\u7ea2",
    "\ud50c\ub7ec\ud53c \ud30c\uc6b0\ub354 \ube14\ub7ec\uc26c": "\u84ec\u84ec\u7c89\u8d28\u816e\u7ea2",
    "\ud30c\uc6b0\ub354 \ube14\ub7ec\uc26c": "\u7c89\u8d28\u816e\u7ea2",
    "\ud30c\uc6b0\ub354 \ube14\ub7ec\uc154": "\u7c89\u8d28\u816e\u7ea2",
    "\ud398\ud0c8 \ub4dc\ub86d \ub9ac\ud034\ub4dc \ube14\ub7ec\uc154": "\u82b1\u74e3\u6c34\u6ef4\u6db2\u4f53\u816e\u7ea2",
    "\ub9ac\ud034\ub4dc \ube14\ub7ec\uc154": "\u6db2\u4f53\u816e\u7ea2",
    "\uacfc\uc77c\uc2a4\ud034\uc2dc": "\u6c34\u679c\u634f\u634f\u4e50",
    "\uc544\ud1a0\ubca0\ub9ac\uc5b4365": "Atobarrier365",
    "\uc544\ud1a0\ubca0\ub9ac\uc5b4": "Atobarrier",
    "\ud53c\ub514\uc54c\uc5d4": "PDRN",
    "\ud788\uc54c\ub8e8\ub860\uc0b0": "\u900f\u660e\u8d28\u9178",
    "\ud310\ud1a0\ud150\uc0b0": "\u6cdb\u9187",
}


CLEAN_TITLE_TOKEN_REPLACEMENTS = {
    "\uc6d4": "\u6708",
    "\uc704": "\u540d",
    "\ubc88": "\u53f7",
    "\uc5b4\uc6cc\uc988": "\u5956\u9879",
    "\uae30\ud68d": "\u4f01\u5212",
    "\uc138\ud2b8": "\u5957\u88c5",
    "\ub2e8\ud488": "\u5355\u54c1",
    "\uc99d\uc815": "\u8d60\u54c1",
    "\uc0ac\uc740\ud488": "\u8d60\u54c1",
    "\uc815\ud488": "\u6b63\u88c5",
    "\ubcf8\ud488": "\u6b63\u88c5",
    "\ub9ac\ud544": "\u66ff\u6362\u88c5",
    "\ub300\uc6a9\ub7c9": "\u5927\u5bb9\u91cf",
    "\ud55c\uc815": "\u9650\u5b9a",
    "\ub9e4": "\u7247",
    "\uac1c": "\u4e2a",
    "\uc5d0\uc2a4\ud2b8\ub77c": "AESTURA",
    "\uc544\ub204\uc544": "Anua",
    "\ub118\ubc84\uc988\uc778": "numbuzin",
    "\ub124\uc774\ubc0d": "NAMING",
    "\uc5d0\uc13c\uc2a4": "\u7cbe\u534e",
    "\uc138\ub7fc": "\u7cbe\u534e",
    "\uc575\ud50c": "\u5b89\u74f6",
    "\ud06c\ub9bc": "\u971c",
    "\uc218\ubd84": "\u8865\u6c34",
    "\uc9c4\uc815": "\u8212\u7f13",
    "\ud1a0\ub108": "\u723d\u80a4\u6c34",
    "\uc2a4\ud0a8\ucf00\uc5b4": "\u62a4\u80a4",
    "\ud558\uc774\ub4dc\ub85c": "\u6c34\u6da6",
    "\uae00\ub7ec\uc26c": "\u5149\u6cfd",
    "\ud53c\ud504": "\u8d60\u54c1",
    "\ub354\ube14": "\u53cc\u91cd",
    "\ucea1\uc290": "\u80f6\u56ca",
    "\ub9c8\uc2a4\ud06c\ud329": "\u9762\u819c",
    "\ub9c8\uc2a4\ud06c": "\u9762\u819c",
    "\ud329": "\u9762\u819c",
    "\ube14\ub7ec\uc26c": "\u816e\u7ea2",
    "\ube14\ub7ec\uc154": "\u816e\u7ea2",
    "\ud30c\uc6b0\ub354": "\u7c89",
    "\ub9ac\ud034\ub4dc": "\u6db2\u4f53",
    "\ud398\uc774\uc2a4": "\u9762\u90e8",
}


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
    original = " ".join(title_ko.strip().split())
    translated = original
    for source, target in sorted(TITLE_PHRASE_REPLACEMENTS.items(), key=lambda item: len(item[0]), reverse=True):
        translated = translated.replace(source, target)
    for source, target in sorted(TITLE_TOKEN_REPLACEMENTS.items(), key=lambda item: len(item[0]), reverse=True):
        translated = translated.replace(source, target)
    for source, target in sorted(TITLE_REPLACEMENTS.items(), key=lambda item: len(item[0]), reverse=True):
        translated = translated.replace(source, target)

    translated = re.sub(r"(?<=\d)월", "月", translated)
    translated = re.sub(r"\s*([/+])\s*", r"\1", translated)
    translated = re.sub(r"\[\s*/+\s*\]", "", translated)
    translated = re.sub(r"\(\s*/+\s*\)", "", translated)
    translated = re.sub(r"\s{2,}", " ", translated)
    translated = translated.strip(" -_/|")
    return translated if _is_usable_title_translation(original, translated) else original


def _is_usable_title_translation(original: str, translated: str) -> bool:
    normalized = translated.strip()
    if not normalized:
        return False
    if normalized in {"[]", "[/]", "(/)", "/", "-", "_"}:
        return False
    if HANGUL_PATTERN.search(original) and len(normalized) <= 4 and len(original.strip()) > 8:
        return False
    if HANGUL_PATTERN.search(original) and not (CJK_PATTERN.search(normalized) or HANGUL_PATTERN.search(normalized)):
        return False
    return True


def _translate_title_with_clean_rules(title_ko: str) -> str:
    original = " ".join(title_ko.strip().split())
    translated = original

    for source, target in sorted(CLEAN_TITLE_PHRASE_REPLACEMENTS.items(), key=lambda item: len(item[0]), reverse=True):
        translated = translated.replace(source, target)
    for source, target in sorted(CLEAN_TITLE_TOKEN_REPLACEMENTS.items(), key=lambda item: len(item[0]), reverse=True):
        translated = translated.replace(source, target)

    translated = re.sub(r"(\d+)\s*\uc704", lambda match: f"\u7b2c{match.group(1)}\u540d", translated)
    translated = re.sub(r"(\d+)\s*\ub9e4", lambda match: f"{match.group(1)}\u7247", translated)
    translated = re.sub(r"(\d+)\s*\uac1c", lambda match: f"{match.group(1)}\u4e2a", translated)
    translated = re.sub(r"(?<=\d)\s*\uc6d4", "\u6708", translated)
    translated = re.sub(r"(\d+)\s*\u540d", lambda match: f"\u7b2c{match.group(1)}\u540d", translated)
    translated = re.sub(r"\s*([/+])\s*", r"\1", translated)
    translated = re.sub(r"\[\s*/+\s*\]", "", translated)
    translated = re.sub(r"\(\s*/+\s*\)", "", translated)
    translated = re.sub(r"\s{2,}", " ", translated)
    translated = translated.strip(" -_/|")
    return translated if _is_usable_title_translation(original, translated) else original


translate_title_with_rules = _translate_title_with_clean_rules


def translate_title_to_chinese(title_ko: str) -> str:
    return translate_title_with_rules(title_ko)


def translate_titles_to_chinese(titles_ko: list[str]) -> TranslationBatchResult:
    fallback_titles = [translate_title_with_rules(title) for title in titles_ko]
    return translate_texts_fast(
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
