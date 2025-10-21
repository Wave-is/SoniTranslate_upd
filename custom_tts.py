"""Helper utilities for external TTS engines used by SoniTranslate."""
from __future__ import annotations

import base64
import logging
import os
import tempfile
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, Iterable, List, Optional

import requests

logger = logging.getLogger(__name__)

STYLETTS2_DEFAULT_URL = os.getenv("STYLETTS2_URL", "http://localhost:7861")
VIBEVOICE_DEFAULT_URL = os.getenv("VIBEVOICE_URL", "http://localhost:7890")
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")


@dataclass(frozen=True)
class GoogleVoice:
    name: str
    language_code: str
    natural_sample_rate_hz: Optional[int] = None
    ssml_gender: Optional[str] = None


def _normalize_base_url(url: str) -> str:
    if not url:
        raise ValueError("A base URL must be provided for the remote TTS service")
    url = url.strip()
    if url.endswith("/"):
        url = url[:-1]
    return url


def _post_gradio(base_url: str, api_name: str, data: Iterable, timeout: int = 300) -> Dict:
    url = f"{_normalize_base_url(base_url)}{api_name}"
    response = requests.post(url, json={"data": list(data)}, timeout=timeout)
    response.raise_for_status()
    return response.json()


def _download_gradio_audio(base_url: str, payload) -> bytes:
    """Download audio bytes from a Gradio payload."""

    if isinstance(payload, list):
        if not payload:
            raise RuntimeError("Empty audio payload")
        payload = payload[0]

    if isinstance(payload, dict):
        if "data" in payload and isinstance(payload["data"], str) and payload["data"].startswith("data:"):
            # data URI
            _, encoded = payload["data"].split(",", 1)
            return base64.b64decode(encoded)
        file_ref = payload.get("path") or payload.get("name") or payload.get("url")
    elif isinstance(payload, str):
        file_ref = payload
    else:
        raise RuntimeError(f"Unsupported Gradio payload type: {type(payload)!r}")

    if not file_ref:
        raise RuntimeError("Audio payload does not contain a file reference")

    if str(file_ref).startswith("http"):
        download_url = file_ref
    else:
        download_url = f"{_normalize_base_url(base_url)}/file={str(file_ref).lstrip('/')}"

    response = requests.get(download_url, timeout=300)
    response.raise_for_status()
    return response.content


def _write_temp_audio(audio_bytes: bytes, suffix: str = ".wav") -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(audio_bytes)
        return temp_file.name


# ---------------------------------------------------------------------------
# StyleTTS2 Ukrainian
# ---------------------------------------------------------------------------

STYLETTS2_UA_VOICES = [
    "Інна Гелевера",
    "Анастасія Павленко",
    "Артем Окороков",
    "Вʼячеслав Дудко",
    "Вероніка Дорош",
    "Влада Муравець",
    "Вікторія Левченко",
    "Гаська Шиян",
    "Денис Денисенко",
    "Катерина Потапенко",
    "Кирило Татарченко",
    "Людмила Чиркова",
    "Марина Панас",
    "Марися Нікітюк",
    "Марта Мольфар",
    "Марічка Штирбулова",
    "Матвій Ніколаєв",
    "Михайло Тишин",
    "Олександр Ролдугін",
    "Олена Шверк",
    "Павло Буковський",
    "Петро Філяк",
    "Поліна Еккерт",
    "Поліна Еккерт(хлопчик)",
    "Роман Куліш",
    "Слава Красовська",
    "Тарас Василюк",
    "Тетяна Гончарова",
    "Тетяна Лукинюк",
    "Юрій Вихованець",
    "Юрій Кудрявець",
]


def styletts2_available_voices() -> List[str]:
    return STYLETTS2_UA_VOICES.copy()


def styletts2_synthesize(
    text: str,
    voice_name: str,
    *,
    model_name: str = "multi",
    speed: float = 1.0,
    base_url: Optional[str] = None,
) -> str:
    if voice_name not in STYLETTS2_UA_VOICES:
        raise ValueError(f"Unsupported StyleTTS2 voice: {voice_name}")

    base = base_url or STYLETTS2_DEFAULT_URL
    result = _post_gradio(base, "/synthesize", [model_name, text, speed, voice_name])
    audio_bytes = _download_gradio_audio(base, result.get("data"))
    return _write_temp_audio(audio_bytes, suffix=".wav")


