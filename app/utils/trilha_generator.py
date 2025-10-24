import base64
from PIL import Image, ImageDraw, ImageFont
import io
import requests
import traceback # Para logs de erro detalhados
import os # Para caminhos de ficheiros
import gc # Garbage Collector (Coletor de Lixo)

# --- Função de Fonte (sem alterações, continua a guardar em /tmp) ---
def get_font_robust(font_filename, font_url, size):
    """Tenta carregar a fonte do sistema. Se falhar, faz o download."""
    local_font_path = f"/tmp/{font_filename}" # Usar um diretório temporário
    
    try:
        # 1. Tenta usar a fonte se já foi descarregada
        if os.path.exists(local_font_path):
            return ImageFont.truetype(local_font_path, size)
            
        # 2. Se não existe, tenta descarregar
        print(f"INFO: A descarregar fonte de {font_url}...")
        r = requests.get(font_url, allow_redirects=True, timeout=10) # Adiciona timeout
        r.raise_for_status() # Verifica se o download falhou
        
        font_data = io.BytesIO(r.content)
        
        # 3. Salva a fonte no /tmp para uso futuro
        with open(local_font_path, "wb") as f:
            f.write(font_data.getbuffer())
            
        # 4. Retorna a fonte a partir dos dados em memória
        font_data.seek(0) # Rebobina o buffer
        return ImageFont.truetype(font_data, size)
        
    except Exception as e:
        print(f"!!!!!! ERRO CRÍTICO AO CARREGAR FONTE: {e} !!!!!!")
        print("!!!!!! A USAR ImageFont.load_default() COMO ÚLTIMA OPÇÃO !!!!!!")
        try:
            return ImageFont.load_default()
        except IOError:
            print("!!!!!! ERRO FATAL: load_default() também falhou. Não há fontes. !!!!!!")
            raise Exception(f"Falha fatal ao carregar qualquer tipo de fonte: {e}")

def generate_trilha_signature(data):
    # --- Variáveis para limpeza de memória ---
    logo_raw = None
    logo_resized = None
    qr_img_raw = None
    qr_img_resized = None
    base_img = None
    qr_bg = None
    draw = None
    
    try:
        print("INFO: A iniciar generate_trilha_signature...")
        
        # --- Fontes ---
        print("INFO: A carregar fontes...")
        font_bold_url = "https://github.com/google/fonts/raw/main/ofl/inter/Inter-Bold.ttf"
        font_regular_url = "https://github.com/google/fonts/raw/main/ofl/inter/Inter-Regular.ttf"
        font_bold_filename = "Inter-Bold.ttf"
        font_regular_filename = "Inter-Regular.ttf"
        font_name = get_font_robust(font_bold_filename, font_bold_url, 18)
        font_title = get_font_robust(font_regular_filename, font_regular_url, 14)
        font_phone = get_font_robust(font_bold_filename, font_bold_url, 14)
        print("INFO: Fontes carregadas.")

        # --- Imagem Base ---
        base_img = Image.new("RGBA", (450, 120), "#C3AEF4")
        
        # --- Processamento do Logo (Otimizado) ---
        print("INFO: A descarregar logo...")
        response_logo = requests.get(data.image_url, stream=True, timeout=10)
        response_logo.raise_for_status()
        
        # Usa 'with' para garantir que a imagem original (logo_raw) é fechada
        with Image.open(response_logo.raw) as logo_raw:
            logo_raw_converted = logo_raw.convert("RGBA")
            logo_width = 140
            logo_height = int((logo_width / float(logo_raw_converted.size[0])) * float(logo_raw_converted.size[1]))
            logo_resized = logo_raw_converted.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
        
        # 'logo_raw' e 'logo_raw_converted' são libertados aqui
        
        base_img.paste(logo_resized, (5, (120 - logo_height) // 2), logo_resized)
        del logo_resized # Liberta a memória do logo redimensionado
        print("INFO: Logo processado.")

        # --- Processamento do QR Code (Otimizado) ---
        print("INFO: A processar QR Code...")
        qr_data = data.qrCodeData.split(",")[1]
        qr_data_bytes = io.BytesIO(base64.b64decode(qr_data))
        
        # Usa 'with' para garantir que a imagem original (qr_img_raw) é fechada
        with Image.open(qr_data_bytes) as qr_img_raw:
            qr_img_raw_converted = qr_img_raw.convert("RGBA")
            qr_img_resized = qr_img_raw_converted.resize((100, 100), Image.Resampling.LANCZOS)
        
        # 'qr_img_raw' e 'qr_img_raw_converted' são libertados aqui
        
        qr_bg = Image.new("RGBA", (110, 110), "white")
        qr_bg.paste(qr_img_resized, (5, 5)) 
        del qr_img_resized # Liberta a memória do QR redimensionado

        base_img.paste(qr_bg, (450 - 110 - 5, (120 - 110) // 2))
        del qr_bg # Liberta a memória do fundo do QR
        print("INFO: QR Code processado.")

        # --- Adiciona Texto ---
        print("INFO: A adicionar texto...")
        draw = ImageDraw.Draw(base_img)
        text_color = "#0E2923" # Cor do texto no HTML
        x_offset = 150 # Posição de início do texto (depois do logo)
        draw.text((x_offset, 30), data.name, fill=text_color, font=font_name)
        draw.text((x_offset, 55), data.title, fill=text_color, font=font_title)
        draw.text((x_offset, 75), data.phone, fill=text_color, font=font_phone)
        del draw # Liberta o objeto Draw
        print("INFO: Texto adicionado.")

        # --- Salva a imagem ---
        output = io.BytesIO()
        base_img.save(output, format="PNG")
        print("INFO: Imagem Trilha gerada com sucesso.")
        return output.getvalue()

    except Exception as e:
        print("!!!!!! ERRO AO GERAR ASSINATURA TRILHA !!!!!!")
        print(traceback.format_exc())
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        raise e
    finally:
        # --- Limpeza Manual de Memória ---
        # Tenta libertar tudo, caso algum objeto ainda exista
        del logo_raw, logo_resized, qr_img_raw, qr_img_resized, base_img, qr_bg, draw
        gc.collect() # Força o "garbage collector"
        print("INFO: Limpeza de memória completa.")

