FROM python:3.12.4-alpine3.20

    ENV PYTHONUNBUFFERED 1
    ENV PYTHONDONTWRITEBYTECODE 1

WORKDIR /usr/app/counter

COPY uv.lock .
COPY pyproject.toml .

ENV PATH="/root/.cargo/bin:${PATH}"
ENV PATH="/usr/app/counter:${PATH}"

RUN apk update && \
    apk upgrade && \
    apk add curl && \
    curl -LsSf https://astral.sh/uv/0.4.6/install.sh | sh && \
    uv sync && \
    adduser --disabled-password counter && \
    chown -R counter:counter /usr/app/counter

USER counter

COPY . .

EXPOSE 8000
