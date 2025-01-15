# Base image
FROM python:3.12.4-alpine3.20

# Configurações de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/root/.cargo/bin:/usr/app/counter:${PATH}" \
    TESSDATA_PREFIX="/usr/app/counter/tessdata/"

# Diretório de trabalho
WORKDIR /usr/app

# Copiar arquivos necessários para o build
COPY pyproject.toml .

# Instalar dependências do sistema e ferramentas adicionais
RUN apk update && apk upgrade && \
    apk add --no-cache \
        curl \
        poppler-utils \
        tesseract-ocr \
        tesseract-ocr-dev \
        gcc \
        g++ \
        make \
        perl \
        perl-utils && \
    apk add --no-cache --virtual .build-deps \
        perl-dev && \
    curl -LO https://exiftool.org/Image-ExifTool-13.12.tar.gz && \
    tar -xzf Image-ExifTool-13.12.tar.gz && \
    cd Image-ExifTool-13.12 && \
    perl Makefile.PL && \
    make install && \
    cd .. && \
    rm -rf Image-ExifTool-13.12* && \
    curl -LsSf https://astral.sh/uv/0.4.6/install.sh | sh && \
    uv sync && \
    apk del .build-deps && \
    adduser --disabled-password --home /usr/app counter && \
    chown -R counter:counter /usr/app

# Alternar para usuário não privilegiado
USER counter

# Copiar todo o código para o contêiner
COPY . .

# Expor a porta necessária (caso seja relevante para o seu app)
# EXPOSE 8000

# Comando padrão (se necessário)
# CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
