from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Sequence

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DEFAULT_DEEPSEEK_TRANSLATION_MODEL = "deepseek-v4-flash"
DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
HANGUL_PATTERN = re.compile(r"[\uac00-\ud7a3]")
CODE_BLOCK_PATTERN = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)
_translation_cache: dict[tuple[str, str, str], tuple[str, str | None]] = {}
_keyword_translation_cache: dict[str, tuple[str, str | None]] = {}

@dataclass(frozen=True)
class TranslationBatchResult:
    translations: list[str]
    provider: str
    model: str | None = None


def get_translation_settings() -> dict[str, str | bool]:
    # DeepSeek 采用 OpenAI-compatible SDK，部署时只需要配置 key/base_url/model。
    enabled = os.getenv("DEEPSEEK_TRANSLATION_ENABLED", "true").strip().lower() not in {"0", "false", "no"}
    return {
        "api_key": os.getenv("DEEPSEEK_API_KEY", "").strip(),
        "base_url": os.getenv("DEEPSEEK_BASE_URL", "").strip() or DEFAULT_DEEPSEEK_BASE_URL,
        "model": os.getenv("DEEPSEEK_TRANSLATION_MODEL", "").strip()
        or os.getenv("DEEPSEEK_MODEL", "").strip()
        or DEFAULT_DEEPSEEK_TRANSLATION_MODEL,
        "enabled": enabled,
    }


def is_deepseek_translation_enabled() -> bool:
    settings = get_translation_settings()
    return bool(settings["enabled"] and settings["api_key"])


@lru_cache(maxsize=1)
def _get_deepseek_client() -> OpenAI:
    settings = get_translation_settings()
    api_key = str(settings["api_key"])
    if not api_key:
        raise RuntimeError("DeepSeek API key is not configured")
    return OpenAI(api_key=api_key, base_url=str(settings["base_url"]))


def _sanitize_model_output(text: str) -> str:
    return CODE_BLOCK_PATTERN.sub("", text.strip()).strip()


def _parse_json_array(raw_output: str, expected_length: int) -> list[str]:
    # 大模型偶尔会包一层 markdown 或解释文字，因此先截取 JSON 数组再解析。
    sanitized = _sanitize_model_output(raw_output)
    start = sanitized.find("[")
    end = sanitized.rfind("]")
    if start == -1 or end == -1 or end < start:
        raise ValueError("Translation response is not a JSON array")

    payload = json.loads(sanitized[start : end + 1])
    if not isinstance(payload, list) or len(payload) != expected_length:
        raise ValueError("Translation response length does not match the request")

    translations: list[str] = []
    for item in payload:
        if not isinstance(item, str):
            raise ValueError("Translation response contains a non-string item")
        translations.append(" ".join(item.split()))
    return translations


def _should_translate_with_llm(text: str) -> bool:
    return bool(HANGUL_PATTERN.search(text))


def _request_deepseek_text(
    messages: list[dict[str, str]],
    *,
    response_format: dict[str, str] | None = None,
) -> tuple[str, str]:
    # 统一封装 DeepSeek 调用，标题翻译和搜索词翻译共用，便于后续替换模型。
    settings = get_translation_settings()
    model = str(settings["model"])
    client = _get_deepseek_client()

    request_body: dict[str, object] = {
        "model": model,
        "messages": messages,
        "stream": False,
        "temperature": 0,
        "extra_body": {
            "thinking": {
                "type": "disabled"
            }
        },
    }

    if response_format is not None:
        request_body["response_format"] = response_format

    response = client.chat.completions.create(**request_body)
    output_text = (response.choices[0].message.content or "").strip()

    if not output_text:
        raise ValueError("DeepSeek response text is empty")

    return output_text, model


def _build_translation_messages(
    texts: Sequence[str],
    source_language: str,
    target_language: str,
) -> list[dict[str, str]]:
    # 标题翻译要求接近浏览器直译：保留品牌、规格、赠品和套装信息，不改写成营销标题。
    user_payload = [{"index": index, "text": text} for index, text in enumerate(texts)]
    return [
        {
            "role": "system",
            "content": (
                "You are a high-accuracy Korean-to-Simplified-Chinese product-title translator "
                "for Olive Young products. Translate faithfully, like browser translation, not "
                "advertising copy."
            ),
        },
        {
            "role": "user",
            "content": (
                "Translate each product title accurately into Simplified Chinese.\n"
                "Keep the original information order. Do not rewrite, summarize, omit, infer, add selling points, "
                "or split the title.\n"
                "Preserve official brand names, English words, SPF/PA values, shade numbers, capacities, model codes, "
                "gift details, bundle/set details, punctuation, and parenthesized information.\n"
                "If a Korean brand has a well-known official English name, use that English name.\n"
                "The output must not contain Korean Hangul unless it is an official brand or shade name that should "
                "be preserved.\n"
                "Return only a JSON array of translated strings in the same order as the input. Do not wrap it in markdown.\n"
                f"Source language: {source_language}\n"
                f"Target language: {target_language}\n"
                f"Items: {json.dumps(user_payload, ensure_ascii=False)}"
            ),
        },
    ]


def _request_deepseek_translations(
    texts: Sequence[str],
    source_language: str,
    target_language: str,
) -> TranslationBatchResult:
    messages = _build_translation_messages(texts, source_language, target_language)
    output_text, model = _request_deepseek_text(messages)
    translations = _parse_json_array(output_text, len(texts))
    if any(HANGUL_PATTERN.search(translation) for translation in translations):
        raise ValueError("Translation response still contains Hangul")
    return TranslationBatchResult(translations=translations, provider="deepseek", model=model)


