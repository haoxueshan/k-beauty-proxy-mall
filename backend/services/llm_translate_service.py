from __future__ import annotations

import json
import os
import re
import threading
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
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
_translation_cache_loaded = False
_translation_cache_lock = threading.Lock()
_translation_warmup_lock = threading.Lock()
_translation_warmup_keys: set[tuple[str, str, tuple[str, ...]]] = set()
TRANSLATION_CACHE_PATH = Path(
    os.getenv(
        "TRANSLATION_CACHE_PATH",
        str(Path(__file__).resolve().parents[1] / "data" / "translation_cache.json"),
    )
)

@dataclass(frozen=True)
class TranslationBatchResult:
    translations: list[str]
    provider: str
    model: str | None = None


def get_translation_settings() -> dict[str, str | bool]:
    # DeepSeek uses an OpenAI-compatible SDK.
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


def _serialize_translation_cache_key(cache_key: tuple[str, str, str]) -> str:
    return json.dumps(list(cache_key), ensure_ascii=False, separators=(",", ":"))


def _deserialize_translation_cache_key(raw_key: str) -> tuple[str, str, str] | None:
    try:
        payload = json.loads(raw_key)
    except json.JSONDecodeError:
        return None
    if (
        isinstance(payload, list)
        and len(payload) == 3
        and all(isinstance(item, str) for item in payload)
    ):
        return payload[0], payload[1], payload[2]
    return None


def _ensure_translation_cache_loaded() -> None:
    global _translation_cache_loaded
    if _translation_cache_loaded:
        return

    with _translation_cache_lock:
        if _translation_cache_loaded:
            return
        if TRANSLATION_CACHE_PATH.exists():
            try:
                payload = json.loads(TRANSLATION_CACHE_PATH.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                payload = {}
            if isinstance(payload, dict):
                for raw_key, raw_value in payload.items():
                    if not isinstance(raw_key, str) or not isinstance(raw_value, dict):
                        continue
                    cache_key = _deserialize_translation_cache_key(raw_key)
                    translated_text = raw_value.get("translation")
                    model = raw_value.get("model")
                    if cache_key and isinstance(translated_text, str):
                        _translation_cache[cache_key] = (
                            translated_text,
                            model if isinstance(model, str) else None,
                        )
        _translation_cache_loaded = True


def _persist_translation_cache() -> None:
    TRANSLATION_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        _serialize_translation_cache_key(cache_key): {
            "translation": translated_text,
            "model": model,
        }
        for cache_key, (translated_text, model) in _translation_cache.items()
    }
    temp_path = TRANSLATION_CACHE_PATH.with_suffix(".tmp")
    temp_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temp_path.replace(TRANSLATION_CACHE_PATH)


def _save_translation_cache_entry(
    cache_key: tuple[str, str, str],
    translated_text: str,
    model: str | None,
) -> None:
    _save_translation_cache_entries([(cache_key, translated_text, model)])


