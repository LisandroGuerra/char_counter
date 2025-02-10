import os
import tempfile
from functools import partial

import pdfplumber
import pytesseract

from pdf2image import convert_from_path
from django.shortcuts import render

from .utils import (get_pdf_fonts_and_encodings_as_dict, 
                    get_file_metadata_as_dict,
                    validate_pdf_fonts_and_encodings, 
                    validate_pdf_creator_author_creator_tool,
                    validate_pdf,
                    preprocess_image_hard,
                    preprocess_image_soft
                    )


def handle_uploaded_file(file, callback):
    """Grava o arquivo enviado em um temporário e executa o callback."""
    with tempfile.NamedTemporaryFile(delete=True, suffix=".pdf") as temp_file:
        for chunk in file.chunks():
            temp_file.write(chunk)
        temp_file.flush()
        return callback(temp_file.name)


def process_pdf(file, lang):
    """Processa um arquivo PDF para extrair texto e contar palavras, imagens e páginas."""
    text_extracted = ""
    qt_pages, qt_images, qt_words = 0, 0, 0

    with pdfplumber.open(file) as pdf:
        qt_pages = len(pdf.pages)
        for page in pdf.pages:
            words = page.extract_words()
            qt_words += len(words)
            text_extracted += " ".join(
                word["text"][::-1] if not word["upright"] else word["text"]
                for word in words
            ) + " "

            for image in page.images:
                try:
                    with tempfile.NamedTemporaryFile(delete=True, suffix=".jpg") as temp_img:
                        temp_img.write(image["stream"].get_rawdata())
                        temp_img.flush()
                        text, img_words = process_image(temp_img.name, lang)
                        if text:
                            text_extracted += text
                            qt_words += img_words
                            qt_images += 1
                except Exception as e:
                    print(f"Erro processando imagem de PDF: {e}")

    return text_extracted, qt_pages, qt_images, qt_words


def process_image(file_path, lang="eng"):
    """Processa uma imagem para extrair texto e contar palavras."""
    remove_target_lines = False
    word_length = 4
    
    try:
        processed_image = preprocess_image_hard(file_path)
        text_extracted = pytesseract.image_to_string(processed_image, lang=lang)

        # Remove linhas com caracteres não alfanuméricos excessivos
        lines = text_extracted.splitlines()
        cleaned_lines = []
        for line in lines:
            non_alpha_count = sum(1 for char in line if not char.isalpha())
            alpha_count = sum(1 for char in line if char.isalpha())
            if alpha_count >= non_alpha_count:
                cleaned_lines.append(line)
        text_extracted = "\n".join(cleaned_lines) 

        #Remove linhas que tem apenas palavras com menos caracteres que definido em word_length
        lines = text_extracted.splitlines()
        cleaned_lines = []
        for line in lines:
        # Ignorar linhas vazias ou com apenas espaços em branco
            if line.strip():
                words = line.split()
                # Verificar se todas as palavras têm menos de N caracteres
                if any(len(word) >= word_length for word in words):
                    cleaned_lines.append(line)     
        text_extracted = "\n".join(cleaned_lines)


        # Remove target lines from the end of the text if they contain key words
        if remove_target_lines:
            key_words = ["assinado", "assinatura", "assinaturas"]
            target_lines = 2
            lines = [line.strip() for line in text_extracted.split("\n") if line.strip()]
            def contains_key_words(line, words):
                return any(word in line.lower() for word in words)
            if len(lines) >= target_lines and all(contains_key_words(line, key_words) for line in lines[-target_lines:]):
                lines = lines[:-target_lines]
            text_extracted = "\n".join(lines)


        qt_words = len(text_extracted.split())

        return text_extracted, qt_words
    except Exception as e:
        raise ValueError(f"Erro extraindo texto da imagem: {e}")


def extract_text_from_pdf_images(pdf_path, lang):
    """Extrai texto das imagens geradas a partir de um PDF."""
    report = []
    with tempfile.TemporaryDirectory() as temp_dir:
        images = convert_from_path(pdf_path, output_folder=temp_dir, fmt="JPEG")
        for i, image in enumerate(images):
            image_file = os.path.join(temp_dir, f"page_{i + 1}.jpg")
            image.save(image_file, "JPEG")
            text, qt_words = process_image(image_file, lang)
            report.append({"page": i + 1, "text": text, "word_count": qt_words})

    text_extracted = "\n".join(f"{page['text']}" for page in report)
    qt_pages = len(report)
    qt_words = sum(page["word_count"] for page in report)
    return text_extracted, qt_pages, qt_pages, qt_words


def counter(request):
    """
    Recebe um arquivo e uma lista de idiomas e retorna texto extraído,
    número de páginas, imagens com texto, palavras e caracteres.
    """
    languages_list = [
        {"id": "deu", "name": "Alemão"}, {"id": "kor", "name": "Coreano"},
        {"id": "spa", "name": "Espanhol"}, {"id": "fra", "name": "Francês"},
        {"id": "hin", "name": "Hindi"}, {"id": "eng", "name": "Inglês"},
        {"id": "ita", "name": "Italiano"}, {"id": "jpn", "name": "Japonês"},
        {"id": "por", "name": "Português"}
    ]

    if request.method == "GET":
        return render(request, "index.html", {"languages_list": languages_list})

    file = request.FILES["uploaded_file"]
    lang = "+".join(request.POST.getlist("languages"))
    selected_languages = [
        language["name"] for language in languages_list if language["id"] in lang
    ]
    file_name = file.name[:40] + "..." if len(file.name) > 40 else file.name
    error, message = False, ""
    text_extracted, text_cleaned = "", ""
    qt_pages = qt_images = qt_words = qt_char_extracted = qt_char_cleaned = 0

    try:
        if file.name.lower().endswith(".pdf"):
            pdf_is_valid = handle_uploaded_file(file, validate_pdf)
            # fonts_and_encodings = handle_uploaded_file(file, get_pdf_fonts_and_encodings_as_dict)
            # creators_authors_info = handle_uploaded_file(file, get_file_metadata_as_dict)
            # if validate_pdf_fonts_and_encodings(fonts_and_encodings) and validate_pdf_creator_author_creator_tool(creators_authors_info):
            if pdf_is_valid:
                text_extracted, qt_pages, qt_images, qt_words = process_pdf(file, lang)
            else:
                callback = partial(extract_text_from_pdf_images, lang=lang)
                text_extracted, qt_pages, qt_images, qt_words = handle_uploaded_file(file, callback)
        elif file.name.lower().endswith(("jpg", "jpeg", "png", "bmp", "gif", "tiff")):
            text_extracted, qt_words = process_image(file, lang)
            qt_images += 1
            qt_pages += 1
        else:
            raise ValueError("Tipo de arquivo não suportado.")

        if not text_extracted:
            raise ValueError("Erro ao extrair texto.")

        text_cleaned = text_extracted.replace("\n", "").replace("\r", "").replace("\t", "").replace(" ", "")
        qt_char_extracted = len(text_extracted)
        qt_char_cleaned = len(text_cleaned)

    except Exception as e:
        error = True
        message = f"Erro: {e}"

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
