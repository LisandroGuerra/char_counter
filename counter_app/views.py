from django.shortcuts import render
import pdfplumber


def counter(request):
    if request.method == 'GET':
        return render(request, 'index.html')
    elif request.method == 'POST':
        file = request.FILES['arquivo']
        try:
            with pdfplumber.open(file) as pdf:
                texto_completo = ""
                # Itera por cada página do PDF
                for pagina in pdf.pages:
                    texto = pagina.extract_text()
                    if texto:
                        texto_completo += texto
                # Conta o número de caracteres
                num_caracteres = len(texto_completo)
                result = len(texto_completo.replace(" ", ""))
                error = False
                message = ""
        except:
            result = 0
            error = True
            message = "Erro. Verifique se o arquivo é um PDF."
        
        return render(request, 'index.html', {'file': file, 'result': result, 'error': error, 'message': message})

