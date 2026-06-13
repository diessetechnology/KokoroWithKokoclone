FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    GRADIO_SERVER_NAME=0.0.0.0 \
    GRADIO_SERVER_PORT=7860 \
    GRADIO_ANALYTICS_ENABLED=False

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ffmpeg \
    espeak-ng \
    libsndfile1 \
    build-essential \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN git clone --depth=1 https://github.com/Ashish-Patnaik/kokoclone.git /app

# CPU-only PyTorch first, then project requirements.
RUN pip install --upgrade pip setuptools wheel \
    && pip install --index-url https://download.pytorch.org/whl/cpu torch torchaudio \
    && pip install -r requirements.txt \
    && pip install "kokoro-onnx[cpu]" gradio-client

EXPOSE 7860

CMD ["python", "app.py"]
