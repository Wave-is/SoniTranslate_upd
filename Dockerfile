# ===============================
# Base image: PyTorch + CUDA 11.8
# ===============================
FROM pytorch/pytorch:2.1.0-cuda11.8-cudnn8-runtime

# ===============================
# Environment setup
# ===============================
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Kiev
ENV PYTHONUNBUFFERED=1

# ===============================
# System dependencies
# ===============================
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git \
        wget \
        curl \
        ffmpeg \
        libsndfile1 \
        tzdata \
        libgl1 \
        libglib2.0-0 \
        libxrender1 \
        libxext6 \
        libsm6 \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# ===============================
# Working directory
# ===============================
WORKDIR /app

# ===============================
# Copy project files
# ===============================
COPY . /app

# ===============================
# Python dependencies
# ===============================
# (если есть requirements.txt — устанавливаем)
RUN pip install --upgrade pip wheel setuptools && \
    if [ -f requirements.txt ]; then \
        pip install --no-cache-dir -r requirements.txt; \
    fi

# ===============================
# Optional: install typical deps for SoniTranslate
# ===============================
# RUN pip install --no-cache-dir torch torchvision torchaudio \
#     fastapi uvicorn requests tqdm aiohttp

# ===============================
# Expose port for API (default: 7860)
# ===============================
EXPOSE 7860

# ===============================
# Launch app
# ===============================
# Если у тебя главный файл называется app.py
# — он запустится автоматически
CMD ["python", "app.py"]
