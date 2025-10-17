# custom_tts.py (обновлённая версия)

import os
import tempfile
from pathlib import Path
from google.cloud import texttospeech
from gradio_client import Client

GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
STYLETTS2_URL = "http://localhost:7861"

# Полный список поддерживаемых голосов
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
    "Юрій Кудрявець"
]

def google_tts(text: str, lang: str = "uk-UA", voice_name: str = "uk-UA-Standard-A") -> str:
    if not GOOGLE_CREDENTIALS_PATH or not Path(GOOGLE_CREDENTIALS_PATH).exists():
        raise ValueError("GOOGLE_APPLICATION_CREDENTIALS не указан или файл не найден")

    client = texttospeech.TextToSpeechClient.from_service_account_json(GOOGLE_CREDENTIALS_PATH)
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(language_code=lang, name=voice_name)
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.LINEAR16)

    response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
        f.write(response.audio_content)
        return f.name

def styletts2_ua_tts(text: str, voice_name: str = "Інна Гелевера", speed: float = 1.0) -> str:
    if voice_name not in STYLETTS2_UA_VOICES:
        raise ValueError(f"Голос '{voice_name}' не поддерживается. Доступные: {STYLETTS2_UA_VOICES}")

    client = Client(STYLETTS2_URL, verbose=False)
    try:
        result = client.predict(
            model_name="multi",
            text=text,
            speed=speed,
            voice_name=voice_name,
            api_name="/synthesize"
        )
        return result  # путь к .wav файлу внутри контейнера
    except Exception as e:
        raise RuntimeError(f"StyleTTS2-UA error: {e}")