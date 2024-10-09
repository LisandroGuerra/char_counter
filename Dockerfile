FROM python:3.12.4-alpine3.20

    ENV PYTHONUNBUFFERED 1
    ENV PYTHONDONTWRITEBYTECODE 1

WORKDIR /usr/app

COPY uv.lock .
COPY pyproject.toml .

ENV PATH="/root/.cargo/bin:${PATH}"
ENV PATH="/usr/app/counter:${PATH}"
ENV TESSDATA_PREFIX="/usr/app/counter/tessdata/"

RUN apk update && \
    apk upgrade && \
    apk add curl && \
    apk add --no-cache curl tesseract-ocr tesseract-ocr-dev gcc g++ make && \
    curl -LsSf https://astral.sh/uv/0.4.6/install.sh | sh && \
    uv sync && \
    adduser --disabled-password counter && \
    chown -R counter:counter /usr/app

USER counter

COPY . .

EXPOSE 8000

# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]