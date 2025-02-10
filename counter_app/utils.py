import subprocess
from PIL import Image, ImageEnhance, ImageOps, ImageFilter


def get_pdfinfo_as_dict(pdf_path):
    """
    Executa o comando `pdfinfo` em um arquivo PDF e retorna as informações como um dicionário.
    
    :param pdf_path: Caminho para o arquivo PDF.
    :return: Dicionário contendo as informações do PDF.
    """
    try:
        result = subprocess.run(
            ["pdfinfo", pdf_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode != 0:
            raise RuntimeError(f"Erro ao executar pdfinfo: {result.stderr.strip()}")

        # Processa a saída e converte para um dicionário
        pdf_info = {}
        for line in result.stdout.strip().split("\n"):
            if ":" in line:
                key, value = map(str.strip, line.split(":", 1))
                pdf_info[key] = value

        return pdf_info

    except FileNotFoundError:
        raise FileNotFoundError("O utilitário 'pdfinfo' não foi encontrado. Certifique-se de que está instalado.")
    except Exception as e:
        raise RuntimeError(f"Ocorreu um erro ao obter informações do PDF: {e}")


def get_pdf_fonts_and_encodings_as_dict(pdf_path):
    """
    Executa o comando `pdffonts` em um arquivo PDF e retorna as informações de fontes e encodings como um dicionário.
    
    :param pdf_path: Caminho para o arquivo PDF.
    :return: Dicionário com as fontes e seus encodings.
    """
    try:
        # Executa o comando `pdffonts`
        result = subprocess.run(
            ["pdffonts", pdf_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode != 0:
            raise RuntimeError(f"Erro ao executar pdffonts: {result.stderr.strip()}")

        # Processa a saída do pdffonts
        lines = result.stdout.strip().split("\n")[2:]  # Ignora as duas primeiras linhas (cabeçalhos)
        fonts_and_encodings = []

        for line in lines:
            font_name = line[:34].strip()  # Nome da fonte (colunas 1-34)
            encoding = line[52:66].strip()  # Encoding (colunas 53-66)
            fonts_and_encodings.append({"font_name": font_name, "encoding": encoding})

        return {"fonts": fonts_and_encodings}

    except FileNotFoundError:
        raise FileNotFoundError("O utilitário 'pdffonts' não foi encontrado. Certifique-se de que está instalado.")
    except Exception as e:
        raise RuntimeError(f"Ocorreu um erro ao obter informações das fontes: {e}")


def validate_pdf_fonts_and_encodings(fonts_info):
    """
    Verifica se há 'font_name = "[none]"' ou 'encoding = "Custom"' na saída de fontes.

    :param fonts_info: Dicionário retornado pela função get_fonts_and_encodings_as_dict.
    :return: False se houver algum font_name = "[none]" ou encoding = "Custom", True caso contrário.
    """
    for font in fonts_info.get("fonts", []):
        if font.get("font_name") == "[none]" or font.get("encoding") == "Custom":
            return False
    return True


def validate_pdf_creator_author_creator_tool(file_info):
    """
    Verifica se as chaves 'Creator', 'Author' e 'CreatorTool' estão presentes no arquivo PDF
    e seus valores são diferentes de:
    'creator_tool': 'PDF24 Creator',
    'creator': 'inss',
    'author': 'inss'

    :param file: Arquivo PDF.
    :return: True se as chaves forem diferentes destes valores, False caso contrário.
    """
    try:
        creator_tool = file_info.get("creator_tool", "").lower()
        creator = file_info.get("creator", "").lower()
        author = file_info.get("author", "").lower()

        return not (creator_tool == "pdf24 creator" and creator == "inss" and author == "inss")

    except Exception as e:
        raise RuntimeError(f"Erro ao validar informações do PDF: {e}")


def get_file_metadata_as_dict(file_path):
    """
    Executa o comando `exiftool` em um arquivo e retorna as informações como um dicionário.
    
    :param file_path: Caminho para o arquivo.
    :return: Dicionário contendo os metadados do arquivo.
    """
    try:
        result = subprocess.run(
            ["exiftool", file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode != 0:
            raise RuntimeError(f"Erro ao executar exiftool: {result.stderr.strip()}")

        # Processa a saída e converte para um dicionário
        metadata = {}
        for line in result.stdout.strip().split("\n"):
            if ": " in line:  # Garante que as linhas relevantes sejam processadas
                key, value = map(str.strip, line.split(": ", 1))
                key_map = str.maketrans({" ": "_", "/": "_", "-": "_"})
                key = key.translate(key_map).lower()
                metadata[key] = value

        return metadata

    except FileNotFoundError:
        raise FileNotFoundError("O utilitário 'exiftool' não foi encontrado. Certifique-se de que está instalado.")
    except Exception as e:
        raise RuntimeError(f"Ocorreu um erro ao obter metadados do arquivo: {e}")


def validate_pdf(file_path):
    """
    Valida um arquivo PDF verificando se as fontes e encodings são válidos e se as informações
    de 'Creator', 'Author' e 'CreatorTool' são diferentes de:
    'creator_tool': 'PDF24 Creator',
    'creator': 'inss',
    'author': 'inss'

    :param file_path: Caminho para o arquivo PDF.
    :return: True se o arquivo é válido, False caso contrário.
    """
    try:
        fonts_info = get_pdf_fonts_and_encodings_as_dict(file_path)
        file_info = get_file_metadata_as_dict(file_path)

        return validate_pdf_fonts_and_encodings(fonts_info) and validate_pdf_creator_author_creator_tool(file_info)

    except Exception as e:
        raise RuntimeError(f"Erro ao validar arquivo PDF: {e}")


def preprocess_image_hard(image_path):
    image = Image.open(image_path)
    # Converter para escala de cinza
    gray_image = ImageOps.grayscale(image)
    # Aplicar filtro de nitidez
    sharpened_image = gray_image.filter(ImageFilter.SHARPEN)
    # Binarizar a imagem
    threshold = 128
    binary_image = sharpened_image.point(lambda x: 255 if x > threshold else 0, mode='1')
    return binary_image


def preprocess_image_soft(image_path):
    image = Image.open(image_path).convert("L")
    enhanced_image = ImageEnhance.Contrast(
            image.resize((image.width * 3, image.height * 3), Image.Resampling.LANCZOS)
        ).enhance(2)
    return enhanced_image


# Exemplo de uso
if __name__ == "__main__":
    file_path = "base_testes/pmpgb.pdf"
    file_path = "base_testes/divinaaparecida_traducao_1.png"
    file_path = "base_testes/jacquelineveloso_Trad_Espanhol.pdf"
    # file_path = "base_testes/Traducao_ANTONIO_ALVAREZ_PAREDES.pdf"
    try:
        info = get_file_metadata_as_dict(file_path)
        print('#'*30, 'FILE_METADATA_INICIO', '#'*30)
        print(info)
        print('#'*30, 'FILE_METADATA_FIM', '#'*30)
        print()
    except Exception as e:
        print(e)

    try:    
        info = get_pdf_fonts_and_encodings_as_dict(file_path)
        print('#'*30, 'PDF_FONTS_INICIO', '#'*30)
        print(info)
        print('#'*30, 'PDF_FONTS_FIM', '#'*30)  
        print()
    except Exception as e:
        print(e)

    try:
        info = get_pdfinfo_as_dict(file_path)
        print('#'*30, 'PDF_INFO_INICIO', '#'*30)
        print(info)
        print('#'*30, 'PDF_INFO_FIM', '#'*30)
    except Exception as e:        
        print(e)
