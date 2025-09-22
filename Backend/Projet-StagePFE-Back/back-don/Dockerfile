# ---- Base ----
FROM python:3.11-slim

# Environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System deps 
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    libssl-dev \
    libffi-dev \
    libpq-dev \
 && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN python -m pip install --no-cache-dir --upgrade pip setuptools wheel \
 && pip install --no-cache-dir -r requirements.txt \
 # to ensure Prometheus metrics are available
 && pip install --no-cache-dir prometheus-client

# App code
COPY . .

# to keep ML disabled by default to prevent crashes on missing transformers/torch
ENV USE_ML=0

# The app listens on 8089 
EXPOSE 8089


CMD ["python", "app.py"]
