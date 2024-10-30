from django.shortcuts import render
import pdfplumber
from PIL import Image, ImageEnhance
import pytesseract
import os


def process_pdf(file, lang):
    '''
    Receives a file and a language code and returns the text extracted from the PDF, number of pages, number of words and number of images with text.
    Languages supported by Tesseract OCR: https://tesseract-ocr.github.io/tessdoc/Data-Files-in-different-versions.html
    Can use multiple languages separated by '+', e.g. 'eng+por'.
    '''
    text_extracted = ''
    image_path = 'image.jpg'
    qt_pages, qt_images, qt_words = 0, 0, 0
    
    with pdfplumber.open(file) as pdf:
        qt_pages = len(pdf.pages)
        for page in pdf.pages:
            words = page.extract_words()
            qt_words += len(words)
            for word in words:
                text = word['text']
                is_vertical = not word['upright']  # Detects if the text is vertical
                processed_text = text[::-1] if is_vertical else text  # Reverses the text if it is vertical
                text_extracted += processed_text + " "

            for image in page.images:
                try:
                    # Save the image to a temporary file
                    with open(image_path, 'wb') as f:
                        f.write(image['stream'].get_rawdata())
                    
                    # Try to extract text from the image
                    text, qt_words_img = process_image(image_path, lang)
                    if text:
                        text_extracted += text  
                        qt_words += qt_words_img                      
                        qt_images += 1

                except Exception as e:
                    print(f"Erro processando imagem de PDF: {e}")

                finally:
                    # Remove the temporary image if it exists
                    if os.path.exists(image_path):
                        os.remove(image_path)
                
    return text_extracted, qt_pages, qt_images, qt_words


def process_image(file_path, lang='eng'):
    '''
    Receives a file path and a language code and returns the text extracted from the image.
    Languages supported by Tesseract OCR: https://tesseract-ocr.github.io/tessdoc/Data-Files-in-different-versions.html
    Can use multiple languages separated by '+', e.g. 'eng+por'.
    '''
    try:
        # Opens an image treat it and extracts text with pytesseract
        qt_words = 0
        image = Image.open(file_path).convert('L')
        resized_image = image.resize((image.width * 3, image.height * 3), Image.Resampling.LANCZOS)
        enhanced_image = ImageEnhance.Contrast(resized_image).enhance(2)
        text_extracted = pytesseract.image_to_string(enhanced_image, lang=lang)
        qt_words += len(text_extracted.split())
        return text_extracted, qt_words

    except Exception as e:
        raise ValueError(f"Erro extraindo texto da imagem: {e}")


def counter(request):
    '''
    Receives a file and a list of languages and returns the extracted text, number of pages, number of images with text, number of words and number of characters.
    '''
    languages_list = [
        {'id': 'deu', 'name': 'Alemão'},
        {'id': 'kor', 'name': 'Coreano'},
        {'id': 'spa', 'name': 'Espanhol'},
        {'id': 'fra', 'name': 'Francês'},
        {'id': 'hin', 'name': 'Hindi'},
        {'id': 'eng', 'name': 'Inglês'},
        {'id': 'ita', 'name': 'Italiano'},
        {'id': 'jpn', 'name': 'Japonês'},
        {'id': 'por', 'name': 'Português'}
    ]

    if request.method == 'GET':
        return render(request, 'index.html', {'languages_list': languages_list})
    elif request.method == 'POST':
        file_languages = request.POST.getlist('languages')
        lang = '+'.join(file_languages)
        selected_languages = [language['name'] for language in languages_list if language['id'] in file_languages]
        file = request.FILES['uploaded_file']
        file_name = str(file)[0:40] + '...' if len(str(file)) > 40 else str(file)
        error = False
        message, text_extracted, text_cleaned = '', '', ''
        qt_char_extracted, qt_char_cleaned, qt_pages, qt_images, qt_words = 0, 0, 0, 0, 0
        try:
            if file.name.lower().endswith(('.pdf')):
                # PDF file processing
                text_extracted, qt_pages, qt_images, qt_words = process_pdf(file, lang)
            elif file.name.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff')):
                # Image file processing
                text_extracted, qt_words = process_image(file, lang)
                qt_images += 1
                qt_pages += 1
            else:
                raise ValueError("Tipo de arquivo não suportado.")

            if not text_extracted:
                if file.name.lower().endswith(('.pdf')):
                    raise ValueError("Erro ao extrair texto do PDF.")
                elif file.name.lower().endswith(('.jpg', '.jpeg', '.png')):
                    raise ValueError("Erro ao extrair texto da imagem.")
                else:
                    raise ValueError("Erro ao extrair texto.")
            # Clean the extracted text
            text_cleaned = (
                text_extracted.replace("\n", "")
                              .replace("\r", "")
                              .replace("\t", "")
                              .replace(" ", "")
            )
            # Count the number of characters in the extracted and cleaned text
            qt_char_extracted = len(text_extracted)
            qt_char_cleaned = len(text_cleaned)

        except Exception as e:
            error = True
            message = f"Erro: {str(e)}"
        
        return render(request, 'index.html', {
            'file_name': file_name,
            'languages_list': languages_list,
            'selected_languages': selected_languages, 
            'error': error, 
            'message': message,
            'qt_pages': qt_pages,
            'qt_images': qt_images,
            'qt_words': qt_words, 
            'qt_char_extracted': qt_char_extracted,
            'qt_char_cleaned': qt_char_cleaned,
            'text_extracted': text_extracted.strip().strip("\n")})
