import subprocess
import logging
from PIL import Image, ImageEnhance, ImageOps, ImageFilter

# Configuração de Logs
logger = logging.getLogger(__name__)

def get_pdfinfo_as_dict(pdf_path):
    """
    Executa o comando `pdfinfo` (Poppler) em um arquivo PDF.
    Útil para debug de metadados básicos.
    """
    try:
        result = subprocess.run(
            ["pdfinfo", pdf_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode != 0:
            logger.warning(f"pdfinfo retornou erro para {pdf_path}: {result.stderr.strip()}")
            return {}

        pdf_info = {}
        for line in result.stdout.strip().split("\n"):
            if ":" in line:
                key, value = map(str.strip, line.split(":", 1))
                pdf_info[key] = value

        return pdf_info

    except FileNotFoundError:
        logger.error("Ferramenta 'pdfinfo' não encontrada no sistema.")
        return {}
    except Exception as e:
        logger.error(f"Erro ao obter informações do PDF: {e}")
        return {}


def get_pdf_fonts_and_encodings_as_dict(pdf_path):
    """
    Executa `pdffonts`. Usado pela validação legada para detectar fontes corrompidas.
    """
    try:
        result = subprocess.run(
            ["pdffonts", pdf_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode != 0:
            # Em arquivos protegidos por senha, pdffonts pode falhar se não passar a senha.
            # Como este é um utilitário de validação, apenas logamos.
            logger.warning(f"pdffonts falhou: {result.stderr.strip()}")
            return {"fonts": []}

        lines = result.stdout.strip().split("\n")[2:]
        fonts_and_encodings = []

        for line in lines:
            # Layout fixo do pdffonts (atenção a mudanças de versão do poppler)
            if len(line) > 65:
                font_name = line[:34].strip()
                encoding = line[52:66].strip()
                fonts_and_encodings.append({"font_name": font_name, "encoding": encoding})

        return {"fonts": fonts_and_encodings}

    except Exception as e:
        logger.error(f"Erro no pdffonts: {e}")
        return {"fonts": []}


def get_file_metadata_as_dict(file_path):
    """
    Wrapper para o ExifTool. Extrai metadados detalhados.
    """
    try:
        result = subprocess.run(
            ["exiftool", file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode != 0:
            logger.warning(f"exiftool falhou: {result.stderr.strip()}")
            return {}

        metadata = {}
        for line in result.stdout.strip().split("\n"):
            if ": " in line:
                key, value = map(str.strip, line.split(": ", 1))
                # Normalização de chaves para snake_case
                key_map = str.maketrans({" ": "_", "/": "_", "-": "_"})
                key = key.translate(key_map).lower()
                metadata[key] = value

        return metadata

    except FileNotFoundError:
        logger.error("Ferramenta 'exiftool' não encontrada.")
        return {}
    except Exception as e:
        logger.error(f"Erro no exiftool: {e}")
        return {}


# -------------------------------------------------------------------------
# FUNÇÕES DE VALIDAÇÃO (LEGADO / REGRA DE NEGÓCIO ESPECÍFICA)
# Mantidas conforme solicitação para possível reativação futura.
# -------------------------------------------------------------------------

def validate_pdf_fonts_and_encodings(fonts_info):
    """
    [LEGADO] Verifica se há fontes quebradas ou encodings customizados suspeitos.
    """
    for font in fonts_info.get("fonts", []):
        if font.get("font_name") == "[none]" or font.get("encoding") == "Custom":
            return False
    return True


def validate_pdf_creator_author_creator_tool(file_info):
    """
    [LEGADO] Regra de negócio restritiva.
    Rejeita documentos criados por 'PDF24 Creator' com autor 'INSS'.
    """
    try:
        creator_tool = file_info.get("creator_tool", "").lower()
        creator = file_info.get("creator", "").lower()
        author = file_info.get("author", "").lower()

        # Lógica de bloqueio específica
        if creator_tool == "pdf24 creator" and creator == "inss" and author == "inss":
            logger.info("PDF rejeitado pela regra de validação de metadados (PDF24/INSS).")
            return False
        return True

    except Exception as e:
        logger.error(f"Erro na validação de metadados: {e}")
        return False


def validate_pdf(file_path):
    """
    [LEGADO] Validador mestre. Combina validação de fonte e metadados.
    Atualmente não utilizado no fluxo principal (views.py), mas disponível.
    """
    try:
        fonts_info = get_pdf_fonts_and_encodings_as_dict(file_path)
        file_info = get_file_metadata_as_dict(file_path)

        fonts_ok = validate_pdf_fonts_and_encodings(fonts_info)
        meta_ok = validate_pdf_creator_author_creator_tool(file_info)

        return fonts_ok and meta_ok

    except Exception as e:
        logger.error(f"Erro geral na validação do PDF: {e}")
        return False


# -------------------------------------------------------------------------
# PROCESSAMENTO DE IMAGEM (SUPORTE AO OCR)
# -------------------------------------------------------------------------

def preprocess_image_hard(image_path):
    """
    Aplica filtros agressivos para melhorar OCR em documentos ruidosos.
    Retorna um objeto PIL Image pronto para ser consumido pelo pytesseract.
    """
    try:
        image = Image.open(image_path)
        
        # 1. Escala de Cinza
        gray_image = ImageOps.grayscale(image)
        
        # 2. Sharpen (Nitidez)
        sharpened_image = gray_image.filter(ImageFilter.SHARPEN)
        
        # 3. Binarização (Threshold)
        # Transforma pixels cinzas em preto ou branco absoluto
        threshold = 128
        binary_image = sharpened_image.point(lambda x: 255 if x > threshold else 0, mode='1')
        
        return binary_image
    except Exception as e:
        logger.error(f"Erro no preprocess_image_hard: {e}")
        # Retorna a imagem original em caso de erro para não quebrar o fluxo
        return Image.open(image_path)


def preprocess_image_soft(image_path):
    """
    Aplica melhoria de contraste suave.
    Útil para documentos escaneados com texto muito claro/apagado.
    """
    try:
        image = Image.open(image_path).convert("L")
        
        # Aumenta resolução (upscaling) para ajudar o OCR em letras pequenas
        resized_image = image.resize(
            (image.width * 2, image.height * 2), 
            Image.Resampling.LANCZOS
        )
        
        # Aumenta o contraste
        enhanced_image = ImageEnhance.Contrast(resized_image).enhance(2.0)
        
        return enhanced_image
    except Exception as e:
        logger.error(f"Erro no preprocess_image_soft: {e}")
        return Image.open(image_path)