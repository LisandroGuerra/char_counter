FROM python:3.12.4-alpine3.20
# FROM python:3.11.10-alpine3.20 # OpenCV

    ENV PYTHONUNBUFFERED 1
    ENV PYTHONDONTWRITEBYTECODE 1
    ENV PATH="/root/.cargo/bin:${PATH}"
    ENV PATH="/usr/app/counter:${PATH}"
    ENV TESSDATA_PREFIX="/usr/app/counter/tessdata/"

WORKDIR /usr/app

COPY uv.lock .
COPY pyproject.toml .


RUN apk update && \
    apk upgrade && \
    apk add curl && \
    apk add poppler-utils && \
    apk add --no-cache tesseract-ocr tesseract-ocr-dev gcc g++ make && \
    curl -LsSf https://astral.sh/uv/0.4.6/install.sh | sh && \
    uv sync && \
    adduser --disabled-password counter && \
    chown -R counter:counter /usr/app

# RUN apk update && \
#     apk upgrade && \
#     apk add --no-cache \
#         build-base \
#         py3-setuptools \
#         py3-pip \
#         py3-wheel \
#         python3-dev \
#         py3-numpy \
#         jpeg-dev \
#         zlib-dev \
#         libpng-dev \
#         freetype-dev \
#         openblas-dev \
#         linux-headers \
#         tesseract-ocr \
#         tesseract-ocr-dev \
#         curl \
#         gcc \
#         g++ \
#         make && \
#     curl -LsSf https://astral.sh/uv/0.4.6/install.sh | sh && \
#     uv sync && \
#     adduser --disabled-password counter && \
#     chown -R counter:counter /usr/app

USER counter

COPY . .

# EXPOSE 8000

# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]