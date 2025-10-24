import base64
from PIL import Image, ImageDraw, ImageFont
import io
import requests
import traceback # Para logs de erro detalhados
import os # Para caminhos de ficheiros
import gc # Garbage Collector (Coletor de Lixo)

# --- Caminhos de fontes comuns em sistemas Linux (Railway) ---
SYSTEM_FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf",
    "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf"
]

# --- Função de Fonte (Plano D: Tenta fontes do sistema primeiro) ---
def get_font_robust(font_type='bold', size=14):
    """Tenta carregar fontes do sistema. Se falhar, faz o download."""
    
    # 1. Tenta encontrar uma fonte de sistema apropriada
    font_path_to_try = None
    if font_type == 'bold':
        font_path_to_try = SYSTEM_FONT_PATHS[0] # DejaVuSans-Bold
    else:
        font_path_to_try = SYSTEM_FONT_PATHS[1] # DejaVuSans-Regular

    if os.path.exists(font_path_to_try):
        try:
            print(f"INFO: A carregar fonte do sistema: {font_path_to_try}")
            return ImageFont.truetype(font_path_to_try, size)
        except Exception as e:
            print(f"AVISO: Falha ao carregar fonte do sistema {font_path_to_try}. Erro: {e}")
            
    print("AVISO: Nenhuma fonte de sistema encontrada. A tentar download...")

    # 2. Se falhar, tenta o download (Plano B da versão anterior)
    font_url = "https://github.com/google/fonts/raw/main/ofl/inter/Inter-Bold.ttf" if font_type == 'bold' else "https://github.com/google/fonts/raw/main/ofl/inter/Inter-Regular.ttf"
    font_filename = "Inter-Bold.ttf" if font_type == 'bold' else "Inter-Regular.ttf"
    local_font_path = f"/tmp/{font_filename}"
    
    try:
        # 2a. Tenta usar a fonte se já foi descarregada
        if os.path.exists(local_font_path):
            print(f"INFO: A usar fonte descarregada anteriormente: {local_font_path}")
            return ImageFont.truetype(local_font_path, size)
            
        # 2b. Se não existe, tenta descarregar
        print(f"INFO: A descarregar fonte de {font_url}...")
        r = requests.get(font_url, allow_redirects=True, timeout=10)
        r.raise_for_status()
        
        font_data = io.BytesIO(r.content)
        
        # 2c. Salva a fonte no /tmp para uso futuro
        with open(local_font_path, "wb") as f:
            f.write(font_data.getbuffer())
            
        font_data.seek(0) # Rebobina o buffer
        return ImageFont.truetype(font_data, size)
        
    except Exception as e:
        # 3. Se TUDO falhar, lança um erro controlado
        print("!!!!!! ERRO FATAL: Falha ao carregar fontes do sistema E ao descarregar fontes. !!!!!!")
        print(f"Último erro: {e}")
        # Isto irá "derrubar" o FastAPI de forma controlada e aparecerá nos logs.
        raise Exception(f"Falha fatal ao carregar qualquer tipo de fonte. {e}")


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
        font_name = get_font_robust('bold', 18)
        font_title = get_font_robust('regular', 14)
        font_phone = get_font_robust('bold', 14)
        print("INFO: Fontes carregadas.")

        # --- Imagem Base ---
        base_img = Image.new("RGBA", (450, 120), "#C3AEF4")
        
        # --- Processamento do Logo (Otimizado) ---
        print("INFO: A descarregar logo...")
        response_logo = requests.get(data.image_url, stream=True, timeout=10)
        response_logo.raise_for_status()
        
        with Image.open(response_logo.raw) as logo_raw:
            logo_raw_converted = logo_raw.convert("RGBA")
            logo_width = 140
            logo_height = int((logo_width / float(logo_raw_converted.size[0])) * float(logo_raw_converted.size[1]))
            logo_resized = logo_raw_converted.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
        
        base_img.paste(logo_resized, (5, (120 - logo_height) // 2), logo_resized)
        del logo_resized 
        print("INFO: Logo processado.")

        # --- Processamento do QR Code (Otimizado) ---
        print("INFO: A processar QR Code...")
        qr_data = data.qrCodeData.split(",")[1]
        qr_data_bytes = io.BytesIO(base64.b64decode(qr_data))
        
        with Image.open(qr_data_bytes) as qr_img_raw:
            qr_img_raw_converted = qr_img_raw.convert("RGBA")
            qr_img_resized = qr_img_raw_converted.resize((100, 100), Image.Resampling.LANCZOS)
        
        qr_bg = Image.new("RGBA", (110, 110), "white")
        qr_bg.paste(qr_img_resized, (5, 5)) 
        del qr_img_resized 

        base_img.paste(qr_bg, (450 - 110 - 5, (120 - 110) // 2))
        del qr_bg 
        print("INFO: QR Code processado.")

        # --- Adiciona Texto ---
        print("INFO: A adicionar texto...")
        draw = ImageDraw.Draw(base_img)
        text_color = "#0E2923" 
        x_offset = 150 
        draw.text((x_offset, 30), data.name, fill=text_color, font=font_name)
        draw.text((x_offset, 55), data.title, fill=text_color, font=font_title)
        draw.text((x_offset, 75), data.phone, fill=text_color, font=font_phone)
        del draw 
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
        del logo_raw, logo_resized, qr_img_raw, qr_img_resized, base_img, qr_bg, draw
        gc.collect() 
        print("INFO: Limpeza de memória completa.")

