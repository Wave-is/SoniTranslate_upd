# custom_translators.py
import os
import requests
from typing import Optional

DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")
DEEPLX_API_URL = os.getenv("DEEPLX_API_URL")  # e.g. http://localhost:1188/translate

def deepl_translate(text: str, source_lang: str, target_lang: str) -> str:
    if not DEEPL_API_KEY:
        raise ValueError("DEEPL_API_KEY is not set")
    url = "https://api-free.deepl.com/v2/translate"
    data = {
        "auth_key": DEEPL_API_KEY,
        "text": text,
        "source_lang": source_lang.upper(),
        "target_lang": target_lang.upper()
    }
    resp = requests.post(url, data=data)
    resp.raise_for_status()
    return resp.json()["translations"][0]["text"]

def deeplx_translate(text: str, source_lang: str, target_lang: str) -> str:
    if not DEEPLX_API_URL:
        raise ValueError("DEEPLX_API_URL is not set")
    payload = {
        "text": text,
        "source_lang": source_lang.upper(),
        "target_lang": target_lang.upper()
    }
    resp = requests.post(f"{DEEPLX_API_URL.rstrip('/')}/translate", json=payload)
    resp.raise_for_status()
    return resp.json().get("data", resp.json().get("result", ""))