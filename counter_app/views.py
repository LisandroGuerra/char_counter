import os
import logging
import re
import tempfile
from functools import partial

import pdfplumber
import pytesseract
from pytesseract import Output
from pdf2image import convert_from_path
from pdf2image.exceptions import PDFPageCountError
from pdfminer.pdfdocument import PDFPasswordIncorrect
from django.shortcuts import render
from django.conf import settings

# Configuração de Logging
logger = logging.getLogger(__name__)

def clean_text(text):
    """Aplica regex para limpar linhas indesejadas do texto extraído."""
    if not text:
        return ""
    
    cleaned_lines = []
    patterns = getattr(settings, 'OCR_IGNORE_PATTERNS', [])
    
    for line in text.splitlines():
        if any(re.search(pattern, line, re.IGNORECASE) for pattern in patterns):
            continue
        cleaned_lines.append(line)
    
    return "\n".join(cleaned_lines)

def handle_uploaded_file(file, callback):
    """Grava o arquivo enviado em um temporário e executa o callback."""
    try:
        suffix = os.path.splitext(file.name)[1].lower()
        if not suffix: suffix = ".tmp"
            
        with tempfile.NamedTemporaryFile(delete=True, suffix=suffix) as temp_file:
            for chunk in file.chunks():
                temp_file.write(chunk)
            temp_file.flush()
            return callback(temp_file.name)
    except Exception as e:
        raise e

def process_image_ocr(file_path, lang="eng"):
    """
    Realiza OCR em uma imagem única.
    """
    try:
        text_bytes = pytesseract.image_to_string(file_path, lang=lang, output_type=Output.BYTES)
        text = text_bytes.decode('utf-8', errors='ignore')
        
        lines = [line for line in text.splitlines() if line.strip()]
        text_cleaned = "\n".join(lines)
        qt_words = len(text_cleaned.split())
        return text_cleaned, qt_words
    except Exception as e:
        logger.warning(f"Falha no OCR da imagem {file_path}: {e}")
        return "", 0

def process_pdf(file_path, lang, password=None):
    """Processa PDF com senha dinâmica."""
    text_extracted = ""
    qt_pages, qt_images, qt_words = 0, 0, 0

    try:
        with pdfplumber.open(file_path, password=password) as pdf:
            qt_pages = len(pdf.pages)
            for page in pdf.pages:
                words = page.extract_words()
                qt_words += len(words)
                
                # --- Lógica Original de Espelhamento ---
                page_text = " ".join(
                    word["text"][::-1] if not word["upright"] else word["text"]
                    for word in words
                )
                text_extracted += page_text + "\n"

                # OCR em imagens internas (mantido, mas secundário)
                for image in page.images:
                    try:
                        with tempfile.NamedTemporaryFile(delete=True, suffix=".jpg") as temp_img:
                            temp_img.write(image["stream"].get_rawdata())
                            temp_img.flush()
                            img_text, img_words = process_image_ocr(temp_img.name, lang)
                            if img_text:
                                text_extracted += "\n" + img_text
                                qt_words += img_words
                                qt_images += 1
                    except Exception as e:
                        pass # Ignora erros pontuais em imagens internas

    except PDFPasswordIncorrect:
        raise PDFPasswordIncorrect("Senha incorreta.")
    except Exception as e:
        logger.warning(f"Erro genérico no process_pdf: {e}")
        raise e

    return text_extracted, qt_pages, qt_images, qt_words

def extract_text_from_pdf_images_fallback(pdf_path, lang, password=None):
    """Fallback com senha dinâmica."""
    report = []
    
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            images = convert_from_path(
                pdf_path, 
                output_folder=temp_dir, 
                fmt="JPEG",
                userpw=password 
            )
        except PDFPageCountError as e:
            logger.error(f"Erro de senha ou arquivo corrompido no fallback: {e}")
            raise ValueError("Senha incorreta ou PDF protegido.")
        except Exception as e:
            logger.error(f"Erro crítico no fallback pdf2image: {e}")
            raise ValueError("Não foi possível converter o PDF.")

        for i, image in enumerate(images):
            image_file = os.path.join(temp_dir, f"page_{i + 1}.jpg")
            image.save(image_file, "JPEG")
            text, qt_words = process_image_ocr(image_file, lang)
            report.append({"page": i + 1, "text": text, "word_count": qt_words})

    text_extracted = "\n".join(page['text'] for page in report)
    qt_pages = len(report)
    qt_words = sum(page["word_count"] for page in report)
    # No fallback, consideramos qt_images = qt_pages pois cada página virou uma imagem
    return text_extracted, qt_pages, qt_pages, qt_words

