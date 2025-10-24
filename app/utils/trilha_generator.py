import base64
from PIL import Image, ImageDraw, ImageFont
import io
import requests
import traceback # Para logs de erro detalhados
import os # Para caminhos de ficheiros

# --- CORREÇÃO: Função para carregar uma fonte de forma segura ---
# Tenta carregar a fonte localmente. Se falhar, faz o download.
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
        # Se TUDO falhar (download, etc.), tenta o load_default()
        # Se isto falhar, o container vai "morrer" (crash)
        try:
            return ImageFont.load_default()
        except IOError:
            print("!!!!!! ERRO FATAL: load_default() também falhou. Não há fontes. !!!!!!")
            # Se até o load_default falhar, não há nada a fazer.
            # Lança o erro para "derrubar" o FastAPI de forma controlada.
            raise Exception(f"Falha fatal ao carregar qualquer tipo de fonte: {e}")

def generate_trilha_signature(data):
    try:
        print("INFO: A iniciar generate_trilha_signature...") # Log de início
        
        # --- URLs e nomes de ficheiros das Fontes ---
        font_bold_url = "https://github.com/google/fonts/raw/main/ofl/inter/Inter-Bold.ttf"
        font_regular_url = "https://github.com/google/fonts/raw/main/ofl/inter/Inter-Regular.ttf"
        font_bold_filename = "Inter-Bold.ttf"
        font_regular_filename = "Inter-Regular.ttf"

        # --- Carregar Fontes de forma segura ---
        print("INFO: A carregar fontes...")
        font_name = get_font_robust(font_bold_filename, font_bold_url, 18)
        font_title = get_font_robust(font_regular_filename, font_regular_url, 14)
        font_phone = get_font_robust(font_bold_filename, font_bold_url, 14)
        print("INFO: Fontes carregadas.")

        # --- Processamento do GIF (lê apenas o primeiro frame) ---
        print("INFO: A descarregar logo...")
        response_logo = requests.get(data.image_url, stream=True, timeout=10)
        response_logo.raise_for_status()
        logo = Image.open(response_logo.raw).convert("RGBA")
        print("INFO: Logo descarregado.")
        
        # O layout no HTML (trilha-signature-preview) tem 450x120
        # O fundo é #C3AEF4
        base_img = Image.new("RGBA", (450, 120), "#C3AEF4")
        
        # O logo no HTML é 140px de largura, vamos redimensionar
        logo_width = 140
        logo_height = int((logo_width / float(logo.size[0])) * float(logo.size[1]))
        logo_resized = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
        
        # Cola o logo (centralizado na célula de 140px)
        base_img.paste(logo_resized, (5, (120 - logo_height) // 2), logo_resized)
        print("INFO: Logo processado.")

        # --- Processamento do QR Code ---
        print("INFO: A processar QR Code...")
        qr_data = data.qrCodeData.split(",")[1]
        qr_img_raw = Image.open(io.BytesIO(base64.b64decode(qr_data))).convert("RGBA")
        
        # O QR no HTML tem 110x110 (incluindo padding)
        qr_img_resized = qr_img_raw.resize((100, 100), Image.Resampling.LANCZOS)
        
        # Cria um fundo branco para o QR code
        qr_bg = Image.new("RGBA", (110, 110), "white")
        qr_bg.paste(qr_img_resized, (5, 5)) # Adiciona 5px de padding

        # Cola o QR code (com fundo) na imagem base
        base_img.paste(qr_bg, (450 - 110 - 5, (120 - 110) // 2)) # 5px da borda direita
        print("INFO: QR Code processado.")

        # --- Adiciona Texto ---
        print("INFO: A adicionar texto...")
        draw = ImageDraw.Draw(base_img)
        text_color = "#0E2923" # Cor do texto no HTML
        x_offset = 150 # Posição de início do texto (depois do logo)
        
        # Nome
        draw.text((x_offset, 30), data.name, fill=text_color, font=font_name)
        # Cargo
        draw.text((x_offset, 55), data.title, fill=text_color, font=font_title)
        # Telefone
        draw.text((x_offset, 75), data.phone, fill=text_color, font=font_phone)
        print("INFO: Texto adicionado.")

        # --- Salva a imagem ---
        output = io.BytesIO()
        base_img.save(output, format="PNG")
        print("INFO: Imagem Trilha gerada com sucesso.")
        return output.getvalue()

    except Exception as e:
        # --- LOG DE ERRO ---
        # Se algo falhar, isto irá imprimir o erro completo nos logs do Railway
        print("!!!!!! ERRO AO GERAR ASSINATURA TRILHA !!!!!!")
        print(traceback.format_exc())
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        # Levanta o erro para o FastAPI o reportar
        raise e

