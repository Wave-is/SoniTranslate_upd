# apply_patch.py
import re

# --- 1. Чтение оригинального файла ---
with open("app_rvc.py", "r", encoding="utf-8") as f:
    content = f.read()

# --- 2. Добавление импортов в начало (после существующих импортов) ---
imports_to_add = """
# === CUSTOM MODULES ===
from custom_translators import deepl_translate, deeplx_translate
from custom_tts import google_tts, styletts2_ua_tts
# ======================
"""

# Находим последнюю строку с import или from ... import ...
last_import_line = 0
lines = content.splitlines()
for i, line in enumerate(lines):
    if line.startswith("import ") or line.startswith("from "):
        last_import_line = i

# Вставляем после последнего импорта
lines.insert(last_import_line + 1, imports_to_add)
content = "\n".join(lines)

# --- 3. Расширение списка переводчиков ---
# Ищем строку, где определён список переводчиков (обычно содержит "Google", "LibreTranslate" и т.д.)
content = re.sub(
    r'(TRANSLATORS\s*=\s*\[[^\]]*")Google Translate"([^]]*\])',
    r'\1Google Translate", "DeepL", "DeepLX"\2',
    content
)

# --- 4. Расширение списка TTS ---
content = re.sub(
    r'(TTS_ENGINES\s*=\s*\[[^\]]*")Edge TTS"([^]]*\])',
    r'\1Edge TTS", "Google TTS", "StyleTTS2-UA"\2',
    content
)

# --- 5. Добавление логики перевода ---
translate_block = '''
        elif translator == "DeepL":
            translated_text = deepl_translate(text_to_translate, source_lang, target_lang)
        elif translator == "DeepLX":
            translated_text = deeplx_translate(text_to_translate, source_lang, target_lang)
'''

# Ищем блок с `elif translator == "Google Translate":` и вставляем после него
content = re.sub(
    r'(elif translator == "Google Translate":.*?)(\s+elif|\s+else|\s+if)',
    r'\1' + translate_block + r'\2',
    content,
    flags=re.DOTALL
)

# --- 6. Добавление логики TTS ---
tts_block = '''
        elif tts_engine == "Google TTS":
            audio_path = google_tts(translated_text, lang=target_lang)
        elif tts_engine == "StyleTTS2-UA":
            # Используем голос по умолчанию или из интерфейса
            voice_name = "Інна Гелевера"  # можно сделать параметром
            audio_path = styletts2_ua_tts(translated_text, voice_name=voice_name)
'''

# Ищем блок с `elif tts_engine == "Edge TTS":` и вставляем после него
content = re.sub(
    r'(elif tts_engine == "Edge TTS":.*?)(\s+elif|\s+else|\s+if)',
    r'\1' + tts_block + r'\2',
    content,
    flags=re.DOTALL
)

# --- 7. Запись обратно ---
with open("app_rvc.py", "w", encoding="utf-8") as f:
    f.write(content)

print("✅ app_rvc.py успешно патчится!")