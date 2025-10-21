"""Utility helpers for external translation services."""
from __future__ import annotations

import logging
import os
from typing import Optional

import requests

logger = logging.getLogger(__name__)

DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")
DEEPLX_API_URL = os.getenv("DEEPLX_API_URL")  # e.g. http://localhost:1188


def _normalize_language(code: Optional[str]) -> Optional[str]:
    if not code:
        return None
    code = code.strip()
    if not code or code.lower() in {"auto", "automatic detection"}:
        return None
    return code.upper()


def deepl_translate(text: str, source_lang: Optional[str], target_lang: str) -> str:
    """Translate text using the official DeepL API.

    Parameters
    ----------
    text:
        Text to translate.
    source_lang:
        Two-letter (or supported) language code. If ``None`` or ``"auto"`` the
        DeepL API will autodetect the source language.
    target_lang:
        Language code for the translation target.
    """

    if not DEEPL_API_KEY:
        raise ValueError("DEEPL_API_KEY is not set")

    normalized_source = _normalize_language(source_lang)
    normalized_target = _normalize_language(target_lang)
    if not normalized_target:
        raise ValueError("target_lang must be provided for DeepL translation")

    payload = {
        "auth_key": DEEPL_API_KEY,
        "text": text,
        "target_lang": normalized_target,
    }
    if normalized_source:
        payload["source_lang"] = normalized_source

    response = requests.post(
        "https://api-free.deepl.com/v2/translate",
        data=payload,
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    try:
        return data["translations"][0]["text"]
    except (KeyError, IndexError) as exc:
        logger.error("Unexpected DeepL response: %s", data)
        raise RuntimeError("Unexpected DeepL response structure") from exc


def deeplx_translate(text: str, source_lang: Optional[str], target_lang: str) -> str:
    """Translate text using a DeepLX compatible service."""

    if not DEEPLX_API_URL:
        raise ValueError("DEEPLX_API_URL is not set")

    normalized_source = _normalize_language(source_lang) or "AUTO"
    normalized_target = _normalize_language(target_lang)
    if not normalized_target:
        raise ValueError("target_lang must be provided for DeepLX translation")

    payload = {
        "text": text,
        "source_lang": normalized_source,
        "target_lang": normalized_target,
    }

    response = requests.post(
        f"{DEEPLX_API_URL.rstrip('/')}/translate",
        json=payload,
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()

    # DeepLX implementations vary slightly – try common keys in order.
    for key in ("data", "result", "translated_text"):
        value = data.get(key)
        if isinstance(value, str):
            return value
    logger.error("Unexpected DeepLX response: %s", data)
    raise RuntimeError("Unexpected DeepLX response structure")
