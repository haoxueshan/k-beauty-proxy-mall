from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Sequence

from dotenv import load_dotenv

load_dotenv()

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - dependency is optional until installed
    OpenAI = None  # type: ignore[assignment]


DEFAULT_OPENAI_TRANSLATION_MODEL = "gpt-4o-mini"
HANGUL_PATTERN = re.compile(r"[\uac00-\ud7a3]")
CODE_BLOCK_PATTERN = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)
_translation_cache: dict[tuple[str, str, str], tuple[str, str | None]] = {}


@dataclass(frozen=True)
class TranslationBatchResult:
    translations: list[str]
    provider: str
    model: str | None = None


def get_translation_settings() -> dict[str, str | bool]:
    enabled = os.getenv("OPENAI_TRANSLATION_ENABLED", "true").strip().lower() not in {"0", "false", "no"}
    return {
        "api_key": os.getenv("OPENAI_API_KEY", "").strip(),
        "model": os.getenv("OPENAI_TRANSLATION_MODEL", "").strip()
        or os.getenv("OPENAI_MODEL", "").strip()
        or DEFAULT_OPENAI_TRANSLATION_MODEL,
        "enabled": enabled,
    }


def is_openai_translation_enabled() -> bool:
    settings = get_translation_settings()
    return bool(settings["enabled"] and settings["api_key"] and OpenAI is not None)


@lru_cache(maxsize=1)
def _get_openai_client():
    settings = get_translation_settings()
    api_key = str(settings["api_key"])
    if not api_key or OpenAI is None:
        return None
    return OpenAI(api_key=api_key)


def _sanitize_model_output(text: str) -> str:
    return CODE_BLOCK_PATTERN.sub("", text.strip()).strip()


def _parse_json_array(raw_output: str, expected_length: int) -> list[str]:
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


def _build_messages(texts: Sequence[str], source_language: str, target_language: str) -> list[dict]:
    developer_message = {
        "role": "developer",
        "content": (
            "You are a professional e-commerce translator. "
            "Translate product titles accurately into concise Simplified Chinese. "
            "Preserve brand names, English words, SPF/PA values, shade numbers, capacities, and model codes. "
            "Return only a JSON array of translated strings in the same order as the input."
        ),
    }
    user_payload = [{"index": index, "text": text} for index, text in enumerate(texts)]
    user_message = {
        "role": "user",
        "content": (
            f"Translate the following items from {source_language} to {target_language}. "
            "Do not add explanations.\n"
            f"{json.dumps(user_payload, ensure_ascii=False)}"
        ),
    }
    return [developer_message, user_message]


def _request_openai_translations(
    texts: Sequence[str],
    source_language: str,
    target_language: str,
) -> TranslationBatchResult:
    client = _get_openai_client()
    settings = get_translation_settings()
    model = str(settings["model"])
    if client is None:
        raise RuntimeError("OpenAI client is not configured")

    response = client.responses.create(
        model=model,
        input=_build_messages(texts, source_language, target_language),
    )
    output_text = getattr(response, "output_text", "")
    translations = _parse_json_array(output_text, len(texts))
    return TranslationBatchResult(translations=translations, provider="openai", model=model)


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

    if not pending_texts or not is_openai_translation_enabled():
        provider = "cache" if cached_count else "fallback"
        return TranslationBatchResult(translations=cached_or_fallback, provider=provider, model=cached_model)

    try:
        batch_result = _request_openai_translations(pending_texts, source_language, target_language)
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
