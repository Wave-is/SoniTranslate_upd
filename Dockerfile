# Используем образ Python 3.10 в качестве базового
FROM pytorch/pytorch:2.1.0-cuda11.8-cudnn8-runtime
# Устанавливаем часовой пояс (пример для Москвы)
ARG TZ=Europe/Moscow
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
git \
git-lfs \
ffmpeg \
wget \
g++ \
&& rm -rf /var/lib/apt/lists/*

# Устанавливаем директорию проекта
WORKDIR /app
# Клонируем репозиторий SoniTranslate с GitHub
ARG GITHUB_REPO=https://github.com/R3gm/SoniTranslate.git
ARG BRANCH=main
RUN git clone ${GITHUB_REPO} . && \
git checkout ${BRANCH}
# Устанавливаем lfs
RUN git lfs install
# Устанавливаем зависимости Python
RUN python -m pip install --upgrade pip
RUN python -m pip install pip==23.1.2
RUN pip install -r requirements_base.txt -v
# Устанавливаем fairseq из репозитория
RUN git clone https://github.com/facebookresearch/fairseq.git /tmp/fairseq && \
cd /tmp/fairseq && \
pip install --editable ./
# Устанавливаем остальные зависимости из requirements_extra.txt, исключая fairseq
RUN sed '/^fairseq/d' -e '/^#/d' requirements_extra.txt | xargs pip install -v
RUN pip install onnxruntime-gpu
# Опционально: Устанавливаем Piper TTS
ARG INSTALL_PIPER_TTS=true
RUN if [ "$INSTALL_PIPER_TTS" = "true" ]; then pip install -q piper-tts==1.2.0; fi
# Опционально: Устанавливаем Coqui XTTS
ARG INSTALL_COQUI_XTTS=true
RUN if [ "$INSTALL_COQUI_XTTS" = "true" ]; then pip install -q -r requirements_xtts.txt && pip install -q TTS==0.21.1 --no-deps; fi
# Устанавливаем переменные окружения
ARG DEFAULT_HF_TOKEN=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
ENV YOUR_HF_TOKEN=${DEFAULT_HF_TOKEN}
# Создаем директории
RUN mkdir -p /app/downloads /app/logs /app/weights /app/clean_song_output /app/_XTTS_ /app/audio2/audio /app/audio /app/outputs
# Запуск приложения
ENTRYPOINT ["python", "app_rvc.py"]
CMD ["--theme", "Taithrah/Minimal", "--verbosity_level", "info", "--language", "russian"]
