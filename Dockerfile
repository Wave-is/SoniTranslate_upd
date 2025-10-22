# Используем базовый образ PyTorch
FROM pytorch/pytorch:2.1.0-cuda11.8-cudnn8-runtime

# Рабочая директория
WORKDIR /app

# Копируем файлы
COPY . /app

# Устанавливаем зависимости
RUN apt-get update && apt-get install -y git ffmpeg libsndfile1 \
 && pip install --no-cache-dir -r requirements.txt

# Запускаем сервер
CMD ["python", "app.py"]
