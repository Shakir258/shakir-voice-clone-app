FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PORT=7860 \
    HOST=0.0.0.0 \
    DEVICE=cpu \
    CORS_ORIGINS="*" \
    OPENVOICE_CHECKPOINT_DIR=/app/models/checkpoints_v2

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    wget \
    unzip \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir --no-deps git+https://github.com/myshell-ai/OpenVoice.git@main git+https://github.com/myshell-ai/MeloTTS.git && \
    python -m unidic download && \
    python -m melo.download_utils

# Download and setup OpenVoice V2 model checkpoints automatically
RUN mkdir -p models && \
    wget -q https://myshell-public-repo-host.s3.amazonaws.com/openvoice/checkpoints_v2_0417.zip -O /tmp/checkpoints.zip && \
    unzip -q /tmp/checkpoints.zip -d models/ && \
    rm /tmp/checkpoints.zip

# Copy backend code
COPY . .

# Ensure data directories exist
RUN mkdir -p data/voices data/generated data/temp data/cache data/previews

# Expose Hugging Face Space port
EXPOSE 7860

# Start FastAPI application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
