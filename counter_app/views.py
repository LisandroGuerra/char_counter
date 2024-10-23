from django.shortcuts import render
import pdfplumber
from PIL import Image, ImageEnhance
import pytesseract


def process_pdf(file):
    texto_extraido_pdf = ""
    with pdfplumber.open(file) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if texto:
                texto_extraido_pdf += texto

    return texto_extraido_pdf


def process_image(file):
    # Abre a imagem e extrai o texto com pytesseract
    image = Image.open(file).convert('L')
    resized_image = image.resize((image.width * 3, image.height * 3), Image.Resampling.LANCZOS)
    enhanced_image = ImageEnhance.Contrast(resized_image).enhance(2)
    texto_extraido_image = pytesseract.image_to_string(enhanced_image)
    return texto_extraido_image


def counter(request):
    if request.method == 'GET':
        return render(request, 'index.html')
    elif request.method == 'POST':
        file = request.FILES['arquivo']
        error = False
        message = ""
        texto_completo = ""
        res0 = res1 = res2 = 0
        try:
            if file.name.lower().endswith(('.pdf')):
                # Processa arquivo PDF
                texto_completo = process_pdf(file)
            elif file.name.lower().endswith(('.jpg', '.jpeg', '.png')):
                # Processa arquivo de imagem
                texto_completo = process_image(file)
            else:
                raise ValueError("Tipo de arquivo não suportado.")

            if not texto_completo:
                if file.name.lower().endswith(('.pdf')):
                    raise ValueError("Erro ao extrair texto do PDF.")
                elif file.name.lower().endswith(('.jpg', '.jpeg', '.png')):
                    raise ValueError("Erro ao extrair texto da imagem.")
                else:
                    raise ValueError("Erro ao extrair texto.")
            # Limpa o texto
            res1 = texto_completo.replace(" ", "")
            res2 = res1.replace("\n", "")
            res0 = len(texto_completo)
            res1 = len(res1)
            res2 = len(res2)
            

            texto_completo_limpo = (
                texto_completo.replace("\n", "")
                              .replace("\r", "")
                              .replace("\t", "")
                              .replace(" ", "")
            )
            
            # Conta o número de caracteres
            result = len(texto_completo_limpo)
        except Exception as e:
            result = 0
            error = True
            message = f"Erro: {str(e)}"
        
        return render(request, 'index.html', {
            'file': file, 
            'result': result, 
            'error': error, 
            'message': message, 
            'res0': res0, 
            'res1': res1,
            'res2': res2,
            'texto_extraido': texto_completo.strip().strip("\n")})







# APENAS PDF - FUNCIONANDO
# def counter(request):
#     if request.method == 'GET':
#         return render(request, 'index.html')
#     elif request.method == 'POST':
#         file = request.FILES['arquivo']
#         try:
#             with pdfplumber.open(file) as pdf:
#                 texto_completo = ""
#                 # Itera por cada página do PDF
#                 for pagina in pdf.pages:
#                     texto = pagina.extract_text()
#                     if texto:
#                         texto_completo += texto
#                 # Conta o número de caracteres
#                 print(texto_completo)
#                 num_caracteres = len(texto_completo)
#                 # Limpa o texto
#                 texto_completo_limpo = texto_completo.replace("\n", "").replace("\r", "").replace("\t", "").replace(" ", "")
#                 result = len(texto_completo_limpo)
#                 error = False
#                 message = ""
#         except:
#             result = 0
#             error = True
#             message = "Erro. Verifique se o arquivo é um PDF."
        
#         return render(request, 'index.html', {'file': file, 'result': result, 'error': error, 'message': message})

