
# Base image
FROM python:3.12.4-alpine3.20

# Ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/usr/local/bin:/usr/app/counter:/usr/app/:${PATH}" \
    UV_CACHE_DIR=/tmp/uv \
    UV_PROJECT_ENVIRONMENT=/tmp/uv-venv

WORKDIR /usr/app

COPY pyproject.toml .

RUN apk update && apk upgrade && \
    apk add --no-cache \
        curl \
        poppler-utils \
        tesseract-ocr \
        tesseract-ocr-data-por \
        tesseract-ocr-data-eng \
        tesseract-ocr-data-spa \
        tesseract-ocr-data-deu \
        tesseract-ocr-data-fra \
        tesseract-ocr-data-ita \
        tesseract-ocr-data-jpn \
        gcc \
        g++ \
        make \
        perl \
        exiftool \
        git && \
    curl -LsSf https://astral.sh/uv/0.4.6/install.sh | sh && \
    mv /root/.cargo/bin/uv /usr/local/bin/uv && \
    uv sync && \
    adduser --disabled-password --home /usr/app counter && \
    mkdir -p /tmp/uv && chown -R counter:counter /tmp/uv && \
    mkdir -p /tmp/uv-venv && chown -R counter:counter /tmp/uv-venv && \
    chown -R counter:counter /usr/app

USER counter

COPY . .