def counter(request):
    """View principal."""
    languages_list = [
        {"id": "deu", "name": "Alemão"}, {"id": "kor", "name": "Coreano"},
        {"id": "spa", "name": "Espanhol"}, {"id": "fra", "name": "Francês"},
        {"id": "hin", "name": "Hindi"}, {"id": "eng", "name": "Inglês"},
        {"id": "ita", "name": "Italiano"}, {"id": "jpn", "name": "Japonês"},
        {"id": "por", "name": "Português"}
    ]

    if request.method == "GET":
        return render(request, "index.html", {"languages_list": languages_list})

    file = request.FILES.get("uploaded_file")
    password = request.POST.get("password") or None
    
    if not file:
        return render(request, "index.html", {"languages_list": languages_list, "error": True, "message": "Nenhum arquivo enviado."})

    lang_input = request.POST.getlist("languages")
    lang = "+".join(lang_input) if lang_input else "por+eng"
    selected_languages = [l["name"] for l in languages_list if l["id"] in lang]
    file_name = file.name[:40] + "..." if len(file.name) > 40 else file.name
    
    error, message = False, ""
    text_extracted = ""
    qt_pages = qt_images = qt_words = qt_char_extracted = qt_char_cleaned = 0

    try:
        if file.name.lower().endswith(".pdf"):
            try:
                callback_standard = partial(process_pdf, lang=lang, password=password)
                text_extracted, qt_pages, qt_images, qt_words = handle_uploaded_file(file, callback_standard)
                
                # === NOVA VALIDAÇÃO DE QUALIDADE ===
                # 1. Poucas palavras
                if qt_words < 5 and qt_pages > 0:
                    raise ValueError("Texto insuficiente.")
                
                # 2. Detecção de CID (Encoding Corrompido)
                if "(cid:" in text_extracted:
                    logger.warning("PDF com encoding corrompido (CID) detectado. Forçando OCR visual.")
                    raise ValueError("Encoding corrompido (CID).")
                    
            except PDFPasswordIncorrect:
                error = True
                message = "O arquivo é protegido por senha. Por favor, digite a senha correta no campo 'Senha do PDF'."
                return render(request, "index.html", {"file_name": file_name, "languages_list": languages_list, "selected_languages": selected_languages, "error": error, "message": message})

            except Exception as e:
                logger.warning(f"Tentativa padrão falhou ou foi rejeitada ({e}). Iniciando Fallback (OCR Visual)...")
                try:
                    callback_fallback = partial(extract_text_from_pdf_images_fallback, lang=lang, password=password)
                    text_extracted, qt_pages, qt_images, qt_words = handle_uploaded_file(file, callback_fallback)
                except ValueError as ve:
                    if "Senha incorreta" in str(ve):
                        error = True
                        message = "O arquivo é protegido e a senha informada está incorreta ou vazia."
                    else:
                        raise ve

        elif file.name.lower().endswith(("jpg", "jpeg", "png", "bmp", "gif", "tiff")):
            callback_img = partial(process_image_ocr, lang=lang)
            text_extracted, qt_words = handle_uploaded_file(file, callback_img)
            qt_images = 1
            qt_pages = 1
        else:
            raise ValueError("Tipo de arquivo não suportado.")

        if not error:
            text_extracted = clean_text(text_extracted)
            if not text_extracted.strip():
                message = "Alerta: Nenhum texto legível foi identificado."

            text_cleaned_stats = text_extracted.replace("\n", "").replace("\r", "").replace("\t", "").replace(" ", "")
            qt_char_extracted = len(text_extracted)
            qt_char_cleaned = len(text_cleaned_stats)

    except Exception as e:
        error = True
        message = f"Erro no processamento: {str(e)}"
        logger.exception("Erro crítico na view counter")

    return render(
        request,
        "index.html",
        {
            "file_name": file_name,
            "languages_list": languages_list,
            "selected_languages": selected_languages,
            "error": error,
            "message": message,
            "qt_pages": qt_pages,
            "qt_images": qt_images,
            "qt_words": qt_words,
            "qt_char_extracted": qt_char_extracted,
            "qt_char_cleaned": qt_char_cleaned,
            "text_extracted": text_extracted.strip(),
        },
    )