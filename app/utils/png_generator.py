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
# (Esta função é uma cópia da que está no trilha_generator.py)
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
            print(f"INFO (png_gen): A carregar fonte do sistema: {font_path_to_try}")
            return ImageFont.truetype(font_path_to_try, size)
        except Exception as e:
            print(f"AVISO (png_gen): Falha ao carregar fonte do sistema {font_path_to_try}. Erro: {e}")
            
    print("AVISO (png_gen): Nenhuma fonte de sistema encontrada. A tentar download...")

    # 2. Se falhar, tenta o download (Plano B da versão anterior)
    font_url = "https://github.com/google/fonts/raw/main/ofl/inter/Inter-Bold.ttf" if font_type == 'bold' else "https://github.com/google/fonts/raw/main/ofl/inter/Inter-Regular.ttf"
    font_filename = "Inter-Bold.ttf" if font_type == 'bold' else "Inter-Regular.ttf"
    local_font_path = f"/tmp/{font_filename}"
    
    try:
        if os.path.exists(local_font_path):
            print(f"INFO (png_gen): A usar fonte descarregada anteriormente: {local_font_path}")
            return ImageFont.truetype(local_font_path, size)
            
        print(f"INFO (png_gen): A descarregar fonte de {font_url}...")
        r = requests.get(font_url, allow_redirects=True, timeout=10)
        r.raise_for_status()
        font_data = io.BytesIO(r.content)
        
        with open(local_font_path, "wb") as f:
            f.write(font_data.getbuffer())
            
        font_data.seek(0)
        return ImageFont.truetype(font_data, size)
        
    except Exception as e:
        print("!!!!!! ERRO FATAL (png_gen): Falha ao carregar fontes do sistema E ao descarregar fontes. !!!!!!")
        print(f"Último erro: {e}")
        raise Exception(f"Falha fatal ao carregar qualquer tipo de fonte. {e}")


# --- Função Principal para PNG (Netflix, Pinterest, etc.) ---
def generate_signature_png(data):
    # (Nota: Esta é uma implementação simples. O layout do HTML é complexo.)
    # (O objetivo principal é PARAR o "crash" do servidor.)
    
    logo_raw = None
    logo_resized = None
    base_img = None
    draw = None

    try:
        print("INFO (png_gen): A iniciar generate_signature_png...")
        
        # --- Fontes ---
        print("INFO (png_gen): A carregar fontes...")
        font_name = get_font_robust('bold', 16)
        font_title = get_font_robust('regular', 13)
        font_phone = get_font_robust('regular', 13)
        print("INFO (png_gen): Fontes carregadas.")

        # --- Imagem Base ---
        # O layout no HTML (signature-preview) tem 600px de largura.
        # Vamos assumir uma altura de 100px. Fundo branco.
        base_img = Image.new("RGBA", (600, 100), "white")
        
        # --- Processamento do Logo (Otimizado) ---
        print("INFO (png_gen): A descarregar logo...")
        response_logo = requests.get(data.image_url, stream=True, timeout=10)
        response_logo.raise_for_status()
        
        with Image.open(response_logo.raw) as logo_raw:
            logo_raw_converted = logo_raw.convert("RGBA")
            # O logo no HTML tem max-width: 150px
            logo_width = 150
            logo_height = int((logo_width / float(logo_raw_converted.size[0])) * float(logo_raw_converted.size[1]))
            # Redimensiona se for maior que a altura da imagem
            if logo_height > 90:
                logo_height = 90
                logo_width = int((logo_height / float(logo_raw_converted.size[1])) * float(logo_raw_converted.size[0]))
            
            logo_resized = logo_raw_converted.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
        
        # Cola o logo (com 5px de padding)
        base_img.paste(logo_resized, (5, (100 - logo_height) // 2), logo_resized)
        del logo_resized 
        print("INFO (png_gen): Logo processado.")

        # --- Adiciona Texto ---
        print("INFO (png_gen): A adicionar texto...")
        draw = ImageDraw.Draw(base_img)
        text_color = "#333333" # Cor de texto escura
        x_offset = 170 # Posição de início do texto (depois do logo)
        
        # (Nota: O 'data' não envia 'department' ou 'twitter', apenas name, title, phone)
        draw.text((x_offset, 25), data.name, fill=text_color, font=font_name)
        draw.text((x_offset, 50), data.title, fill=text_color, font=font_title)
        draw.text((x_offset, 70), data.phone, fill=text_color, font=font_phone)
        del draw 
        print("INFO (png_gen): Texto adicionado.")

        # --- Salva a imagem ---
        output = io.BytesIO()
        base_img.save(output, format="PNG")
        print("INFO (png_gen): Imagem PNG gerada com sucesso.")
        return output.getvalue()

    except Exception as e:
        print("!!!!!! ERRO AO GERAR ASSINATURA PNG !!!!!!")
        print(traceback.format_exc())
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        raise e
    finally:
        # --- Limpeza Manual de Memória ---
        del logo_raw, logo_resized, base_img, draw
        gc.collect() 
        print("INFO (png_gen): Limpeza de memória completa.")
