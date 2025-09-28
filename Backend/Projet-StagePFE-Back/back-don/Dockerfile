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
COPY requirements.txt requirements-ml.txt .
RUN python -m pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt \ 
  
    && pip install --no-cache-dir -r requirements-ml.txt


# App code
COPY . .


ENV USE_ML=0

# The app listens on 8089 
EXPOSE 8089


CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "app:app"]
