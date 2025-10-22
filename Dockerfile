# ===============================
#   🐳  SoniTranslate Dockerfile
# ===============================
# Базовый образ с PyTorch и CUDA 11.8
FROM pytorch/pytorch:2.1.0-cuda11.8-cudnn8-runtime

LABEL maintainer="Wave-IS"
LABEL description="Docker image for SoniTranslate with PyTorch, CUDA 11.8 and Gradio API"

# --------------------------------
# 1️⃣ Системные зависимости
# --------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    wget \
    curl \
    ffmpeg \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# --------------------------------
# 2️⃣ Создаём рабочую директорию
# --------------------------------
WORKDIR /app
COPY . /app

# --------------------------------
# 3️⃣ Устанавливаем Python-зависимости
# --------------------------------
RUN echo "📦 Installing Python dependencies..." && \
    pip install --upgrade pip wheel setuptools && \
    if [ -f requirements.txt ]; then \
        echo "⚙️  Fixing invalid torch requirement if needed..." && \
        sed -i 's/torch>=2\.1\.0+cu118/torch==2.1.0+cu118/' requirements.txt || true; \
        echo "📥 Installing from requirements.txt..." && \
        pip install --no-cache-dir -r requirements.txt; \
    else \
        echo "⚠️  No requirements.txt found, skipping..."; \
    fi

# --------------------------------
# 4️⃣ (Опционально) Дополнительные модули
# --------------------------------
# RUN pip install --no-cache-dir gradio fastapi uvicorn

# --------------------------------
# 5️⃣ Открываем порт и задаём команду запуска
# --------------------------------
EXPOSE 7860
CMD ["python", "app.py"]

# --------------------------------
# ✅ Примечания:
# --------------------------------
# • torch==2.1.0+cu118 гарантирует стабильную CUDA-совместимость
# • Если ты хочешь CPU-only версию, просто поменяй базовый образ:
#     FROM pytorch/pytorch:2.1.0-cpu
# • Кэширование pip-зависимостей не включено, т.к. GitHub Actions
#   автоматически кеширует Docker-слои между билдами