def _save_translation_cache_entries(
    entries: Sequence[tuple[tuple[str, str, str], str, str | None]],
) -> None:
    if not entries:
        return
    with _translation_cache_lock:
        for cache_key, translated_text, model in entries:
            _translation_cache[cache_key] = (translated_text, model)
        try:
            _persist_translation_cache()
        except OSError:
            pass


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
    # Some model responses include markdown or prose, so parse the JSON array slice.
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
    # Shared DeepSeek request wrapper for title and keyword translation.
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
    # 商品标题翻译要求：
    # 1. 韩文商品信息必须翻译成简体中文
    # 2. 保留品牌名、英文名、色号、容量、规格、赠品、套装和括号结构
    # 3. 不改写成营销标题，不添加原文没有的信息
    user_payload = [
        {"index": index, "text": text}
        for index, text in enumerate(texts)
    ]

    return [
        {
            "role": "system",
            "content": (
                "你是一名专门处理 Olive Young 韩妆商品标题的高准确度翻译助手。"
                "你的任务是将韩文商品标题准确翻译为简体中文。"
                "翻译必须忠实原文、信息完整、表达自然，但不能改写成营销文案。"
                "不得添加原文没有的功效、卖点或解释。"
            ),
        },
        {
            "role": "user",
            "content": (
                "请将下面每个 Olive Young 商品标题准确翻译成简体中文。\n\n"

                "【核心要求】\n"
                "1. 韩文商品信息必须翻译成简体中文，输出结果中不要残留韩文。\n"
                "2. 品牌名、系列名、色号名如果有官方英文名、罗马字或常用写法，可以保留原写法，"
                "例如 3CE、NAMING、rom&nd、Torriden。\n"
                "3. 商品品类、功效描述、肤质描述、颜色说明、容量、规格、数量、赠品、套装、企划、限定、"
                "版本、括号内信息都必须翻译成中文。\n"
                "4. 保持原始信息顺序，不要调整标题结构。\n"
                "5. 不要总结、不要省略、不要推测、不要添加卖点、不要拆分标题。\n"
                "6. 保留英文单词、SPF/PA、色号、容量、型号代码、数字、百分号、加号、斜杠、"
                "标点符号和括号结构。\n\n"

                "【常见词翻译规则】\n"
                "기획 = 企划\n"
                "증정 = 赠送 / 赠品\n"
                "세트 = 套装\n"
                "리필 = 替换装 / 补充装\n"
                "본품 = 正装\n"
                "단독 = 独家\n"
                "한정 = 限定\n"
                "대용량 = 大容量\n"
                "선착순 = 先到先得\n"
                "컬러 = 颜色\n"
                "호 = 号\n\n"

                "【输出格式】\n"
                "1. 只返回 JSON 字符串数组。\n"
                "2. 数组顺序必须与输入项目的 index 顺序完全一致。\n"
                "3. 输出数量必须与输入数量完全一致。\n"
                "4. 不要返回 index，不要返回对象，不要解释，不要使用 markdown。\n"
                "5. JSON 必须可以被 json.loads() 直接解析。\n\n"

                f"源语言：{source_language}\n"
                f"目标语言：{target_language}\n"
                f"待翻译项目：{json.dumps(user_payload, ensure_ascii=False)}"
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
    # Convert Chinese search terms to Korean source keywords; fallback keeps search usable.
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
                "Use these examples when relevant: 防晒 -> 선크림, 洁面 -> 클렌징폼, 面膜 -> 마스크팩, 口红 -> 립틴트.\n"
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
    # Only send text containing Hangul to the LLM; other text can reuse fallback.
    _ensure_translation_cache_loaded()
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

    cache_entries: list[tuple[tuple[str, str, str], str, str | None]] = []
    for index, translated_text in zip(pending_indices, batch_result.translations):
        cache_key = (source_language, target_language, normalized_texts[index])
        cache_entries.append((cache_key, translated_text, batch_result.model))
        cached_or_fallback[index] = translated_text
    _save_translation_cache_entries(cache_entries)

    return TranslationBatchResult(
        translations=cached_or_fallback,
        provider=batch_result.provider,
        model=batch_result.model,
    )


def translate_texts_fast(
    texts: Sequence[str],
    *,
    source_language: str,
    target_language: str,
    fallback_texts: Sequence[str] | None = None,
) -> TranslationBatchResult:
    _ensure_translation_cache_loaded()
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

    translations = list(normalized_fallbacks)
    cached_count = 0
    cached_model: str | None = None
    pending_texts: list[str] = []
    pending_fallbacks: list[str] = []

    for index, text in enumerate(normalized_texts):
        cache_key = (source_language, target_language, text)
        cached = _translation_cache.get(cache_key)
        if cached is not None:
            translations[index] = cached[0]
            cached_count += 1
            cached_model = cached_model or cached[1]
            continue

        if _should_translate_with_llm(text):
            pending_texts.append(text)
            pending_fallbacks.append(normalized_fallbacks[index])

    _warm_translation_cache_async(
        pending_texts,
        source_language=source_language,
        target_language=target_language,
        fallback_texts=pending_fallbacks,
    )

    provider = "cache" if cached_count and cached_count == len(normalized_texts) else "fallback"
    return TranslationBatchResult(translations=translations, provider=provider, model=cached_model)


def _warm_translation_cache_async(
    texts: Sequence[str],
    *,
    source_language: str,
    target_language: str,
    fallback_texts: Sequence[str],
) -> None:
    pending_texts = [text for text in texts if text]
    if not pending_texts or not is_deepseek_translation_enabled():
        return

    warmup_key = (source_language, target_language, tuple(pending_texts))
    with _translation_warmup_lock:
        if warmup_key in _translation_warmup_keys:
            return
        _translation_warmup_keys.add(warmup_key)

    def worker() -> None:
        try:
            translate_texts(
                pending_texts,
                source_language=source_language,
                target_language=target_language,
                fallback_texts=fallback_texts,
            )
        finally:
            with _translation_warmup_lock:
                _translation_warmup_keys.discard(warmup_key)

    threading.Thread(target=worker, name="translation-cache-warmup", daemon=True).start()
