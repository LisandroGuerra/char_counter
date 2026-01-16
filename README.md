# Char Counter Service

Sistema de contagem de caracteres e OCR para documentos PDF e imagens, desenvolvido para análise volumétrica de documentos.

## Visão Geral

O sistema recebe arquivos (PDF ou Imagens), realiza OCR (Reconhecimento Óptico de Caracteres) para extrair o texto, aplica filtros de limpeza e retorna estatísticas de contagem (palavras, caracteres, páginas).

### Stack Tecnológica
* **Backend:** Django 5.1
* **OCR Engine:** Tesseract OCR 5
* **Manipulação de PDF:** `pdfplumber` (texto nativo) e `pdf2image`/`poppler` (imagens)
* **Metadados:** ExifTool
* **Containerização:** Docker + Alpine Linux

## Configuração do Ambiente

### 1. Variáveis de Ambiente (.env)
Crie um arquivo `.env` na raiz do projeto. Este arquivo não deve ser versionado.

```env
# Senha padrão para tentar abrir PDFs protegidos
PDF_DEFAULT_PASSWORD=SuaSenhaSeguraAqui

# Configurações do Django
DJANGO_DEBUG=True
DJANGO_SECRET_KEY=sua-chave-secreta-aqui