# ---------------------------------------------------------------------------
# VibeVoice
# ---------------------------------------------------------------------------

VIBEVOICE_DEFAULT_VOICES = [
    "zh-Xinran_woman",
    "en-Alice_woman_bgm",
    "zh-Anchen_man_bgm",
    "in-Samuel_man",
    "en-Alice_woman",
    "en-Frank_man",
    "zh-Bowen_man",
    "en-Maya_woman",
    "en-Carter_man",
    "en-Yasser_man",
]


def vibevoice_available_voices(base_url: Optional[str] = None) -> List[str]:
    base = base_url or VIBEVOICE_DEFAULT_URL
    try:
        result = _post_gradio(base, "/update_speaker_visibility", [4])
    except Exception as exc:  # pragma: no cover - depends on external service
        logger.warning("Could not retrieve VibeVoice voices: %s", exc)
        return VIBEVOICE_DEFAULT_VOICES.copy()

    voices: List[str] = []
    data = result.get("data", [])
    for column in data:
        if isinstance(column, list):
            for entry in column:
                if isinstance(entry, str) and entry not in voices:
                    voices.append(entry)
    return voices or VIBEVOICE_DEFAULT_VOICES.copy()


def vibevoice_synthesize(
    text: str,
    voice_name: str,
    *,
    cfg_scale: float = 1.3,
    num_speakers: int = 1,
    base_url: Optional[str] = None,
) -> str:
    base = base_url or VIBEVOICE_DEFAULT_URL
    payload = [
        num_speakers,
        text,
        voice_name,
        voice_name,
        voice_name,
        voice_name,
        cfg_scale,
    ]
    result = _post_gradio(base, "/generate_podcast_wrapper", payload)
    audio_bytes = _download_gradio_audio(base, result.get("data"))
    return _write_temp_audio(audio_bytes, suffix=".wav")


# ---------------------------------------------------------------------------
# Google Cloud Text-to-Speech
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _google_tts_client(credentials_path: Optional[str]):
    try:
        from google.cloud import texttospeech  # type: ignore
    except ModuleNotFoundError as exc:  # pragma: no cover - import guarded at runtime
        raise RuntimeError(
            "google-cloud-texttospeech is required for Google TTS support"
        ) from exc

    if credentials_path:
        return texttospeech.TextToSpeechClient.from_service_account_json(
            credentials_path
        )
    return texttospeech.TextToSpeechClient()


def google_cloud_available_voices(
    credentials_path: Optional[str] = GOOGLE_CREDENTIALS_PATH,
) -> Dict[str, GoogleVoice]:
    client = _google_tts_client(credentials_path)
    from google.cloud import texttospeech  # type: ignore

    response = client.list_voices()
    voices: Dict[str, GoogleVoice] = {}
    for voice in response.voices:
        language_code = voice.language_codes[0] if voice.language_codes else ""
        display_name = voice.name
        ssml_gender = texttospeech.SsmlVoiceGender(voice.ssml_gender).name
        voices[display_name] = GoogleVoice(
            name=voice.name,
            language_code=language_code,
            natural_sample_rate_hz=voice.natural_sample_rate_hz,
            ssml_gender=ssml_gender,
        )
    return voices


def google_cloud_synthesize(
    text: str,
    *,
    voice: GoogleVoice,
    speaking_rate: float = 1.0,
    credentials_path: Optional[str] = GOOGLE_CREDENTIALS_PATH,
) -> str:
    client = _google_tts_client(credentials_path)
    from google.cloud import texttospeech  # type: ignore

    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice_params = texttospeech.VoiceSelectionParams(
        language_code=voice.language_code,
        name=voice.name,
        ssml_gender=texttospeech.SsmlVoiceGender[voice.ssml_gender]
        if voice.ssml_gender
        else texttospeech.SsmlVoiceGender.SSML_VOICE_GENDER_UNSPECIFIED,
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16,
        speaking_rate=speaking_rate,
    )
    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice_params,
        audio_config=audio_config,
    )
    return _write_temp_audio(response.audio_content, suffix=".wav")