def _clean_single_keyword(raw_output: str) -> str:
    sanitized = _sanitize_model_output(raw_output)
    sanitized = sanitized.strip().strip("\"'`")

    try:
        parsed = json.loads(sanitized)
    except json.JSONDecodeError:
        parsed = None

    if isinstance(parsed, str):
        sanitized = parsed
    elif isinstance(parsed, list) and parsed and isinstance(parsed[0], str):
        sanitized = parsed[0]
    elif isinstance(parsed, dict):
        value = parsed.get("keyword_ko") or parsed.get("keyword") or parsed.get("translation")
        if isinstance(value, str):
            sanitized = value

    sanitized = re.sub(r"[\r\n\t]+", " ", sanitized)
    sanitized = re.sub(r"[。？！?!].*$", "", sanitized)
    return " ".join(sanitized.split()).strip()

def translate_search_keyword_to_korean(keyword: str, fallback_text: str | None = None) -> TranslationBatchResult:
    # 中文搜索词先转成韩文回源关键词；失败时回退原词，保证搜索链路不断。
    normalized_keyword = " ".join(keyword.strip().split())
    fallback = fallback_text or normalized_keyword

    if not normalized_keyword:
        return TranslationBatchResult(translations=[""], provider="fallback")

    if HANGUL_PATTERN.search(normalized_keyword):
        return TranslationBatchResult(translations=[normalized_keyword], provider="input")

    cache_key = normalized_keyword.lower()
    if cache_key in _keyword_translation_cache:
        cached_text, cached_model = _keyword_translation_cache[cache_key]
        return TranslationBatchResult(translations=[cached_text], provider="cache", model=cached_model)

    if not is_deepseek_translation_enabled():
        return TranslationBatchResult(translations=[fallback], provider="fallback")

    messages = [
        {
            "role": "system",
            "content": "You translate Chinese beauty e-commerce search keywords into concise Korean shopping keywords.",
        },
        {
            "role": "user",
            "content": (
                "Translate this Chinese beauty search keyword to one concise Korean Olive Young search keyword.\n"
                "Return exactly one Korean keyword or phrase. Do not add explanations, punctuation, romanization, or Chinese.\n"
                "Prefer common Korean shopping terms such as 선크림, 클렌징폼, 립스틱, 치약.\n"
                f"Keyword: {normalized_keyword}"
            ),
        },
    ]

    try:
        output_text, model = _request_deepseek_text(messages)
        translated_keyword = _clean_single_keyword(output_text)
    except Exception:
        return TranslationBatchResult(translations=[fallback], provider="fallback")

    if not translated_keyword or not HANGUL_PATTERN.search(translated_keyword):
        return TranslationBatchResult(translations=[fallback], provider="fallback")

    _keyword_translation_cache[cache_key] = (translated_keyword, model)

    return TranslationBatchResult(translations=[translated_keyword], provider="deepseek", model=model)

def translate_text(text: str, source_language: str, target_language: str, fallback_text: str | None = None) -> str:
    result = translate_texts(
        [text],
        source_language=source_language,
        target_language=target_language,
        fallback_texts=[fallback_text or text],
    )
    return result.translations[0]


def translate_texts(
    texts: Sequence[str],
    *,
    source_language: str,
    target_language: str,
    fallback_texts: Sequence[str] | None = None,
) -> TranslationBatchResult:
    # 只把包含韩文的文本送去大模型，纯中文/英文内容直接复用 fallback，减少不必要调用。
    normalized_texts = [" ".join(text.strip().split()) for text in texts]
    if fallback_texts is not None and len(fallback_texts) != len(normalized_texts):
        raise ValueError("fallback_texts must match the length of texts")

    normalized_fallbacks = (
        [" ".join(text.strip().split()) for text in fallback_texts]
        if fallback_texts is not None
        else normalized_texts
    )
    if not normalized_texts:
        return TranslationBatchResult(translations=[], provider="fallback")

    cached_or_fallback = list(normalized_fallbacks)
    cached_count = 0
    cached_model: str | None = None
    pending_indices: list[int] = []
    pending_texts: list[str] = []

    for index, text in enumerate(normalized_texts):
        cache_key = (source_language, target_language, text)
        if cache_key in _translation_cache:
            cached_text, model = _translation_cache[cache_key]
            cached_or_fallback[index] = cached_text
            cached_count += 1
            cached_model = cached_model or model
            continue
        if not _should_translate_with_llm(text):
            continue
        pending_indices.append(index)
        pending_texts.append(text)

    if not pending_texts or not is_deepseek_translation_enabled():
        provider = "cache" if cached_count else "fallback"
        return TranslationBatchResult(translations=cached_or_fallback, provider=provider, model=cached_model)

    try:
        batch_result = _request_deepseek_translations(pending_texts, source_language, target_language)
    except Exception:
        return TranslationBatchResult(translations=cached_or_fallback, provider="fallback")

    for index, translated_text in zip(pending_indices, batch_result.translations):
        cache_key = (source_language, target_language, normalized_texts[index])
        _translation_cache[cache_key] = (translated_text, batch_result.model)
        cached_or_fallback[index] = translated_text

    return TranslationBatchResult(
        translations=cached_or_fallback,
        provider=batch_result.provider,
        model=batch_result.model,
    )
