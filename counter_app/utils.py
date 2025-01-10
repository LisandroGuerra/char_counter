import subprocess


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


def get_pdf_fonts_and_encodings_as_dict(pdf_path, *args, **kwargs):
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

# Exemplo de uso
if __name__ == "__main__":
    file_path = "base_testes/pmpgb.pdf"
    file_path = "base_testes/divinaaparecida_traducao_1.png"
    file_path = "base_testes/jacquelineveloso_Trad_Espanhol.pdf"
    try:
        info = get_file_metadata_as_dict(file_path)
        print(info)
    except Exception as e:
        print(e)
